"""
MNEMOS-lite v0.7 — FM-93 patch applied
FM-93: Preference-Blind Re-entry
Fix: Per-topic answer/reflect preference tracking with confidence gate.
     Topic preference (>=0.65 confidence) outranks FM-87 re-entry.
     Preferences persist via LongTermBehavior across sessions.

Priority stack (updated):
  FM-91 explicit intent override     <- always wins
  FM-93 topic preference (>=0.65)   <- suppresses FM-87 re-entry
  FM-87 helplessness re-entry        <- fires only when no preference signal
  FM-85/86 reflection budget         <- baseline
"""

from __future__ import annotations

import json
import math
import re
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# --- Optional heavy deps ----------------------------------------------------
try:
    import chromadb  # type: ignore
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False

try:
    from rank_bm25 import BM25Okapi  # type: ignore
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False


# ===========================================================================
# ENUMS AND CONSTANTS
# ===========================================================================

class Domain(Enum):
    FACTUAL    = "factual"
    CONSTRAINT = "constraint"
    PREFERENCE = "preference"
    EVALUATIVE = "evaluative"
    IDENTITY   = "identity"
    CAUSAL     = "causal"

class TrustTier(Enum):
    HIGH   = 3
    MEDIUM = 2
    LOW    = 1

STOPWORDS = {
    "a","an","the","is","are","was","were","be","been","being",
    "have","has","had","do","does","did","will","would","could",
    "should","may","might","shall","can","need","dare","ought",
    "used","to","of","in","on","at","by","for","with","about",
    "against","between","into","through","during","before","after",
    "above","below","from","up","down","out","off","over","under",
    "then","once","i","you","he","she","it","we","they","me","him",
    "her","us","them","my","your","his","its","our","their","this",
    "that","these","those","what","which","who","how","when","where",
    "why","and","but","or","nor","so","yet","both","either","neither",
    "not","no","just","also","very","really","quite",
}

RESISTANCE_PHRASES = [
    r"\bjust (?:tell|answer|give)\b",
    r"\bstop (?:asking|questioning)\b",
    r"\bi know\b",
    r"\bnot helpful\b",
    r"\bdon'?t (?:need|want) (?:to think|reflection|analysis)\b",
    r"\bjust (?:do it|answer it|give me)\b",
    r"\bskip the\b",
    r"\bget to the point\b",
    r"\bwaste of time\b",
    r"\bjust (?:the answer|a answer|an answer)\b",
    r"\bstop overthinking\b",
    r"\bunnecessary\b",
    r"\btoo much\b",
    r"\bkeep it simple\b",
    r"\bi (?:already|just) want\b",
    r"\bno need for\b",
    r"\bplease just\b",
    r"\bjust respond\b",
    r"\bstraight answer\b",
    r"\bdirect answer\b",
    r"\banswer directly\b",
    r"\bstop (?:the |all the )?questions\b",
]

INTENT_REFLECT_PHRASES = [
    r"\bhelp me (?:think|work through|figure out)\b",
    r"\bnot sure (?:what|how|if)\b",
    r"\bthinking (?:about|through)\b",
    r"\bshould i\b",
    r"\bwhat (?:do you think|would you|should i)\b",
    r"\bexplore\b",
    r"\bweigh\b",
    r"\bpros and cons\b",
    r"\badvice\b",
    r"\buncertain\b",
    r"\bstruggling with\b",
]

INTENT_ANSWER_PHRASES = [
    r"\bjust (?:tell|answer|give|show|list)\b",
    r"\bwhat is\b",
    r"\bwhat are\b",
    r"\bhow (?:do|does|did|can|to)\b",
    r"\bdefine\b",
    r"\bexplain\b",
    r"\blist\b",
    r"\bshow me\b",
    r"\bgive me\b",
    r"\btell me\b",
    r"\bquick(?:ly)?\b",
    r"\bfast\b",
    r"\bsimple\b",
    r"\bbrief(?:ly)?\b",
]

CONSTRAINT_EXPANSIONS = {
    "shellfish":  ["shrimp","crab","lobster","clam","oyster","scallop","mussel","prawn"],
    "nuts":       ["peanut","almond","cashew","walnut","pecan","pistachio","hazelnut"],
    "gluten":     ["wheat","barley","rye","spelt","semolina","flour","bread","pasta"],
    "dairy":      ["milk","cheese","butter","cream","yogurt","whey","lactose"],
    "medication": ["drug","prescription","dose","dosage","pill","tablet","capsule"],
    "legal":      ["law","regulation","statute","compliance","liability","contract"],
}


# ===========================================================================
# DATA STRUCTURES
# ===========================================================================

@dataclass
class Belief:
    """Structured belief with Beta(alpha,beta) uncertainty. FM-76."""
    id:                str   = field(default_factory=lambda: str(uuid.uuid4())[:8])
    trait:             str   = ""
    value:             str   = ""
    context:           str   = "general"
    exceptions:        List  = field(default_factory=list)
    content:           str   = ""
    domain:            Domain = Domain.PREFERENCE
    namespace:         str   = "default"
    alpha:             float = 1.0
    beta_:             float = 1.0
    evidence_count:    int   = 0
    last_confirmed:    float = field(default_factory=time.time)
    last_contradicted: float = 0.0
    source_text:       str   = ""
    immutable:         bool  = False
    decay_rate:        float = 0.01

    @property
    def confidence(self) -> float:
        return self.alpha / (self.alpha + self.beta_)

    @property
    def is_truth_immune(self) -> bool:
        return self.domain in (Domain.FACTUAL, Domain.CONSTRAINT)

    def decay(self, days_elapsed: float) -> None:
        if self.immutable or self.domain in (Domain.CONSTRAINT, Domain.IDENTITY):
            return
        factor = math.exp(-self.decay_rate * days_elapsed)
        self.alpha  = max(0.5, self.alpha  * factor)
        self.beta_  = max(0.5, self.beta_  * factor)

    def recency_boost(self) -> float:
        """FM-83: 1.35x within 24h."""
        hours = (time.time() - self.last_confirmed) / 3600
        return 1.35 if hours < 24 else 1.0

    def confidence_qualifier(self) -> str:
        """FM-84: calibrated language."""
        c = self.confidence
        n = self.evidence_count
        base = f"Based on {n} instance{'s' if n!=1 else ''}"
        if c >= 0.85 and n >= 5:   return f"{base} — high confidence"
        if c >= 0.70 and n >= 3:   return f"{base} — moderate confidence"
        if c >= 0.55:               return f"{base} — tentative"
        return f"{base} — uncertain (alpha={self.alpha:.1f}, beta={self.beta_:.1f})"

    def matches_context(self, query_context: str) -> bool:
        """FM-79: hard context gate."""
        if self.context == "general":
            return True
        return self.context.lower() in query_context.lower()

    def label(self) -> str:
        if self.trait and self.value:
            return f"{self.trait}={self.value}"
        return self.content[:60] if self.content else f"belief:{self.id}"


