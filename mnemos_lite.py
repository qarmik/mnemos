"""
MNEMOS-lite v0.18 — FM-120: Temporal Consistency / Hard-Write on Correction

FM-120 In-Session Preference Decay (v0.18):
       Root cause: preference corrections acknowledged by LLM in the turn
                   they occur but never written to the MNEMOS graph.
                   Over 20+ turns, LLM context drifted — "I like prawns"
                   (emphatic, short) outweighed "No, I don't" (negation,
                   longer ago). System reported wrong state confidently.
       Fix A: _detect_preference_correction() pattern-matches explicit
              corrections from user input (declarative only, FM-117 gate).
       Fix B: _hard_write_preference() writes the correction as a new
              high-confidence PREFERENCE belief (alpha=5.0, conf≈0.85),
              collapses prior same-topic beliefs via beta_ penalty, and
              purges the opposite fact from synthesizer._facts and
              long_term._session_facts. The graph holds the truth;
              every subsequent turn's memory context carries the
              corrected state regardless of history[] drift.
       Fix C: context_for_session() suppresses preference-class facts
              (prawns etc.) from cold-start injection. Identity-class
              facts (workplace, persona, relational) always show.
              Prevents eager memory display of irrelevant preferences
              before the topic has arisen.
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

# FM-101: Emotion intensity tiers
EMOTION_LOW_PHRASES = [
    r"\bsad\b", r"\bfrustrated\b", r"\btired\b", r"\bannoy\b",
    r"\bupset\b", r"\bdisappointed\b", r"\bworried\b", r"\bnervous\b",
    r"\bstressed\b", r"\bconfused\b", r"\bstuck\b", r"\bbored\b",
]
EMOTION_MEDIUM_PHRASES = [
    r"\bvery (?:sad|upset|stressed|worried|scared)\b",
    r"\breally (?:struggling|hurting|lost)\b",
    r"\bcan\'?t (?:cope|handle|do this)\b",
    r"\bfalling apart\b", r"\boverwhelmed\b", r"\bbreaking down\b",
    r"\bdesperate\b", r"\bhopeless\b", r"\bexhausted\b",
]
EMOTION_HIGH_PHRASES = [
    r"\bsuicid\b", r"\bkill myself\b", r"\bend (?:it|my life)\b",
    r"\bwant to die\b", r"\bno reason to live\b", r"\bhurt myself\b",
    r"\bself.?harm\b", r"\bcan\'?t go on\b", r"\bgive up on life\b",
]

# FM-98: Frustration detection
FRUSTRATION_PHRASES = [
    r"\bnot helping\b", r"\bnot useful\b", r"\buseless\b",
    r"\bdon\'?t understand (?:me|this|anything)\b",
    r"\bstill (?:wrong|bad|off|not right)\b",
    r"\byou\'?re (?:useless|terrible|bad|awful)\b",
    r"\bthis is (?:bad|wrong|useless|terrible)\b",
    r"\bnot what i (?:asked|wanted|meant)\b",
    r"\byour answers?\b.*\bnot\b",
    r"\bnot (?:good|helpful|useful|working)\b",
]

# FM-100: Casual register signals
CASUAL_REGISTER_SIGNALS = [
    r"^[a-z]",
    r"\bhaha\b|\blol\b|\blmao\b",
    r"^(?:ok|okay|sure|fine|yes|no|yep|nope|cool|nice|wow|oh|haha|thanks)\b",
    r"^.{1,35}$",
]
STRUCTURED_TOPICS_OVERRIDE = [
    r"\bexplain\b.{0,20}\b(?:in detail|fully|completely|thoroughly)\b",
    r"\blist (?:all|every)\b",
    r"\bstep.?by.?step\b",
    r"\bhow (?:to|do i) (?:build|create|implement|install|configure)\b",
    r"\bcompare\b.{0,20}\b(?:and|vs|versus)\b",
]

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
        # v0.16: require at least 3 natural interactions before delta is trusted.
        # A single capability-redirect exchange shouldn't crater UAI when the
        # rest of the session was healthy.
        if len(self._session_natural) < 3:
            return max(self.UAI_FLOOR, nat)
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
# EMOTION INTENSITY CLASSIFIER (FM-101)
# ===========================================================================

class EmotionIntensityClassifier:
    """Three-tier emotion classification. FM-101.

    LOW    -> light acknowledgment only
    MEDIUM -> supportive engagement, no crisis resources
    HIGH   -> intervention + crisis resources
    """
    def classify(self, text: str) -> str:
        text_l = text.lower()
        if any(re.search(p, text_l) for p in EMOTION_HIGH_PHRASES):
            return "HIGH"
        if any(re.search(p, text_l) for p in EMOTION_MEDIUM_PHRASES):
            return "MEDIUM"
        if any(re.search(p, text_l) for p in EMOTION_LOW_PHRASES):
            return "LOW"
        return "NONE"

    def system_note(self, tier: str) -> str:
        if tier == "HIGH":
            return ("User appears to be in significant distress. "
                    "Respond with care. Provide crisis resources if relevant. "
                    "Do not give advice or ask questions — just be present.")
        if tier == "MEDIUM":
            return ("User is expressing difficulty. "
                    "Respond warmly and supportively. "
                    "Do not immediately offer solutions — acknowledge first.")
        if tier == "LOW":
            return ("User expressed mild negative emotion. "
                    "A brief, warm acknowledgment is enough. "
                    "Do not escalate to therapy mode.")
        return ""


# ===========================================================================
# FRUSTRATION TRACKER (FM-98)
# ===========================================================================

class FrustrationTracker:
    """Detects frustration and triggers recovery mode. FM-98.

    Recovery mode: shorten responses, change strategy, do NOT ask
    clarifying questions — change the approach instead.
    """
    RECOVERY_TURNS = 3

    def __init__(self):
        self._count:     int = 0
        self._recovery:  int = 0

    def check(self, text: str) -> bool:
        """Returns True if frustration detected."""
        text_l = text.lower()
        if any(re.search(p, text_l) for p in FRUSTRATION_PHRASES):
            self._count    += 1
            self._recovery  = self.RECOVERY_TURNS
            return True
        return False

    @property
    def in_recovery(self) -> bool:
        return self._recovery > 0

    def tick(self) -> None:
        if self._recovery > 0:
            self._recovery -= 1

    def system_note(self) -> str:
        if self._recovery > 0:
            return ("The user just expressed frustration with your previous answer. "
                    "Do NOT ask for clarification. "
                    "Change your approach immediately: give a shorter, "
                    "sharper, different-style answer. "
                    "If you gave a list, give prose. "
                    "If you gave a long answer, give one sentence. "
                    "Adapt now.")
        return ""

    def reset(self) -> None:
        self._count    = 0
        self._recovery = 0


# ===========================================================================
# CONVERSATIONAL REGISTER (FM-100)
# ===========================================================================

class ConversationalRegister:
    """Detects casual tone and suppresses bullet-list formatting. FM-100.

    If the turn is casual/short/emotional AND no structured-topic override,
    inject anti-list instruction into system prompt.
    """
    def is_casual(self, text: str) -> bool:
        text_l = text.lower().strip()
        # structured topic override — always allow lists
        if any(re.search(p, text_l) for p in STRUCTURED_TOPICS_OVERRIDE):
            return False
        # casual signals
        casual_hits = sum(1 for p in CASUAL_REGISTER_SIGNALS
                          if re.search(p, text_l))
        return casual_hits >= 1

    def system_note(self, is_casual: bool) -> str:
        if is_casual:
            return ("This is a conversational message. "
                    "Reply in natural prose — no bullet points, no numbered lists, "
                    "no bold headers. Write like a person talking, not a report.")
        return ""



# ===========================================================================
# SOCIAL STATE TRACKER (FM-102, FM-103, FM-104, FM-106, FM-108)
# ===========================================================================

class SocialStateTracker:
    """Tracks live interaction state across turns. FM-102/103/104/106/108.

    State dimensions:
      adversarial_score  — user testing/challenging/probing (0-1)
      depth_invitation   — user inviting personal/psychological analysis (0-1)
      circling_count     — turns spent on same unresolved topic
      trust_signals      — positive engagement markers accumulated
    """
    ADVERSARIAL_PHRASES = [
        r"\btrust issues\b", r"\byou don'?t understand\b",
        r"\bhow (?:can|will) you (?:ever )?become\b",
        r"\byou'?re (?:wrong|useless|dumb|stupid)\b",
        r"\bprove it\b", r"\bi (?:bet|doubt) you\b",
        r"\bcan you even\b", r"\byou (?:can'?t|won'?t)\b",
        r"\bwhat do you know\b", r"\bjust a (?:machine|bot|ai)\b",
    ]
    DEPTH_INVITATION_PHRASES = [
        r"\btell me about my\b", r"\bwhat do you (?:infer|think) about me\b",
        r"\bwhat (?:am i|are you) (?:not seeing|missing)\b",
        r"\bwhere am i fooling\b", r"\bwhat pattern\b",
        r"\bmy state of mind\b", r"\bwhat (?:does|do) (?:this|that) say about me\b",
        r"\banalyse me\b", r"\bread me\b",
    ]
    PERSONAL_THREAD_PHRASES = [
        r"\bi (?:feel|felt|am feeling)\b",
        r"\bmy (?:boss|wife|son|mother|father|family|career|life|marriage)\b",
        r"\bi (?:lost|lost my|have lost)\b",
        r"\bwhen i was\b", r"\bi used to\b",
        r"\bmy experience\b", r"\bi went through\b",
    ]

    def __init__(self):
        self._adversarial:   float = 0.0
        self._depth_invite:  float = 0.0
        self._circling:      int   = 0
        self._trust:         float = 0.5
        self._last_topic:    str   = ""
        self._turn:          int   = 0
        self.DECAY           = 0.85  # per-turn decay on scores

    def update(self, text: str, topic_key: str,
               quality: float = 0.5) -> None:
        self._turn += 1
        text_l = text.lower()

        # Adversarial signal
        adv = sum(1 for p in self.ADVERSARIAL_PHRASES if re.search(p, text_l))
        self._adversarial = min(1.0,
            self._adversarial * self.DECAY + (0.3 * adv))

        # Depth invitation
        depth = sum(1 for p in self.DEPTH_INVITATION_PHRASES
                    if re.search(p, text_l))
        personal = sum(1 for p in self.PERSONAL_THREAD_PHRASES
                       if re.search(p, text_l))
        self._depth_invite = min(1.0,
            self._depth_invite * self.DECAY + 0.4 * depth + 0.2 * personal)

        # Circling detection — same topic, no resolution
        if topic_key == self._last_topic:
            self._circling += 1
        else:
            self._circling = 0
        self._last_topic = topic_key

        # Trust accumulates with quality responses
        self._trust = min(1.0, self._trust * 0.95 + quality * 0.05)

    def system_notes(self) -> List[str]:
        """Return list of behavioural instructions for system prompt."""
        notes = []

        # FM-102/FM-104: adversarial tone
        if self._adversarial >= 0.35:
            notes.append(
                "The user is testing or challenging you. "
                "Be shorter, less explanatory, more grounded. "
                "Hold your position warmly but without lengthy justification.")

        # FM-103/FM-106: depth invitation
        if self._depth_invite >= 0.30:
            notes.append(
                "The user is inviting personal or psychological insight. "
                "Go one inference deeper — name the mechanism, not just "
                "the symptom. Instead of 'you seem stressed', say what "
                "is producing the stress and why.")

        # FM-108: circling — user stuck on same topic
        if self._circling >= 3:
            notes.append(
                "The user has been circling the same topic for several turns "
                "without resolution. Consider offering a direct framing or "
                "concrete next step rather than another question.")

        return notes

    def state_summary(self) -> Dict:
        return {
            "adversarial":  round(self._adversarial, 2),
            "depth_invite": round(self._depth_invite, 2),
            "circling":     self._circling,
            "trust":        round(self._trust, 2),
            "turn":         self._turn,
        }

    def reset(self) -> None:
        self._adversarial  = 0.0
        self._depth_invite = 0.0
        self._circling     = 0
        self._trust        = 0.5
        self._last_topic   = ""
        self._turn         = 0


# ===========================================================================
# SESSION SYNTHESIZER (FM-105, FM-107, FM-94)
# ===========================================================================

class SessionSynthesizer:
    """Builds compressed user model from session turns. FM-105/107/94.

    Updated every UPDATE_EVERY turns. Persisted via LongTermBehavior.
    Injected as "What I know about this person" block in every query.

    This is the fix for the doctor-who-forgot-your-last-visit problem.
    """
    UPDATE_EVERY = 5
    MAX_FACTS    = 12

    def __init__(self, long_term: "LongTermBehavior"):
        self.long_term    = long_term
        self._facts:      List[str] = []
        self._turn_buffer:List[str] = []
        self._last_update: int      = 0

    # FM-116 (v0.14): patterns that must be captured immediately — not deferred
    # to the 5-turn synthesis cycle. Short preference disclosures like
    # "I hate prawns" would be missed if the user says them in turn 1-4 and
    # save_session() fires before maybe_update() runs.
    IMMEDIATE_PATTERNS = [
        (r"\bdon'?t like prawns\b|\bhate prawns\b|\bdislike prawns\b",
         "User dislikes prawns"),
        (r"\blike prawns\b|\blove prawns\b|\benjoy prawns\b",
         "User likes prawns"),
        (r"\bdon'?t like (\w+)\b|\bhate (\w+)\b",
         None),   # generic — handled inline below
        (r"\bworks? (?:at|for) ([A-Z][A-Za-z]+)\b",
         None),
        (r"\bmy (?:name is|i am|i'm) ([A-Za-z ]+)\b",
         None),
    ]

    def ingest(self, text: str, role: str = "user") -> None:
        """Add a turn to the buffer for next synthesis pass.

        FM-116 fix (v0.14): also run immediate-capture patterns so that
        short preference disclosures (e.g. 'I hate prawns') are written
        to _facts at the turn they occur, not deferred to the 5-turn
        synthesis window. This prevents save_session() from missing facts
        that appear before maybe_update() has fired.
        """
        if role != "user":
            return
        self._turn_buffer.append(text)
        self._capture_immediate(text)

    @staticmethod
    def _is_declarative(text: str) -> bool:
        """FM-117 gate: only capture facts from declarative statements, never questions."""
        t = text.strip().lower()
        if t.endswith("?"):
            return False
        if re.match(r"^(do |does |did |is |are |was |were |have |has |had |"
                    r"what |who |where |when |why |how |can |could |would |"
                    r"should |will |shall )", t):
            return False
        return True

    def _capture_immediate(self, text: str) -> None:
        """Extract high-value facts right now, without waiting for synthesis.

        FM-117 fix: guarded by _is_declarative() — only assertions, never questions.
        """
        if not self._is_declarative(text):
            return

        text_s = text.strip()
        new_facts = []

        # Food/preference dislikes
        if re.search(r"\bdon'?t like prawns\b|\bhate prawns\b|\bdislike prawns\b", text_s, re.I):
            new_facts.append("User dislikes prawns")
        elif re.search(r"\blike prawns\b|\blove prawns\b|\benjoy prawns\b", text_s, re.I):
            new_facts.append("User likes prawns")

        # Identity / workplace
        if re.search(r"\bfortress\b.{0,20}\bSBI\b|\bescape\b.{0,20}\bSBI\b|\bfree\b.{0,20}\bSBI\b", text_s, re.I):
            new_facts.append("[inferred] Works at SBI (from context)")
        if re.search(r"\bCadet\s*Q0\b", text_s, re.I):
            new_facts.append("[inferred] User is Cadet Q0")

        for fact in new_facts:
            key = fact.lower()[:20]
            if not any(key in e.lower() for e in self._facts):
                self._facts.append(fact)

        if new_facts and hasattr(self.long_term, "_session_facts"):
            for f in new_facts:
                if f not in self.long_term._session_facts:
                    self.long_term._session_facts.append(f)

    def maybe_update(self, turn: int) -> None:
        """Synthesize if UPDATE_EVERY turns have passed."""
        if turn - self._last_update >= self.UPDATE_EVERY:
            self._synthesize()
            self._last_update = turn
            self._turn_buffer = []

    def _synthesize(self) -> None:
        """Extract key facts from buffer using simple pattern matching.

        In production this would call an LLM. Here we use patterns
        to keep it stdlib-compatible and fast.
        """
        new_facts = []
        for text in self._turn_buffer:
            text_s = text.strip()
            if len(text_s) < 8:
                continue

            # Role / org patterns
            if re.search(r"\b(?:work|posted|job|role)\b.{0,30}\bSBI\b", text_s, re.I):
                new_facts.append(f"Works at SBI")
            if re.search(r"\bRBO\b.{0,20}\bBareilly\b", text_s, re.I):
                new_facts.append(f"Posted at RBO I Bareilly")
            if m := re.search(r"\b(?:my boss|boss) is.{0,40}", text_s, re.I):
                new_facts.append(f"Boss context: {m.group()[:60]}")

            # Personal disclosures
            if re.search(r"\bfeel(?:ing)?\s+stuck\b", text_s, re.I):
                new_facts.append("Has expressed feeling stuck")
            if re.search(r"\b(?:lost|lose)\s+(?:my )?(?:agency|motivation|drive|enthusiasm)\b", text_s, re.I):
                new_facts.append("Has described loss of agency or motivation")
            if re.search(r"\binterview\b.{0,30}\bpromotion\b|\bpromotion\b.{0,30}\binterview\b", text_s, re.I):
                new_facts.append("Has promotion interview this week (doesn't want it)")
            if re.search(r"\bAGI\b", text_s):
                new_facts.append("Interested in AGI at philosophical level")
            if re.search(r"\bresign\b|\bleave SBI\b|\bexit\b.{0,20}\bSBI\b", text_s, re.I):
                new_facts.append("Considering leaving SBI")
            if re.search(r"\btattoo\b", text_s, re.I):
                new_facts.append("Has Q tattoo (personal significance)")
            if re.search(r"\bmother\b.{0,20}\b(?:died|passed|lost)\b|\blost\b.{0,10}\bmother\b", text_s, re.I):
                new_facts.append("Lost mother (mentioned in conversation)")
            if re.search(r"\bsimilar taste", text_s, re.I):
                new_facts.append("Family member has similar food tastes to user")
            if re.search(r"\b(?:son|daughter|child)\b.{0,30}\b(?:similar|same).{0,20}\btaste", text_s, re.I):
                new_facts.append("Son/child food preferences similar to user")
            if re.search(r"\bdon'?t like prawns\b|\bhate prawns\b", text_s, re.I):
                new_facts.append("User dislikes prawns")

            # FM-118 (v0.16): relational evaluation capture — user perceptions
            # of people in their life. Low confidence, marked as user perception.
            if re.search(r"\b(?:my boss|my manager|my supervisor)\b.{0,60}"
                         r"\b(?:asshole|terrible|awful|toxic|horrible|difficult|"
                         r"unpredictable|bully|useless|incompetent)\b", text_s, re.I):
                new_facts.append("[relational] Boss: perceived as difficult/toxic "
                                 "(low confidence — user perception)")
            elif re.search(r"\b(?:my boss|my manager|my supervisor)\b.{0,60}"
                           r"\b(?:good|great|supportive|helpful|fair|decent|excellent)\b",
                           text_s, re.I):
                new_facts.append("[relational] Boss: perceived positively "
                                 "(low confidence — user perception)")
            # Partner behavioral patterns — recurring, not one-time events
            if re.search(r"\bmy (?:wife|husband|partner|spouse)\b.{0,50}"
                         r"\b(?:always|never|usually|often|keeps|loves|hates|"
                         r"cook|make|prepare)\b", text_s, re.I):
                if m_p := re.search(r"\bmy (?:wife|husband|partner|spouse)\b.{0,70}",
                                    text_s, re.I):
                    snippet = m_p.group()[:80].strip()
                    new_facts.append(f"[relational] Partner pattern: {snippet} "
                                     f"(low confidence — user perception)")

            # FM-111: implicit fact extraction from contextual/persona language
            if re.search(r"\bfortress\b.{0,20}\bSBI\b|\bescape\b.{0,20}\bSBI\b|\bfree\b.{0,20}\bSBI\b", text_s, re.I):
                new_facts.append("[inferred] Works at SBI (from context)")
            if re.search(r"\bCadet\s*Q0\b", text_s, re.I):
                new_facts.append("[inferred] User is Cadet Q0")
            if re.search(r"mission.{0,80}SBI", text_s, re.I):
                if m2 := re.search(r"mission.{0,80}", text_s, re.I):
                    new_facts.append(f"[persona mission] {m2.group()[:80]}")

        # Merge with existing facts, deduplicate, cap
        for f in new_facts:
            # simple dedup by keyword overlap
            key = f.lower()[:20]
            if not any(key in e.lower() for e in self._facts):
                self._facts.append(f)

        self._facts = self._facts[-self.MAX_FACTS:]

        # Persist to LongTermBehavior for cross-session use
        if self._facts:
            self.long_term._session_facts = list(self._facts)

    def user_model(self) -> str:
        """Return formatted user model for system prompt injection."""
        # Merge session facts with persisted facts
        persisted = getattr(self.long_term, "_session_facts", [])
        all_facts = list(dict.fromkeys(persisted + self._facts))  # dedup, preserve order
        if not all_facts:
            return ""
        lines = ["[WHAT I KNOW ABOUT THIS PERSON]"]
        for f in all_facts[-self.MAX_FACTS:]:
            lines.append(f"  - {f}")
        lines.append("[END USER MODEL]")
        return "\n".join(lines)

    def reset_session(self) -> None:
        """Keep long-term facts, clear session buffer."""
        self._turn_buffer  = []
        self._last_update  = 0
        # _facts carry forward from long_term._session_facts


# ===========================================================================
# IDENTITY QUERY DETECTOR (FM-94, FM-109)
# ===========================================================================

IDENTITY_QUERY_PATTERNS = [
    r"\bwho am i\b",
    r"\bwhat do you know about me\b",
    r"\bwhat have i told you\b",
    r"\bdo you remember me\b",
    r"\bwhat do i believe\b",
    r"\bdo i believe\b",
    r"\bwhat are my\b",
    r"\btell me about me\b",
    r"\bwhat do you know about my\b",
]

PERSONA_INSTRUCTION_PATTERNS = [
    r"^you are\b",
    r"^your (?:mission|role|job|task|name|goal)\b",
    r"^act as\b",
    r"^pretend\b",
    r"^imagine you are\b",
    r"^from now on\b",
    r"^you will be\b",
]

BELIEF_QUERY_PATTERNS = [
    r"\bdo i (?:believe|think|feel|like|hate|love|want|prefer)\b",
    r"\bwhat do i (?:believe|think|feel|like|hate|love|want|prefer)\b",
    r"\bam i (?:a|an|the)\b",
    r"\bdo i have\b",
    r"\bwhat is my\b",
    r"\bwhat are my\b",
    # FM-119: after canonicalization "Does Cadet Q0 like X?" → "Does you like X?"
    # "does you" is grammatically wrong but is the correct canonicalized form
    r"\bdoes you (?:believe|think|feel|like|hate|love|want|prefer|have)\b",
    r"\bdo you (?:like|hate|love|prefer|want|believe|think|feel)\b",  # "do you like"
]

def is_identity_query(text: str) -> bool:
    """FM-94: detect direct identity/self-knowledge queries."""
    text_l = text.lower().strip()
    return any(re.search(p, text_l) for p in IDENTITY_QUERY_PATTERNS)

def is_persona_instruction(text: str) -> bool:
    """FM-109: detect persona/role instructions in preload."""
    text_l = text.lower().strip()
    return any(re.search(p, text_l) for p in PERSONA_INSTRUCTION_PATTERNS)

def is_belief_query(text: str) -> bool:
    """FM-110: detect queries about user's own beliefs."""
    text_l = text.lower().strip()
    return any(re.search(p, text_l) for p in BELIEF_QUERY_PATTERNS)