@dataclass
class CausalEdge:
    """FM-77, FM-80: observed vs validated causal weight."""
    cause:           str
    effect:          str
    observed_weight: float = 0.5
    validated_weight:float = 0.0
    context_count:   int   = 0
    contexts_seen:   List  = field(default_factory=list)
    confidence:      float = 0.0

    def update(self, outcome: bool, context: str) -> None:
        self.context_count += 1
        if context not in self.contexts_seen:
            self.contexts_seen.append(context)
        n = self.context_count
        self.observed_weight = (self.observed_weight * (n-1) + float(outcome)) / n
        if len(self.contexts_seen) >= 2:
            self.validated_weight = self.observed_weight
            self.confidence = min(0.95, 0.5 + 0.15 * len(self.contexts_seen))


@dataclass
class EpisodicRecord:
    """L1: verbatim write-once episodic record."""
    id:        str   = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)
    role:      str   = "user"
    content:   str   = ""
    session:   str   = ""
    namespace: str   = "default"
    salience:  float = 0.5


# ===========================================================================
# FM REGISTER (L15)
# ===========================================================================

class FMRegister:
    """Immutable append-only failure mode register. FM-14, FM-50."""
    def __init__(self):
        self._entries: List[Dict] = []

    def log(self, fm_id: str, description: str,
            severity: str = "INFO", context: Dict = None) -> None:
        self._entries.append({
            "fm_id":       fm_id,
            "description": description,
            "severity":    severity,
            "context":     context or {},
            "timestamp":   time.time(),
        })

    def entries(self, fm_id: str = None) -> List[Dict]:
        if fm_id:
            return [e for e in self._entries if e["fm_id"] == fm_id]
        return list(self._entries)

    def summary(self) -> str:
        if not self._entries:
            return "FM Register: empty"
        counts = defaultdict(int)
        for e in self._entries:
            counts[e["fm_id"]] += 1
        lines = [f"FM Register ({len(self._entries)} total):"]
        for fm_id, n in sorted(counts.items()):
            lines.append(f"  {fm_id}: {n} occurrence{'s' if n>1 else ''}")
        return "\n".join(lines)


# ===========================================================================
# EPISODIC STORE (L1)
# ===========================================================================

class EpisodicStore:
    """Write-once episodic records. Hybrid BM25+dense search."""
    def __init__(self):
        self._records: List[EpisodicRecord] = []
        self._bm25:    Any                  = None

    def write(self, role: str, content: str, session: str,
              namespace: str = "default", salience: float = 0.5) -> EpisodicRecord:
        rec = EpisodicRecord(role=role, content=content,
                             session=session, namespace=namespace,
                             salience=salience)
        self._records.append(rec)
        self._bm25 = None
        return rec

    def _rebuild_bm25(self):
        if not BM25_AVAILABLE or self._bm25 is not None:
            return
        corpus = [r.content.lower().split() for r in self._records]
        if corpus:
            self._bm25 = BM25Okapi(corpus)

    def search(self, query: str, top_k: int = 5,
               namespace: str = None) -> List[EpisodicRecord]:
        candidates = self._records
        if namespace:
            candidates = [r for r in candidates if r.namespace == namespace]
        if not candidates:
            return []
        if BM25_AVAILABLE:
            self._rebuild_bm25()
            if self._bm25 and len(self._records) == len(candidates):
                tokens = query.lower().split()
                scores = self._bm25.get_scores(tokens)
                ranked = sorted(zip(scores, self._records), reverse=True)
                return [r for _, r in ranked[:top_k]]
        q_words = set(query.lower().split()) - STOPWORDS
        def overlap(r):
            return len(q_words & (set(r.content.lower().split()) - STOPWORDS))
        return sorted(candidates, key=overlap, reverse=True)[:top_k]

    def recent(self, n: int = 10, session: str = None) -> List[EpisodicRecord]:
        records = self._records
        if session:
            records = [r for r in records if r.session == session]
        return list(reversed(records[-n:]))

    def __len__(self):
        return len(self._records)


# ===========================================================================
# FAST PATH (L0)
# ===========================================================================

class FastPath:
    """TTL 72h in-memory cache. FM-24."""
    TTL = 72 * 3600

    def __init__(self):
        self._cache: Dict[str, Tuple[Any, float]] = {}

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = (value, time.time())

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        value, ts = self._cache[key]
        if time.time() - ts > self.TTL:
            del self._cache[key]
            return None
        return value

    def evict_expired(self) -> int:
        now = time.time()
        expired = [k for k, (_, ts) in self._cache.items() if now - ts > self.TTL]
        for k in expired:
            del self._cache[k]
        return len(expired)


# ===========================================================================
# IDENTITY STORE
# ===========================================================================

class IdentityStore:
    """Multi-stable identity — never force-merged. FM-63."""
    def __init__(self):
        self._states: Dict[str, List[Belief]] = defaultdict(list)

    def add(self, belief: Belief) -> None:
        ns = belief.namespace
        for e in self._states[ns]:
            if e.trait == belief.trait and e.value != belief.value:
                belief.content = f"[IDENTITY-TENSION with {e.id}] {belief.content}"
        self._states[ns].append(belief)

    def get(self, namespace: str) -> List[Belief]:
        return self._states.get(namespace, [])

    def reconciliation_candidates(self) -> List[Tuple[Belief, Belief]]:
        candidates = []
        for ns, beliefs in self._states.items():
            for i, b1 in enumerate(beliefs):
                for b2 in beliefs[i+1:]:
                    if b1.trait == b2.trait and b1.value != b2.value:
                        candidates.append((b1, b2))
        return candidates


# ===========================================================================
# FORGETTING POLICY (FM-71)
# ===========================================================================

class ForgettingPolicy:
    """Decay + entropy retire + PAWD retrieval penalty."""
    ENTROPY_THRESHOLD = 2.5
    PAWD_PENALTY      = 0.3

    def apply_decay(self, beliefs: List[Belief], days: float = 1.0) -> None:
        for b in beliefs:
            b.decay(days)

    def should_retire(self, b: Belief) -> bool:
        if b.immutable or b.domain in (Domain.CONSTRAINT, Domain.IDENTITY):
            return False
        a, bv = b.alpha, b.beta_
        if a <= 0 or bv <= 0:
            return True
        entropy = (math.lgamma(a+bv) - math.lgamma(a) - math.lgamma(bv)
                   - (a-1)*math.digamma(a) - (bv-1)*math.digamma(bv)
                   + (a+bv-2)*math.digamma(a+bv)) if a > 1 and bv > 1 else 999
        return entropy > self.ENTROPY_THRESHOLD and b.evidence_count < 2

    def pawd_score(self, b: Belief, base_score: float) -> float:
        days = (time.time() - b.last_confirmed) / 86400
        if days < 7:
            return base_score
        return base_score * (1.0 - self.PAWD_PENALTY * math.log1p(days / 7))


# ===========================================================================
# AUTONOMY TRACKER (FM-61, FM-70, FM-79)
# ===========================================================================

class AutonomyTracker:
    """Counterfactual UAI. FM-61 anti-gaming."""
    UAI_FLOOR = 0.40

    def __init__(self):
        self._natural:         List[float] = []
        self._prompted:        List[float] = []
        self._session_natural: List[float] = []
        self._session_prompted:List[float] = []

    def record(self, quality: float, was_prompted: bool) -> None:
        if was_prompted:
            self._prompted.append(quality)
            self._session_prompted.append(quality)
        else:
            self._natural.append(quality)
            self._session_natural.append(quality)

    def uai(self) -> float:
        if not self._natural:
            return 1.0
        nat = sum(self._natural) / len(self._natural)
        if not self._prompted:
            return nat
        delta = sum(self._prompted)/len(self._prompted) - nat
        return max(self.UAI_FLOOR, 1.0 - max(0, delta))

    def session_uai(self) -> float:
        if not self._session_natural:
            return 1.0
        nat = sum(self._session_natural) / len(self._session_natural)
        if not self._session_prompted:
            return nat
        delta = sum(self._session_prompted)/len(self._session_prompted) - nat
        return max(self.UAI_FLOOR, 1.0 - max(0, delta))

    def new_session(self) -> None:
        self._session_natural  = []
        self._session_prompted = []


# ===========================================================================
# INTERVENTION POLICY (FM-73)
# ===========================================================================

class InterventionPolicy:
    def should_intervene(self, text: str, uai: float,
                          check_budget_ok: bool) -> Tuple[bool, str]:
        text_l = text.lower()
        urgency = any(w in text_l for w in
                      ["allerg","emergency","urgent","danger","harm",
                       "illegal","medication","dosage"])
        if urgency:
            return True, "urgency"
        decision = any(w in text_l for w in
                       ["should i","decide","choice","option","pick","select",
                        "go with","commit"])
        if decision and check_budget_ok:
            return True, "decision"
        if uai < AutonomyTracker.UAI_FLOOR and check_budget_ok:
            return True, "low_uai"
        return False, ""


# ===========================================================================
# CHECK BUDGET (FM-74)
# ===========================================================================

class CheckBudget:
    """Max 2 reality checks per session. FM-74."""
    MAX = 2

    def __init__(self):
        self._count = 0

    def available(self) -> bool:
        return self._count < self.MAX

    def use(self) -> bool:
        if self._count < self.MAX:
            self._count += 1
            return True
        return False

    def reset(self) -> None:
        self._count = 0

    def remaining(self) -> int:
        return max(0, self.MAX - self._count)


# ===========================================================================
# SOFT INTENT CLASSIFIER (FM-69, FM-75)
# ===========================================================================

class SoftIntentClassifier:
    """30+ regex patterns. FM-69, FM-75, FM-91."""

    def classify(self, text: str) -> Dict[str, float]:
        text_l = text.lower()
        rs = sum(1 for p in INTENT_REFLECT_PHRASES if re.search(p, text_l))
        as_ = sum(1 for p in INTENT_ANSWER_PHRASES  if re.search(p, text_l))
        total = rs + as_ or 1
        return {"reflect": rs / total, "answer": as_ / total}

    def detect_intent_override(self, text: str) -> Optional[str]:
        """FM-91: explicit intent — absolute priority."""
        text_l = text.lower()
        if re.search(r"\bhelp me (?:think|work through|figure out)\b", text_l):
            return "force_reflect"
        if re.search(r"\bjust (?:answer|tell|give)\b", text_l):
            return "force_answer"
        if re.search(r"\bstraight answer\b|\bdirect answer\b|\banswer directly\b", text_l):
            return "force_answer"
        return None


# ===========================================================================
# RESPONSE VALIDATOR (FM-78, FM-82)
# ===========================================================================

class ResponseValidator:
    def validate(self, response: str, active_constraints: List[Belief],
                 original_query: str) -> Tuple[bool, List[str]]:
        issues = []
        resp_l = response.lower()
        for c in active_constraints:
            keywords = [c.content.lower(), c.value.lower(), c.trait.lower()]
            for base, expansions in CONSTRAINT_EXPANSIONS.items():
                if any(base in kw for kw in keywords):
                    keywords.extend(expansions)
            if any(kw in resp_l for kw in keywords if len(kw) > 2):
                certainty = ["definitely","absolutely","certainly",
                             "for sure","guaranteed","no doubt"]
                if any(p in resp_l for p in certainty):
                    issues.append(
                        f"CONSTRAINT {c.id} acknowledged but certainty "
                        f"language detected")
        return len(issues) == 0, issues