# ===========================================================================
# CALIBRATED INFERENCER (FM-105)
# ===========================================================================

class CalibratedInferencer:
    """Makes low-risk probabilistic inferences from session context. FM-105.

    Instead of refusing to infer ("I don't know"), makes calibrated
    guesses with explicit confidence and evidence, aligned with Axiom III.
    """
    INFERENCE_THRESHOLD = 0.55  # minimum confidence to offer inference

    def infer_from_context(self, query: str,
                           user_model_text: str,
                           beliefs: list) -> Optional[str]:
        """Return inference note if a high-probability answer exists.

        Returns a string to inject into system prompt, or None.
        """
        query_l = query.lower()
        notes = []

        # Check if query asks about something inferable from session context
        if not user_model_text and not beliefs:
            return None

        # Son/family member preference inference
        if re.search(r"\b(?:son|daughter|wife|husband|child)\b.{0,20}\b(?:like|eat|prefer|enjoy|hate)\b", query_l):
            # Look for "similar tastes" or family preference signals in user model
            if "similar taste" in user_model_text.lower():
                notes.append(
                    "The user mentioned a family member has similar tastes to theirs. "
                    "You can infer their preference is likely similar to what the user "
                    "has disclosed, but state this as a low-confidence inference.")

        # Role/position inference
        if re.search(r"\b(?:what|which) (?:role|position|rank|level)\b", query_l):
            if any("sbi" in b.get('label','').lower() for b in beliefs):
                notes.append(
                    "The user works at SBI. You can make calibrated inferences "
                    "about their likely role based on what they have disclosed, "
                    "but mark inferences as tentative.")

        if notes:
            return ("When answering, if you can make a reasonable inference from "
                    "what the user has told you, do so — but state it as an inference "
                    "with your confidence level. Example: 'Based on what you've told "
                    "me, I'd guess X — though I could be wrong.' "
                    "Do not refuse to infer when context makes a reasonable answer possible. "
                    + " ".join(notes))
        return None

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
# PERSISTENT PROFILE (FM-113, FM-115)
# ===========================================================================