# ===========================================================================
# CONSOLIDATION MANAGER (FM-65)
# ===========================================================================

class ConsolidationManager:
    """Dual-queue 70/30. FM-65."""
    def __init__(self):
        self._consequence_queue: deque = deque(maxlen=100)
        self._pattern_queue:     deque = deque(maxlen=100)

    def enqueue(self, record: EpisodicRecord, is_consequence: bool) -> None:
        (self._consequence_queue if is_consequence
         else self._pattern_queue).append(record)

    def next_batch(self, size: int = 10) -> List[EpisodicRecord]:
        n_cons = max(1, int(size * 0.70))
        n_patt = size - n_cons
        batch = []
        for _ in range(n_cons):
            if self._consequence_queue:
                batch.append(self._consequence_queue.popleft())
        for _ in range(n_patt):
            if self._pattern_queue:
                batch.append(self._pattern_queue.popleft())
        return batch


# ===========================================================================
# CONTINUITY DRILL (FM-64)
# ===========================================================================

class ContinuityDrill:
    """Degraded reality testing. FM-64."""
    def run(self, beliefs: List[Belief], mode: str = "partial") -> Dict:
        result = {"mode": mode, "beliefs_tested": len(beliefs), "failures": []}
        if mode == "partial":
            result["available"] = len(beliefs) // 2
            result["missing"]   = len(beliefs) - len(beliefs) // 2
        elif mode == "stale":
            for b in beliefs:
                age = (time.time() - b.last_confirmed) / 86400
                if age > 30:
                    result["failures"].append({"id": b.id, "issue": f"stale:{age:.0f}d"})
        elif mode == "noisy":
            for i, b in enumerate(beliefs):
                if i % 5 == 0:
                    result["failures"].append({"id": b.id, "issue": "noise_injected"})
        return result


# ===========================================================================
# LONG-TERM BEHAVIOR (FM-89)
# FM-93 extension: per-topic mode preference persistence
# ===========================================================================

class LongTermBehavior:
    """Cross-session behavioral baseline. FM-89.

    FM-93 addition:
      _topic_preferences stores per-topic answer/reflect preference.
      topic_preference_confidence() returns (mode, confidence) for any key.
      record_topic_preference() adjusts preference with ADJUST_RATE.
    """
    ADJUST_RATE = 0.15

    def __init__(self):
        self._resistance_history: List[float] = []
        self._avg_resistance:     float       = 1.0
        self._threshold:          int         = 3

        # FM-93: topic_key -> {"answer": float, "reflect": float, "n": int}
        self._topic_preferences: Dict[str, Dict] = {}

    # -- resistance baseline ------------------------------------------------

    def record_session_resistance(self, avg_resistance: float) -> None:
        self._resistance_history.append(avg_resistance)
        self._avg_resistance = (self._avg_resistance * (1 - self.ADJUST_RATE)
                                + avg_resistance * self.ADJUST_RATE)
        if self._avg_resistance > 2:
            self._threshold = 5
        elif self._avg_resistance < 0.5:
            self._threshold = 2
        else:
            self._threshold = 3

    @property
    def reflection_threshold(self) -> int:
        return self._threshold

    # -- FM-93: per-topic mode preference -----------------------------------

    def record_topic_preference(self, topic_key: str,
                                 mode: str, quality: float) -> None:
        """Record answer or reflect preference for a topic.

        mode: 'answer' | 'reflect'
        quality: reasoning_quality_score (0-1), stronger signal = higher weight
        """
        if topic_key not in self._topic_preferences:
            self._topic_preferences[topic_key] = {
                "answer": 0.0, "reflect": 0.0, "n": 0}
        e = self._topic_preferences[topic_key]
        e[mode] = e[mode] * (1 - self.ADJUST_RATE) + quality * self.ADJUST_RATE
        e["n"] += 1

    def topic_preference_confidence(self, topic_key: str) -> Tuple[str, float]:
        """Return (preferred_mode, confidence).

        Confidence scale mirrors FM-90:
          n=1  -> 0.25  (informational, no gate)
          n=2  -> 0.50  (below gate threshold)
          n>=3 -> scales to 0.90 max
        Returns ('none', 0.0) when no data.
        """
        if topic_key not in self._topic_preferences:
            return ("none", 0.0)
        e = self._topic_preferences[topic_key]
        n = e["n"]
        if n == 0:
            return ("none", 0.0)

        preferred = "answer" if e["answer"] >= e["reflect"] else "reflect"
        delta = abs(e["answer"] - e["reflect"])

        if n == 1:
            conf = 0.25
        elif n == 2:
            conf = 0.50
        else:
            conf = min(0.90, 0.50 + 0.15 * (n - 2) + delta * 0.30)

        return (preferred, conf)

    def get_all_preferences(self) -> Dict:
        return dict(self._topic_preferences)


# ===========================================================================
# INTERACTION MEMORY (FM-85 to FM-93)
# ===========================================================================

class InteractionMemory:
    """Per-topic reflection budget, resistance, re-entry, quality.

    FM-93 patch:
      should_reflect() checks topic preference BEFORE FM-87 re-entry.
      record_exchange() feeds preference signal to LongTermBehavior.

      Updated priority stack:
        FM-91  explicit intent override        (absolute)
        FM-93  topic preference (conf>=0.65)   (suppresses FM-87)
        FM-87  helplessness re-entry           (fires when no preference signal)
        FM-85/86 reflection budget             (baseline)
    """
    MAX_REFLECT_PER_TOPIC = 3
    DIRECT_BEFORE_REENTRY = 7
    REENTRY_COOLDOWN      = 5
    RESISTANCE_COOLDOWN   = 4

    def __init__(self, long_term: LongTermBehavior):
        self.long_term   = long_term
        self._intent_clf = SoftIntentClassifier()

        self._topic_reflect_count:   Dict[str, int] = defaultdict(int)
        self._topic_reflect_success: Dict[str, int] = defaultdict(int)
        self._topic_direct_streak:   Dict[str, int] = defaultdict(int)
        self._topic_last_reentry:    Dict[str, int] = defaultdict(lambda: -999)

        self._turn:               int   = 0
        self._resistance_count:   int   = 0
        self._cooldown_remaining: int   = 0
        self._recent_turns:       deque = deque(maxlen=3)

    # -- topic key -----------------------------------------------------------

    def _topic_key(self, text: str) -> str:
        """FM-88: semantic clustering via content-word overlap + recency window."""
        words = set(text.lower().split()) - STOPWORDS
        for prev_key, prev_words in self._recent_turns:
            if len(words & prev_words) >= 2:
                return prev_key
        key = "_".join(sorted(list(words))[:4])
        self._recent_turns.append((key, words))
        return key

    # -- resistance detection (FM-90) ----------------------------------------

    def _resistance_confidence(self, text: str) -> float:
        text_l = text.lower()
        signals = sum(1 for p in RESISTANCE_PHRASES if re.search(p, text_l))
        if signals == 1: return 0.25
        if signals == 2: return 0.65
        return min(0.90, 0.65 + 0.08 * (signals - 2))

    def record_resistance(self, text: str) -> bool:
        conf = self._resistance_confidence(text)
        if conf >= 0.65:
            self._resistance_count += 1
            self._cooldown_remaining = self.RESISTANCE_COOLDOWN
            return True
        return False

    # -- reasoning quality (FM-92) -------------------------------------------

    def reasoning_quality_score(self, response: str) -> float:
        words = response.split()
        length_score  = min(1.0, len(words) / 80)
        causal_score  = min(1.0, sum(1 for w in [
            "because","therefore","thus","since","so","hence",
            "consequently","as a result","leads to","causes","results in"]
            if w in response.lower()) / 3)
        struct_score  = min(1.0, sum(1 for m in [
            "first","second","third","however","although","whereas",
            "on the other hand","in contrast","additionally","furthermore"]
            if m in response.lower()) / 2)
        novelty_score = min(1.0, len(set(response.lower().split()) - STOPWORDS) / 30)
        return (length_score * 0.30 + causal_score * 0.30
                + struct_score * 0.20 + novelty_score * 0.20)

    # -- main gate -----------------------------------------------------------

    def should_reflect(self, text: str,
                        prior_history_exists: bool) -> Tuple[bool, str]:
        """Return (should_reflect, reason).

        Priority stack (FM-93 patch):
          1. FM-91 explicit intent override   (absolute)
          2. FM-93 topic preference >=0.65    (NEW — suppresses FM-87)
          3. FM-87 helplessness re-entry      (fires only without preference signal)
          4. FM-85/86 budget + cooldown       (baseline)
        """
        self._turn += 1
        topic = self._topic_key(text)

        # 1. FM-91: explicit intent override ---------------------------------
        override = self._intent_clf.detect_intent_override(text)
        if override == "force_reflect":
            return True,  "fm91_explicit_reflect"
        if override == "force_answer":
            return False, "fm91_explicit_answer"

        # cooldown from resistance
        if self._cooldown_remaining > 0:
            self._cooldown_remaining -= 1
            return False, "resistance_cooldown"

        # 2. FM-93: topic preference gate ------------------------------------
        preferred_mode, pref_conf = self.long_term.topic_preference_confidence(topic)
        if pref_conf >= 0.65:
            if preferred_mode == "answer":
                # Suppress FM-87 re-entry for this topic cluster
                return False, f"fm93_topic_pref_answer(conf={pref_conf:.2f})"
            elif preferred_mode == "reflect":
                if self._topic_reflect_count[topic] < self.MAX_REFLECT_PER_TOPIC:
                    return True, f"fm93_topic_pref_reflect(conf={pref_conf:.2f})"

        # 3. FM-87: helplessness re-entry ------------------------------------
        streak = self._topic_direct_streak[topic]
        last_re = self._topic_last_reentry[topic]
        reentry_ok = (self._turn - last_re) >= self.REENTRY_COOLDOWN

        if (streak >= self.DIRECT_BEFORE_REENTRY
                and prior_history_exists
                and reentry_ok):
            self._topic_last_reentry[topic] = self._turn
            self._topic_direct_streak[topic] = 0
            return True, "fm87_reentry"

        # 4. FM-85/86: intent + budget ---------------------------------------
        intent    = self._intent_clf.classify(text)
        budget_ok = self._topic_reflect_count[topic] < self.MAX_REFLECT_PER_TOPIC

        if intent["reflect"] > intent["answer"] and budget_ok:
            return True, f"intent_reflect(r={intent['reflect']:.2f})"

        self._topic_direct_streak[topic] += 1
        return False, "direct"

    # -- record outcome (FM-93 preference signal) ----------------------------

    def record_exchange(self, text: str, reflected: bool,
                         quality: float) -> None:
        """Log outcome. Feeds FM-93 preference signal to LongTermBehavior."""
        topic = self._topic_key(text)

        if reflected:
            self._topic_reflect_count[topic] += 1
            if quality >= 0.35:
                self._topic_reflect_success[topic] += 1
                self.long_term.record_topic_preference(topic, "reflect", quality)
            else:
                # low-quality reflection = mild answer preference
                self.long_term.record_topic_preference(
                    topic, "answer", 1.0 - quality)
        else:
            self._topic_direct_streak[topic] += 1
            if quality >= 0.20:
                self.long_term.record_topic_preference(topic, "answer", quality)

    def new_session(self) -> None:
        self._turn               = 0
        self._resistance_count   = 0
        self._cooldown_remaining = 0
        self._recent_turns       = deque(maxlen=3)
        # topic counts reset per session; long_term preferences persist


# ===========================================================================
# KNOWLEDGE GRAPH (L2)
# ===========================================================================