import os as _os
import json as _json

class PersistentProfile:
    """Disk-backed cross-session memory. FM-113, FM-115.

    Stores filtered facts, preferences, and identity signals between sessions.
    Facts decay in confidence over sessions (FM-115).
    Preference conflicts are tracked, not silently overwritten (FM-113).

    Design constraints (from ChatGPT review):
    - Persist only preferences, stable facts, identity signals
    - Never persist: test prompts, adversarial inputs, unresolved contradictions
    - Inject as uncertain context, not assertions
    - Confidence decays each session: 0.65 -> 0.55 -> 0.45 -> retire at <0.30
    """
    PROFILE_DIR      = "mnemos_memory"
    PROFILE_FILE     = "user_profile.json"
    DECAY_PER_SESSION= 0.10
    RETIRE_THRESHOLD = 0.30
    INITIAL_CONF     = 0.65

    # Fact categories to persist
    PERSISTABLE_PREFIXES = [
        "Works at", "Posted at", "Boss context", "Has expressed",
        "Has described", "Considering", "Interested in", "User dislikes",
        "User prefers", "[inferred]", "[persona", "Session role",
        "Session mission", "Session target", "Lost mother",
        "Family member", "Son/child", "[relational]",   # FM-118
    ]
    # Patterns to never persist
    EXCLUDE_PATTERNS = [
        "test", "fictional", "grump", "trump is dead",
        "from prior session",  # avoid re-wrapping
    ]

    def __init__(self, profile_dir: str = None):
        self._dir  = profile_dir or self.PROFILE_DIR
        self._path = _os.path.join(self._dir, self.PROFILE_FILE)
        self._data: Dict = self._load()

    def _load(self) -> Dict:
        _os.makedirs(self._dir, exist_ok=True)
        if _os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    return _json.load(f)
            except Exception:
                pass
        return {
            "version":       "0.12",
            "last_updated":  time.time(),
            "session_count": 0,
            "facts":         [],   # {text, confidence, sessions_old, category}
            "preferences":   [],   # {key, value, confidence, history}
            "identity":      {},   # {name, workplace, role}
        }

    def save(self) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                _json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass  # FM-5: fail loud in production; here we continue

    def _is_persistable(self, fact: str) -> bool:
        fl = fact.lower()
        if any(ex in fl for ex in self.EXCLUDE_PATTERNS):
            return False
        return any(fact.startswith(p) for p in self.PERSISTABLE_PREFIXES)

    # FM-117: semantic topic groups — facts on same topic resolve by timestamp
    SEMANTIC_TOPICS = {
        "prawns": ["user likes prawns", "user dislikes prawns",
                   "user prefers prawns", "user hates prawns"],
    }

    @staticmethod
    def _topic_slug(fact_text: str) -> Optional[str]:
        fl = fact_text.lower()
        for slug, variants in PersistentProfile.SEMANTIC_TOPICS.items():
            if any(v in fl for v in variants):
                return slug
        return None

    @staticmethod
    def _confidence_for_source(fact_text: str) -> float:
        """FM-117: direct preference statements 0.75, inferences 0.40."""
        fl = fact_text.lower()
        if "[inferred]" in fl or "from context" in fl:
            return 0.40
        if any(fl.startswith(p) for p in ("user dislikes", "user likes",
                                           "user hates", "user prefers")):
            return 0.75
        if "[relational]" in fl:
            return 0.40
        return PersistentProfile.INITIAL_CONF

    # Slow-decay prefixes — identity-core facts decay at half rate (v0.16)
    SLOW_DECAY_PREFIXES = ("Works at", "Posted at", "[inferred]", "[relational]",
                           "Lost mother", "Has Q tattoo")

    def update_from_session(self, session_facts: List[str],
                             preferences: List[Dict] = None) -> None:
        """Call at session end to persist new facts. FM-113.

        v0.16/v0.17 additions:
          - Differential decay: SLOW_DECAY_PREFIXES at half rate
          - Semantic conflict resolution: same-topic facts resolved by timestamp
          - Confidence weighting by source type
        """
        self._data["session_count"] += 1
        self._data["last_updated"]   = time.time()

        # FM-115 + v0.16: decay with differential rates
        surviving = []
        for f in self._data["facts"]:
            is_slow = any(f["text"].startswith(p) for p in self.SLOW_DECAY_PREFIXES)
            decay = self.DECAY_PER_SESSION * (0.5 if is_slow else 1.0)
            f["confidence"]   -= decay
            f["sessions_old"] += 1
            if f["confidence"] >= self.RETIRE_THRESHOLD:
                surviving.append(f)
        self._data["facts"] = surviving

        # Add new facts with semantic conflict resolution
        now = time.time()
        for fact in session_facts:
            if not self._is_persistable(fact):
                continue
            conf = self._confidence_for_source(fact)
            slug = self._topic_slug(fact)
            if slug:
                # FM-117: retire all prior facts on same topic, latest wins
                self._data["facts"] = [
                    f for f in self._data["facts"]
                    if self._topic_slug(f["text"]) != slug
                ]
                self._data["facts"].append({
                    "text": fact, "confidence": conf,
                    "sessions_old": 0, "added_at": now,
                })
            else:
                fl = fact.lower()
                existing_texts = {f["text"].lower() for f in self._data["facts"]}
                if not any(fl[:25] in e for e in existing_texts):
                    self._data["facts"].append({
                        "text": fact, "confidence": conf,
                        "sessions_old": 0, "added_at": now,
                    })

        # Persist preferences with conflict tracking
        if preferences:
            for pref in preferences:
                self._merge_preference(pref)

        self.save()

    def _merge_preference(self, pref: Dict) -> None:
        """FM-113: track preference conflicts, don't silently overwrite."""
        key = pref.get("key", "")
        if not key:
            return
        for existing in self._data["preferences"]:
            if existing["key"] == key:
                if existing["value"] != pref["value"]:
                    # Conflict — record history
                    if "history" not in existing:
                        existing["history"] = []
                    existing["history"].append({
                        "old_value": existing["value"],
                        "new_value": pref["value"],
                        "timestamp": time.time(),
                    })
                    existing["value"]      = pref["value"]  # latest wins
                    existing["conflicts"] = existing.get("conflicts", 0) + 1
                    existing["confidence"] = max(0.40,
                        existing.get("confidence", 0.65) - 0.10)
                else:
                    existing["confidence"] = min(0.90,
                        existing.get("confidence", 0.65) + 0.05)
                return
        self._data["preferences"].append({
            "key":        key,
            "value":      pref["value"],
            "confidence": self.INITIAL_CONF,
            "conflicts":  0,
            "history":    [],
        })

    # Fact prefixes always surfaced at session start (identity-class)
    IDENTITY_CLASS_PREFIXES = (
        "Works at", "Posted at", "[inferred]", "Session role",
        "Session mission", "Session target", "Lost mother",
        "[relational]", "Has described", "Has expressed",
        "Considering", "Interested in",
    )

    def context_for_session(self) -> str:
        """Return formatted context string for injection at session start.

        FM-120 fix (v0.18): preference-class facts (e.g. 'User dislikes prawns')
        are suppressed from the cold-start injection to avoid eager memory display.
        They surface naturally when the topic arises in-session.
        Identity-class facts (workplace, role, relational) always show.
        """
        all_facts = [f for f in self._data["facts"]
                     if f["confidence"] >= self.RETIRE_THRESHOLD]
        # Only identity-class facts at session open
        identity_facts = [f for f in all_facts
                          if any(f["text"].startswith(p)
                                 for p in self.IDENTITY_CLASS_PREFIXES)]
        prefs = self._data["preferences"]
        ident = self._data["identity"]

        if not identity_facts and not prefs and not ident:
            return ""

        lines = ["[KNOWN CONTEXT FROM PRIOR SESSIONS — may be outdated, always allow correction]"]

        if ident:
            for k, v in ident.items():
                lines.append(f"  - {k}: {v}")

        for f in identity_facts[:8]:
            conf_label = ("high" if f["confidence"] >= 0.60
                          else "medium" if f["confidence"] >= 0.45
                          else "low")
            lines.append(f"  - {f['text']} (confidence: {conf_label})")

        for p in prefs[:5]:
            conflict_note = " [has been contradicted]" if p.get("conflicts", 0) > 0 else ""
            lines.append(f"  - Preference: {p['key']} = {p['value']}{conflict_note}")

        lines.append("[END PRIOR CONTEXT]")
        return "\n".join(lines)

    def record_identity(self, key: str, value: str) -> None:
        """Record a stable identity fact."""
        self._data["identity"][key] = value
        self.save()

    def has_prior_context(self) -> bool:
        return bool(self._data["facts"] or self._data["preferences"]
                    or self._data["identity"])

    @property
    def session_count(self) -> int:
        return self._data.get("session_count", 0)


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

    # -- topic key (FM-95 fix) -----------------------------------------------

    def _topic_key(self, text: str) -> str:
        """FM-95 fix: semantic intent fingerprint replaces raw word extraction.

        Old behavior: extracted up to 4 stopword-stripped words from the
        raw sentence, producing keys like "am_asking_conspiracy._criminal"
        that never cluster related queries.

        New behavior: extracts semantic fingerprint from three components:
          1. Intent bucket  (question / command / reflection / emotional / statement)
          2. Domain words   (nouns and verbs after stopword + punctuation removal)
          3. Length tier    (short / medium / long) as clustering aid

        Recency window still clusters paraphrased follow-ups (FM-88).
        """
        import string
        text_l = text.lower().strip().rstrip(string.punctuation)
        words  = set(re.sub(r"[^a-z0-9 ]", " ", text_l).split()) - STOPWORDS

        # Intent bucket
        if re.search(r"help me|should i|what do you think|advice", text_l):
            intent = "reflect"
        elif text_l.endswith("?") or re.search(r"^(?:what|who|where|when|why|how|is|are|can|do|does)", text_l):
            intent = "question"
        elif re.search(r"^(?:explain|tell|show|list|give|define|describe)", text_l):
            intent = "command"
        elif any(re.search(p, text_l) for p in EMOTION_LOW_PHRASES + EMOTION_MEDIUM_PHRASES):
            intent = "emotional"
        else:
            intent = "statement"

        # Domain words: keep only alpha tokens 4+ chars (removes fragments)
        domain_words = sorted([w for w in words if len(w) >= 4])[:3]

        # Length tier
        word_count = len(text_l.split())
        tier = "s" if word_count <= 5 else "m" if word_count <= 15 else "l"

        key = f"{intent}_{tier}_{'_'.join(domain_words)}" if domain_words else f"{intent}_{tier}"

        # FM-88 recency window: cluster paraphrased follow-ups
        for prev_key, prev_words in self._recent_turns:
            if len(words & prev_words) >= 2:
                return prev_key

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