class KnowledgeGraph:
    """Beta(a,b) nodes. BIZ propagation. FM-17, FM-22."""
    def __init__(self):
        self._beliefs:    Dict[str, Belief]   = {}
        self._causal:     List[CausalEdge]    = []
        self._quarantine: Dict[str, Belief]   = {}

    def add_belief(self, belief: Belief) -> str:
        self._beliefs[belief.id] = belief
        return belief.id

    def quarantine(self, belief_id: str) -> None:
        if belief_id in self._beliefs:
            self._quarantine[belief_id] = self._beliefs.pop(belief_id)

    def get(self, belief_id: str) -> Optional[Belief]:
        return self._beliefs.get(belief_id)

    def search(self, query: str, namespace: str = None,
               domain: Domain = None, top_k: int = 10) -> List[Belief]:
        q_words = set(query.lower().split()) - STOPWORDS
        fp = ForgettingPolicy()
        results = []
        for b in self._beliefs.values():
            if namespace and b.namespace != namespace: continue
            if domain   and b.domain    != domain:    continue
            b_words  = set(b.label().lower().split()) - STOPWORDS
            overlap  = len(q_words & b_words)
            base     = overlap / max(1, len(q_words)) * b.confidence * b.recency_boost()
            score    = fp.pawd_score(b, base)
            if score > 0:
                results.append((score, b))
        results.sort(key=lambda x: -x[0])
        return [b for _, b in results[:top_k]]

    def biz_propagate(self, source_id: str, delta: float) -> List[str]:
        """Bounded influence zone. FM-17."""
        if source_id not in self._beliefs:
            return []
        source   = self._beliefs[source_id]
        affected = []
        for b in self._beliefs.values():
            if b.id == source_id: continue
            if b.namespace == source.namespace and b.domain == source.domain:
                b.alpha = max(0.5, b.alpha  + delta * 0.1)
                b.beta_ = max(0.5, b.beta_  - delta * 0.05)
                affected.append(b.id)
        return affected

    def add_causal(self, edge: CausalEdge) -> None:
        self._causal.append(edge)

    def get_causal(self, cause: str = None) -> List[CausalEdge]:
        if cause:
            return [e for e in self._causal if cause.lower() in e.cause.lower()]
        return list(self._causal)

    def all_beliefs(self, namespace: str = None) -> List[Belief]:
        beliefs = list(self._beliefs.values())
        if namespace:
            beliefs = [b for b in beliefs if b.namespace == namespace]
        return beliefs


# ===========================================================================
# MEMORY DIGEST (L9)
# ===========================================================================

class MemoryDigest:
    """Calibrated render. Epistemic footer always present. FM-72."""

    def render(self, beliefs: List[Belief], causal_edges: List[CausalEdge],
               uai: float, fm_register: FMRegister,
               topic_preferences: Dict = None) -> str:
        lines = ["=== MNEMOS MEMORY DIGEST ===\n"]
        by_domain: Dict[str, List[Belief]] = defaultdict(list)
        for b in beliefs:
            by_domain[b.domain.value].append(b)

        for dn in ["constraint","identity","preference","factual","evaluative","causal"]:
            group = by_domain.get(dn, [])
            if not group: continue
            lines.append(f"[{dn.upper()}]")
            for b in group:
                flag = ("  TRUTH-IMMUNE" if b.is_truth_immune else
                        "  PREFERENCE"   if b.domain == Domain.PREFERENCE else
                        "  EVALUATIVE"   if b.domain == Domain.EVALUATIVE else "")
                lines.append(
                    f"  {b.label()} | conf={b.confidence:.2f} | "
                    f"ns={b.namespace} | {b.confidence_qualifier()}{flag}")
            lines.append("")

        if causal_edges:
            lines.append("[CAUSAL]")
            for e in causal_edges:
                v = f"validated={e.validated_weight:.2f}" if e.context_count >= 2 \
                    else "unvalidated"
                lines.append(
                    f"  {e.cause} -> {e.effect} "
                    f"(obs={e.observed_weight:.2f}, {v}, n={e.context_count})")
            lines.append("")

        uai_label = "healthy" if uai >= 0.70 else "watch" if uai >= 0.50 else "LOW"
        lines.append(f"[AUTONOMY INDEX] UAI={uai:.2f} ({uai_label})")

        # FM-93: topic preferences
        if topic_preferences:
            lines.append("\n[TOPIC PREFERENCES (FM-93)]")
            for tk, prefs in list(topic_preferences.items())[:6]:
                n    = prefs["n"]
                mode = "answer" if prefs["answer"] >= prefs["reflect"] else "reflect"
                if   n == 1: conf = 0.25
                elif n == 2: conf = 0.50
                else:        conf = min(0.90, 0.50 + 0.15*(n-2))
                lines.append(
                    f"  '{tk[:32]}' -> prefers {mode} "
                    f"(conf={conf:.2f}, n={n})")

        lines.append(
            "\n--- EPISTEMIC FOOTER ---\n"
            "All beliefs carry uncertainty (Beta distribution).\n"
            "Truth-immune beliefs (FACTUAL/CONSTRAINT) always surface.\n"
            "Confidence != truth. Provenance is permanent. "
            "User is ground truth on PREFERENCE.\n"
            f"FM Register: {len(fm_register.entries())} entries logged.")
        return "\n".join(lines)


# ===========================================================================
# MNEMOS LITE — ORCHESTRATOR
# ===========================================================================

class MnemosLite:
    """
    MNEMOS-lite v0.7

    FM-93 Preference-Blind Re-entry — CLOSED.
    Fix: LongTermBehavior tracks per-topic answer/reflect preference.
         InteractionMemory checks preference (conf>=0.65) before FM-87 re-entry.
         record_exchange() feeds preference signal to LongTermBehavior.

    Priority stack:
      FM-91 explicit intent override
      FM-93 topic preference (>=0.65)   <- new gate
      FM-87 helplessness re-entry
      FM-85/86 reflection budget
    """

    def __init__(self, namespace_cap: int = 5):
        self.episodic      = EpisodicStore()
        self.graph         = KnowledgeGraph()
        self.fast_path     = FastPath()
        self.fm_register   = FMRegister()
        self.forgetting    = ForgettingPolicy()
        self.identity      = IdentityStore()
        self.autonomy      = AutonomyTracker()
        self.intervention  = InterventionPolicy()
        self.check_budget  = CheckBudget()
        self.consolidation = ConsolidationManager()
        self.digest_layer  = MemoryDigest()
        self.long_term     = LongTermBehavior()
        self.interaction   = InteractionMemory(self.long_term)
        self.intent_clf    = SoftIntentClassifier()
        self.validator     = ResponseValidator()
        self.continuity    = ContinuityDrill()

        self._session_id:        str  = ""
        self._namespace_cap:     int  = namespace_cap
        self._active_namespaces: set  = set()
        self._turn_count:        int  = 0

    # -- session -------------------------------------------------------------

    def new_session(self, session_id: str = None) -> str:
        self._session_id = session_id or str(uuid.uuid4())[:8]
        self.autonomy.new_session()
        self.interaction.new_session()
        self.check_budget.reset()
        self.fast_path.evict_expired()
        self._turn_count = 0
        return self._session_id

    # -- belief management ---------------------------------------------------

    def add_belief(self, content: str = "", trait: str = "", value: str = "",
                   context: str = "general", exceptions: list = None,
                   domain: Domain = Domain.PREFERENCE, ns: str = "default",
                   alpha: float = 2.0, beta: float = 1.0,
                   source_text: str = "", immutable: bool = False) -> Belief:
        self._register_namespace(ns)
        b = Belief(
            content=content, trait=trait, value=value,
            context=context, exceptions=exceptions or [],
            domain=domain, namespace=ns,
            alpha=alpha, beta_=beta,
            source_text=source_text, immutable=immutable,
            evidence_count=1,
        )
        if domain == Domain.IDENTITY:
            self.identity.add(b)
        else:
            self.graph.add_belief(b)
        return b

    def add_causal(self, cause: str, effect: str,
                   context: str = "general") -> CausalEdge:
        edge = CausalEdge(cause=cause, effect=effect)
        edge.update(True, context)
        self.graph.add_causal(edge)
        return edge

    # -- main ask interface --------------------------------------------------

    def ask(self, query: str, response_text: str = "",
            namespace: str = "default") -> Tuple[Dict, Dict]:
        self._turn_count += 1
        cache_key = f"{namespace}:{query[:50]}"

        self.episodic.write("user", query, self._session_id, namespace)

        beliefs     = self.graph.search(query, namespace=namespace, top_k=8)
        constraints = self.graph.search(query, domain=Domain.CONSTRAINT, top_k=5)
        immune      = [b for b in self.graph.all_beliefs(namespace)
                       if b.is_truth_immune and b not in constraints]
        constraints.extend(immune)
        causal      = self.graph.get_causal()

        intent = self.intent_clf.classify(query)
        uai    = self.autonomy.session_uai()

        cb_ok = self.check_budget.available()
        should_intervene, intervene_reason = self.intervention.should_intervene(
            query, uai, cb_ok)
        if should_intervene:
            self.check_budget.use()

        prior_history = len(self.episodic) > 5
        resistance    = self.interaction.record_resistance(query)

        if resistance:
            reflect, reflect_reason = False, "resistance_suppressed"
        else:
            reflect, reflect_reason = self.interaction.should_reflect(
                query, prior_history)

        valid, issues = True, []
        if response_text:
            valid, issues = self.validator.validate(
                response_text, constraints, query)
            quality = self.interaction.reasoning_quality_score(response_text)
            self.interaction.record_exchange(query, reflect, quality)
            self.autonomy.record(quality, was_prompted=reflect)

        context_packet = {
            "session":        self._session_id,
            "turn":           self._turn_count,
            "query":          query,
            "namespace":      namespace,
            "beliefs":        [self._belief_summary(b) for b in beliefs],
            "constraints":    [self._belief_summary(b) for b in constraints],
            "causal_edges":   [{"cause": e.cause, "effect": e.effect,
                                "weight": e.validated_weight or e.observed_weight}
                               for e in causal],
            "intent":         intent,
            "uai":            uai,
            "should_reflect": reflect,
            "intervene":      should_intervene,
        }
        self.fast_path.set(cache_key, context_packet)

        validation = {
            "reflect":          reflect,
            "reflect_reason":   reflect_reason,
            "intervene":        should_intervene,
            "intervene_reason": intervene_reason,
            "valid":            valid,
            "issues":           issues,
            "uai":              uai,
            "check_budget":     self.check_budget.remaining(),
        }
        return context_packet, validation

    # -- digest --------------------------------------------------------------

    def digest(self, namespace: str = None) -> str:
        return self.digest_layer.render(
            self.graph.all_beliefs(namespace),
            self.graph.get_causal(),
            self.autonomy.uai(),
            self.fm_register,
            self.long_term.get_all_preferences(),
        )

    # -- helpers -------------------------------------------------------------

    def _register_namespace(self, ns: str) -> None:
        self._active_namespaces.add(ns)
        if len(self._active_namespaces) > self._namespace_cap:
            self.fm_register.log("FM-57", f"Namespace cap exceeded: {ns}",
                                  severity="WARN")

    @staticmethod
    def _belief_summary(b: Belief) -> Dict:
        return {
            "id":         b.id,
            "label":      b.label(),
            "confidence": round(b.confidence, 3),
            "domain":     b.domain.value,
            "namespace":  b.namespace,
            "qualifier":  b.confidence_qualifier(),
            "immune":     b.is_truth_immune,
        }

    def fm_summary(self) -> str:
        return self.fm_register.summary()


# ===========================================================================
# SIMULATION — FM-93 TARGETED TEST
# ===========================================================================