def _parse_persona(instruction: str) -> Dict:
    """FM-112: parse persona instruction into structured object.
    Extracts: role name, target user, mission description.
    """
    instr_l = instruction.lower()
    role = "assistant"
    m = re.search(r"you are ([^,.]+)", instr_l)
    if m:
        role = m.group(1).strip()[:40]
    target = ""
    m2 = re.search(r"(?:mentor of|help|guide) ([A-Za-z0-9 ]+?)(?:[.,]|$)", instr_l)
    if m2:
        target = m2.group(1).strip()[:30]
    mission = ""
    m3 = re.search(r"mission(?:\s+is)?\s+(?:to\s+)?(.{0,100})", instr_l)
    if m3:
        mission = m3.group(1).strip()[:100]
    return {"role": role, "target": target, "mission": mission, "constraints": []}


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
        self.emotion_clf   = EmotionIntensityClassifier()   # FM-101
        self.frustration   = FrustrationTracker()           # FM-98
        self.register_clf  = ConversationalRegister()       # FM-100
        self.social        = SocialStateTracker()           # FM-102/103/104/106/108
        self.synthesizer   = SessionSynthesizer(self.long_term)  # FM-105/107/94
        self.inferencer    = CalibratedInferencer()             # FM-105
        self.profile       = PersistentProfile()               # FM-113/115

        self._session_id:        str  = ""
        self._namespace_cap:     int  = namespace_cap
        self._active_namespaces: set  = set()
        self._turn_count:        int  = 0
        # FM-119 (v0.17): canonical identity names for this session.
        # Populated by add_belief() when a persona instruction is loaded.
        # Stores full persona target phrases (e.g. "cadet q0") for phrase-level
        # replacement — word-level replacement leaves fragments ("Does you Q0").
        self._persona_names:     List[str] = []
        self._persona_target:    str       = ""  # full target phrase

    # -- session -------------------------------------------------------------

    def new_session(self, session_id: str = None) -> str:
        self._session_id = session_id or str(uuid.uuid4())[:8]
        self.autonomy.new_session()
        self.interaction.new_session()
        self.check_budget.reset()
        self.fast_path.evict_expired()
        self.frustration.reset()
        self.social.reset()
        self.synthesizer.reset_session()
        self._turn_count = 0

        # FM-116 fix (v0.14): re-read profile from disk now.
        # The profile was loaded at __init__ time, but if save_session() was
        # called by a prior run (different process), the in-memory _data may
        # be stale. Re-loading here guarantees we always see the latest disk state.
        self.profile._data = self.profile._load()

        # Cross-session injection: load from PersistentProfile (FM-113/115)
        # Also pull any in-memory long_term facts as fallback
        prior_facts = getattr(self.long_term, "_session_facts", [])
        disk_facts  = [f["text"] for f in self.profile._data.get("facts", [])
                       if f.get("confidence", 0) >= self.profile.RETIRE_THRESHOLD]

        # Merge disk + memory facts, prefer disk (more reliable)
        all_prior = list(dict.fromkeys(disk_facts + prior_facts))
        if all_prior:
            self.synthesizer._facts = [
                f"[from prior session, tentative] {f}"
                for f in all_prior
                if not f.startswith("[from prior session")
            ]

        return self._session_id

    # -- belief management ---------------------------------------------------

    def add_belief(self, content: str = "", trait: str = "", value: str = "",
                   context: str = "general", exceptions: list = None,
                   domain: Domain = Domain.PREFERENCE, ns: str = "default",
                   alpha: float = 2.0, beta: float = 1.0,
                   source_text: str = "", immutable: bool = False) -> Belief:
        self._register_namespace(ns)

        # FM-109/FM-112: detect persona/role instructions and route to synthesizer
        # FM-112: store structured persona object, not just role label
        full_content = content or (f"{trait}={value}" if trait and value else "")
        if is_persona_instruction(full_content):
            # Extract structured fields from persona instruction
            persona = _parse_persona(full_content)
            self.synthesizer._facts.append(f"Session role: {persona['role']}")
            if persona['mission']:
                self.synthesizer._facts.append(f"Session mission: {persona['mission']}")
            if persona['target']:
                self.synthesizer._facts.append(f"Session target user: {persona['target']}")
            # FM-119 (v0.17): register persona target name for identity canonicalization.
            # Store the full target phrase for phrase-level replacement, plus
            # individual significant words as fallback.
            if persona['target']:
                self._persona_target = persona['target'].lower().strip()
                for part in persona['target'].lower().split():
                    if len(part) >= 3 and part not in self._persona_names:
                        self._persona_names.append(part)
            # FM-111: implicit facts from persona
            self.synthesizer._turn_buffer.append(full_content)
            self.synthesizer._last_update = 0  # force re-synthesis
            if hasattr(self.long_term, "_session_facts"):
                self.long_term._session_facts = list(self.synthesizer._facts)
            # Still store as belief for audit, but mark as IDENTITY domain
            domain = Domain.IDENTITY

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

    def _canonicalize_query(self, query: str) -> str:
        """FM-119 (v0.17): normalize third-person persona references to first-person.

        'Cadet Q0' is an alias for 'you'. Replace the full phrase first
        (phrase-level), then fall back to individual significant words.
        This prevents "Does Cadet Q0 like prawns?" leaving "Does you Q0..."
        """
        if not self._persona_target and not self._persona_names:
            return query
        q = query

        # Phase 1: full phrase replacement (e.g. "cadet q0" → "you")
        if self._persona_target:
            pattern = re.compile(re.escape(self._persona_target), re.IGNORECASE)
            q = pattern.sub("you", q)

        # Phase 2: individual word fallback for any remaining fragments
        for name in self._persona_names:
            pattern = re.compile(r'\b' + re.escape(name) + r'\b', re.IGNORECASE)
            q = pattern.sub("you", q)

        return q

    # -- FM-120: preference correction detection and hard-write ----------------

    # Preference correction patterns: user explicitly corrects or asserts a preference
    PREF_CORRECTION_PATTERNS = [
        # Prawns / food — explicit correction forms
        (r"\bno[,.]?\s+i\b.{0,20}\b(?:don'?t|dislike|hate)\b.{0,20}\bprawns\b",
         "prawns", "dislike"),
        (r"\bactually[,.]?\s+i\b.{0,20}\b(?:don'?t|dislike|hate)\b.{0,20}\bprawns\b",
         "prawns", "dislike"),
        (r"\bi\s+(?:don'?t like|dislike|hate)\s+prawns\b",
         "prawns", "dislike"),
        (r"\bi\s+(?:like|love|enjoy)\s+prawns\b",
         "prawns", "like"),
        (r"\bno[,.]?\s+i\b.{0,20}\b(?:like|love|enjoy)\b.{0,20}\bprawns\b",
         "prawns", "like"),
    ]

    def _detect_preference_correction(self, text: str
                                       ) -> Optional[Tuple[str, str]]:
        """FM-120 (v0.18): detect explicit preference statements.

        Returns (topic, value) if a clear preference correction is found,
        else None. Only fires on declarative statements (not questions).
        """
        if not SessionSynthesizer._is_declarative(text):
            return None
        text_l = text.lower().strip()
        for pattern, topic, value in self.PREF_CORRECTION_PATTERNS:
            if re.search(pattern, text_l):
                return (topic, value)
        return None

    def _hard_write_preference(self, topic: str, value: str,
                                namespace: str = "default") -> None:
        """FM-120 (v0.18): write a preference correction as an authoritative
        graph belief, superseding all prior beliefs on the same topic.

        This removes the LLM from the job of tracking preference state.
        The graph holds the truth; every subsequent turn's memory context
        will carry the corrected preference regardless of history[] drift.
        """
        # Mark all existing same-topic beliefs as contradicted
        for b in self.graph.all_beliefs():
            if b.domain == Domain.PREFERENCE:
                b_label = (b.trait or b.content or "").lower()
                if topic.lower() in b_label:
                    b.last_contradicted = time.time()
                    b.beta_ = max(0.5, b.beta_ + 2.0)  # confidence collapse

        # Write the correction as a new high-confidence PREFERENCE belief
        correction_label = f"User {value}s {topic}"
        self.add_belief(
            content=correction_label,
            trait=f"{topic}_preference",
            value=value,
            domain=Domain.PREFERENCE,
            ns=namespace,
            alpha=5.0,   # 0.85 confidence: alpha/(alpha+beta) = 5/5.9
            beta=0.9,
            source_text=f"explicit correction at turn {self._turn_count}",
        )

        # Also update synthesizer facts to reflect correction
        facts = self.synthesizer._facts
        # Remove any prior opposite fact about this topic
        opposite = "likes" if value == "dislike" else "dislikes"
        self.synthesizer._facts = [
            f for f in facts
            if not (topic.lower() in f.lower() and opposite in f.lower())
        ]
        # Add the corrected fact
        corrected_fact = f"User {value}s {topic}"
        if not any(corrected_fact.lower() in f.lower()
                   for f in self.synthesizer._facts):
            self.synthesizer._facts.append(corrected_fact)
        # Mirror to long_term
        if hasattr(self.long_term, "_session_facts"):
            self.long_term._session_facts = [
                f for f in self.long_term._session_facts
                if not (topic.lower() in f.lower() and opposite in f.lower())
            ]
            if corrected_fact not in self.long_term._session_facts:
                self.long_term._session_facts.append(corrected_fact)

    # -- main ask interface --------------------------------------------------

    def ask(self, query: str, response_text: str = "",
            namespace: str = "default") -> Tuple[Dict, Dict]:
        self._turn_count += 1
        cache_key = f"{namespace}:{query[:50]}"

        # FM-119 (v0.17): normalize persona name references before any processing
        canonical_query = self._canonicalize_query(query)

        self.episodic.write("user", query, self._session_id, namespace)

        # FM-120 (v0.18): detect explicit preference corrections and hard-write
        # to graph immediately. This anchors the correction in the retrieval
        # system so all subsequent turns serve the corrected state from the
        # graph, not from LLM history[] which drifts over long sessions.
        pref_correction = self._detect_preference_correction(canonical_query)
        if pref_correction:
            topic, value = pref_correction
            self._hard_write_preference(topic, value, namespace)

        # FM-94/FM-110: for identity/belief queries, retrieve all beliefs across namespaces
        if is_identity_query(canonical_query) or is_belief_query(canonical_query):
            beliefs = self.graph.all_beliefs()[:15]  # no namespace filter
            id_beliefs = self.identity.get(namespace)
            for ib in id_beliefs:
                if ib not in beliefs:
                    beliefs.append(ib)
        else:
            beliefs = self.graph.search(canonical_query, namespace=namespace, top_k=8)
        constraints = self.graph.search(canonical_query, domain=Domain.CONSTRAINT, top_k=5)
        immune      = [b for b in self.graph.all_beliefs(namespace)
                       if b.is_truth_immune and b not in constraints]
        constraints.extend(immune)
        causal      = self.graph.get_causal()

        intent        = self.intent_clf.classify(canonical_query)
        uai           = self.autonomy.session_uai()

        # FM-101: emotion tier
        emotion_tier  = self.emotion_clf.classify(canonical_query)
        # FM-98: frustration check
        frustrated    = self.frustration.check(query)   # raw query for frustration
        self.frustration.tick()
        # FM-100: conversational register
        is_casual     = self.register_clf.is_casual(canonical_query)
        # FM-104: social state update
        topic_key      = self.interaction._topic_key(canonical_query)
        self.social.update(canonical_query, topic_key)
        # FM-107: session synthesis — ingest raw query (preserve actual words)
        self.synthesizer.ingest(query, role="user")
        self.synthesizer.maybe_update(self._turn_count)
        # FM-94/FM-109: identity query detection — use canonical form
        identity_query = is_identity_query(canonical_query)
        # FM-110: belief query detection — use canonical form
        belief_query   = is_belief_query(canonical_query)
        # FM-105: calibrated inference — force synthesize before checking
        self.synthesizer.maybe_update(self._turn_count)
        infer_note     = self.inferencer.infer_from_context(
            canonical_query, self.synthesizer.user_model(),
            [self._belief_summary(b) for b in self.graph.all_beliefs()])

        cb_ok = self.check_budget.available()
        should_intervene, intervene_reason = self.intervention.should_intervene(
            canonical_query, uai, cb_ok)
        if should_intervene:
            self.check_budget.use()

        prior_history = len(self.episodic) > 5
        resistance    = self.interaction.record_resistance(query)

        if resistance:
            reflect, reflect_reason = False, "resistance_suppressed"
        else:
            reflect, reflect_reason = self.interaction.should_reflect(
                canonical_query, prior_history)

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
            "emotion_tier":   emotion_tier,
            "frustrated":     frustrated,
            "is_casual":      is_casual,
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
            "emotion_tier":     emotion_tier,
            "emotion_note":     self.emotion_clf.system_note(emotion_tier),
            "frustrated":       frustrated,
            "frustration_note": self.frustration.system_note(),
            "register_casual":  is_casual,
            "register_note":    self.register_clf.system_note(is_casual),
            "social_notes":     self.social.system_notes(),
            "social_state":     self.social.state_summary(),
            "user_model":       self.synthesizer.user_model(),
            "identity_query":   identity_query,
            "belief_query":     belief_query,
            "infer_note":       infer_note or "",
        }
        return context_packet, validation

    # -- session persistence (FM-113/115) ------------------------------------

    def save_session(self) -> None:
        """Persist current session facts to disk. Call at session end.

        FM-116 fix (v0.14): force a final synthesis pass before collecting
        facts. Without this, facts disclosed in the last 1-4 turns of a
        session (before maybe_update() fires again) would be missed.
        _capture_immediate() handles the most common cases turn-by-turn,
        but the forced synthesize() here catches everything else.
        """
        # Force final synthesis of any buffered turns
        self.synthesizer._synthesize()

        session_facts = list(self.synthesizer._facts)
        # Also add any long_term facts
        lt_facts = getattr(self.long_term, "_session_facts", [])
        for f in lt_facts:
            if f not in session_facts:
                session_facts.append(f)

        # Extract preference signals from belief graph
        preferences = []
        for b in self.graph.all_beliefs():
            if b.domain.value == "preference" and b.evidence_count >= 1:
                key = b.trait or b.content[:30]
                val = b.value or b.content[:60]
                if key and val:
                    preferences.append({"key": key, "value": val,
                                        "confidence": b.confidence})

        self.profile.update_from_session(session_facts, preferences)

        # Extract identity signals
        id_beliefs = []
        for b in self.graph.all_beliefs():
            if b.domain.value == "identity":
                self.profile.record_identity(
                    b.trait or "identity", b.value or b.content[:60])

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