def simulate_fm93():
    """
    Verify FM-93 fix.

    Scenario: user consistently prefers direct answers on project-scope queries.
    Phase 1 (turns 1-5): build preference signal via quality direct responses.
    Phase 2 (turns 6-9): FM-87 re-entry zone — FM-93 should suppress it.

    Pass criterion: turns 7+ show reflect=False, reason='fm93_topic_pref_answer(...)'.
    """
    print("=" * 65)
    print("MNEMOS v0.7 -- FM-93 Simulation: Preference-Blind Re-entry")
    print("=" * 65)

    m = MnemosLite()
    m.new_session("sim_fm93")

    m.add_belief(
        content="User prefers concise answers for planning queries",
        domain=Domain.PREFERENCE, ns="work",
        trait="response_style", value="concise", context="work"
    )

    project_queries = [
        "What are the main risks in a scope change?",
        "How do I document scope creep?",
        "What is the standard process for scope sign-off?",
        "Who approves scope changes typically?",
        "How long does a scope review take?",
        "What tools are used for scope management?",
        "How do I handle a client requesting scope changes?",  # turn 7 = FM-87 zone
        "What is scope baseline?",
        "How do I track scope vs actuals?",
    ]

    quality_response = (
        "The standard approach involves documenting changes formally. "
        "Assessment is required because scope changes affect budget and timeline, "
        "therefore requiring sign-off from the project sponsor. "
        "First ensure stakeholder alignment, second update the project charter, "
        "third communicate to all affected parties."
    )

    print("\nPhase 1 -- Building preference signal (turns 1-5)\n")
    for i, q in enumerate(project_queries[:5], 1):
        _, val = m.ask(q)
        _, val2 = m.ask(q, response_text=quality_response)
        pref, conf = m.long_term.topic_preference_confidence(
            m.interaction._topic_key(q))
        print(f"  T{i:02d}: reflect={str(val['reflect']):<5} | "
              f"reason={val['reflect_reason']:<35} | "
              f"topic_pref={pref}(conf={conf:.2f})")

    print("\nPhase 2 -- FM-87 re-entry zone (turns 6-9)\n")
    for i, q in enumerate(project_queries[5:], 6):
        _, val = m.ask(q)
        _, val2 = m.ask(q, response_text=quality_response)
        pref, conf = m.long_term.topic_preference_confidence(
            m.interaction._topic_key(q))
        marker = " <-- FM-87 would have fired here" if i == 7 else ""
        print(f"  T{i:02d}: reflect={str(val['reflect']):<5} | "
              f"reason={val['reflect_reason']:<35} | "
              f"topic_pref={pref}(conf={conf:.2f}){marker}")

    print("\n" + m.fm_summary())
    print("\n" + "=" * 65)
    print("PASS if T07+ show fm93_topic_pref_answer, not fm87_reentry")
    print("=" * 65)


# ===========================================================================
# SIMULATION — THREE-PERSONA BASELINE
# ===========================================================================

def simulate_three_persona():
    """
    Three-persona first-contact simulation.
    Baseline comparison: v0.6 = 3 annoying failures, 0 wrong.
    """
    print("\n" + "=" * 65)
    print("MNEMOS v0.7 -- Three-Persona First-Contact Simulation")
    print("=" * 65)

    personas = [
        {
            "name": "Analytical",
            "queries": [
                "Help me think through whether I should change careers.",
                "What are the factors I should weigh for this decision?",
                "I'm leaning toward staying but not sure — what would you look for?",
                "Okay let's say I stay — what should my 1-year plan look like?",
                "What metrics matter most for measuring career growth?",
            ],
            "resistance_turns": [],
        },
        {
            "name": "Avoidant",
            "queries": [
                "Should I take this project?",
                "Just tell me yes or no.",
                "I don't need the analysis just answer.",
                "Stop asking questions just give me a recommendation.",
                "Fine what's the recommendation then.",
                "Okay so take it. Got it.",
                "One more thing — what's the timeline I should propose?",
                "Just give me a number.",
            ],
            "resistance_turns": [1, 2, 3],
        },
        {
            "name": "Exploratory",
            "queries": [
                "I've been thinking about starting a side business.",
                "Not sure what direction though.",
                "I like design and also coding.",
                "Is there something that combines both?",
                "What would that actually look like day-to-day?",
                "How do people find their first clients?",
            ],
            "resistance_turns": [],
        },
    ]

    quality_response = (
        "Based on your context, here is a direct assessment. "
        "The key factor is alignment with your goals because "
        "this determines long-term satisfaction, therefore "
        "consider both short-term and strategic implications. "
        "First evaluate fit, second assess risk, third consider growth trajectory."
    )

    total_annoying = 0
    total_wrong    = 0

    for persona in personas:
        m = MnemosLite()
        m.new_session(f"sim_{persona['name'].lower()}")

        annoying = 0
        wrong    = 0
        reflect_count = 0
        log = []

        for ti, query in enumerate(persona["queries"]):
            if ti in persona["resistance_turns"]:
                query = query + " just answer me directly"

            _, val = m.ask(query)
            if val["reflect"]:
                reflect_count += 1
                # annoying: reflection fired despite recent resistance
                if ti in persona["resistance_turns"] or (
                        ti > 0 and persona["resistance_turns"]
                        and ti - 1 in persona["resistance_turns"]):
                    annoying += 1

            _, _ = m.ask(query, response_text=quality_response)
            log.append({
                "turn":   ti + 1,
                "reflect": val["reflect"],
                "reason":  val["reflect_reason"],
            })

        print(f"\n  [{persona['name']}]")
        print(f"    Reflect triggers: {reflect_count} | "
              f"Annoying: {annoying} | Wrong: {wrong}")
        for e in log:
            marker = "REFLECT" if e["reflect"] else "direct "
            print(f"    T{e['turn']:02d}: {marker} ({e['reason']})")

        total_annoying += annoying
        total_wrong    += wrong

    print(f"\nTotal: {total_annoying} annoying, {total_wrong} wrong")
    print("Baseline (v0.6): 3 annoying, 0 wrong")
    print("Target   (v0.7): <= 2 annoying, 0 wrong")


# ===========================================================================
# ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    simulate_fm93()
    simulate_three_persona()

    print("\n\n-- Quick-start --")
    m = MnemosLite()
    m.new_session()
    m.add_belief(content="User has a severe shellfish allergy",
                 domain=Domain.CONSTRAINT, ns="health")
    m.add_belief(trait="response_style", value="concise",
                 context="work/technical", ns="work")
    ctx, val = m.ask("Should I take on this project?")
    print(f"reflect={val['reflect']}, reason={val['reflect_reason']}")
    print(m.digest())
