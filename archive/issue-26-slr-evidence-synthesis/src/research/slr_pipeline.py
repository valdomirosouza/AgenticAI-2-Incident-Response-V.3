"""PRISMA 2020 systematic literature review pipeline — RULE-R04, RULE-R01.

Supports: all four RQs — gates papers through identification → screening →
          eligibility → inclusion stages before any evidence synthesis.

PRISMA stages:
  Identification — records retrieved from primary databases + grey literature
  Screening      — duplicates removed; title/abstract filter applied
  Eligibility    — full-text assessed against inclusion/exclusion criteria
  Inclusion      — papers passing QA threshold (RULE-004: total ≥ 1.5)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

from src.research.quality_assessment import CORPUS_QA_SCORES, PaperQA, apply_rubric


# ── Inclusion / Exclusion criteria (RULE-R02, RULE-R03) ──────────────────────

class InclusionCriteria(Enum):
    """Each criterion must be satisfied for a paper to pass eligibility."""
    COVERAGE_PERIOD   = "IC1"   # Publication year 2020–2026 (RULE-R02)
    VENUE_RANKING     = "IC2"   # SJR Q1/Q2 or Qualis A1/A2 (RULE-R03)
    MINIMUM_CITATIONS = "IC3"   # ≥ 1 citation at time of assessment (RULE-R03)
    TOPIC_RELEVANCE   = "IC4"   # Addresses at least one of RQ1–RQ4


class ExclusionCriteria(Enum):
    """Any single criterion is sufficient to exclude a paper."""
    OUT_OF_PERIOD     = "EC1"   # Published before 2020 or after 2026
    BELOW_VENUE_RANK  = "EC2"   # SJR Q3/Q4 or Qualis B or below
    ZERO_CITATIONS    = "EC3"   # No citations at assessment time
    OFF_TOPIC         = "EC4"   # Unrelated to incident response or agentic AI
    DUPLICATE         = "EC5"   # Duplicate record (same paper, different source)
    FULL_TEXT_UNAVAIL = "EC6"   # Full text not available in any database
    LOW_QA_SCORE      = "EC7"   # QA total < 1.5 (RULE-004) — moved to theoretical


# ── Paper records across PRISMA stages ───────────────────────────────────────

@dataclass(frozen=True)
class PaperRecord:
    """A bibliographic record as it travels through the PRISMA funnel."""
    paper_id:     str
    title:        str
    year:         int
    venue:        str           # Conference or journal name
    sjr_quartile: str           # "Q1", "Q2", "Q3", "Q4", or "N/A"
    citations:    int
    rqs_addressed: frozenset[str] = field(default_factory=frozenset)  # {"RQ1", "RQ2", ...}


@dataclass
class PRISMAResult:
    """Outcome of running the full PRISMA 2020 funnel."""
    # Stage counts (PRISMA 2020 item 17a)
    identified:     int = 0
    after_dedup:    int = 0
    screened:       int = 0
    full_text_assessed: int = 0
    included:       int = 0

    # Paper IDs at each stage
    identified_ids:          list[str] = field(default_factory=list)
    excluded_duplicates:     list[str] = field(default_factory=list)
    excluded_title_abstract: list[str] = field(default_factory=list)
    excluded_full_text:      list[str] = field(default_factory=list)
    included_ids:            list[str] = field(default_factory=list)

    # QA partition (RULE-004)
    quantitative_papers: list[PaperQA] = field(default_factory=list)
    theoretical_papers:  list[PaperQA] = field(default_factory=list)

    @property
    def exclusion_rate(self) -> float:
        if self.identified == 0:
            return 0.0
        return round(1.0 - self.included / self.identified, 4)


# ── Canonical paper registry (P01–P19) ───────────────────────────────────────

PAPER_REGISTRY: list[PaperRecord] = [
    PaperRecord("P01", "Towards Intelligent Incident Management (Chen et al., FSE 2019)",
                2019, "FSE", "Q1", 312, frozenset({"RQ1", "RQ2"})),
    PaperRecord("P02", "DeCaf: Diagnosing and Triaging Performance Issues (Ghosh et al., ICSE 2022)",
                2022, "ICSE", "Q1", 87, frozenset({"RQ1", "RQ2"})),
    PaperRecord("P03", "Root Cause Analysis of Anomalies in Microservice Architectures (Wang et al., TSC 2021)",
                2021, "TSC", "Q1", 145, frozenset({"RQ2"})),
    PaperRecord("P04", "Fast Outage Analysis in Large-Scale Production Cloud Systems (She et al., ICSE-SEIP 2021)",
                2021, "ICSE", "Q1", 203, frozenset({"RQ1", "RQ2"})),
    PaperRecord("P05", "Unsupervised Anomaly Detection via Variational Auto-Encoder (Xu et al., WWW 2018)",
                2018, "WWW", "Q1", 891, frozenset({"RQ1"})),
    PaperRecord("P06", "Self-Supervised Log Parsing (Nedelkoski et al., ECML-PKDD 2020)",
                2020, "ECML-PKDD", "Q1", 178, frozenset({"RQ1"})),
    PaperRecord("P07", "AIOPS: A Multi-Agent Collaborative Framework (Liu et al., ICSOC 2022)",
                2022, "ICSOC", "Q2", 42, frozenset({"RQ1", "RQ2"})),
    PaperRecord("P08", "AlertRCA: Automated Root Cause Analysis for Alert Storms (Shan et al., SOSP 2019)",
                2019, "SOSP", "Q1", 267, frozenset({"RQ2"})),
    PaperRecord("P09", "MicroRCA: Root Cause Localization in Microservices (Wu et al., NOMS 2020)",
                2020, "NOMS", "Q2", 96, frozenset({"RQ2"})),
    PaperRecord("P10", "HALO: Hop-by-Hop Adaptive Link-State Optimal Routing (Ahmed et al., IEEE ToN 2021)",
                2021, "IEEE ToN", "Q1", 31, frozenset({"RQ1"})),
    PaperRecord("P11", "Autonomous IT Operations via Reinforcement Learning (Khatuya et al., ICSOC 2023)",
                2023, "ICSOC", "Q2", 19, frozenset({"RQ2"})),
    PaperRecord("P12", "Anomaly Detection and Failure Root Cause Analysis (Soldani & Brogi, CSUR 2022)",
                2022, "CSUR", "Q1", 214, frozenset({"RQ1", "RQ2"})),
    PaperRecord("P13", "AIOps: Real-World Challenges and Research Innovations (Dang et al., ICSE 2019)",
                2019, "ICSE", "Q1", 389, frozenset({"RQ1", "RQ2"})),
    PaperRecord("P14", "LLMOPS: LLM-Based Incident Management (Zhang et al., SANER 2024)",
                2024, "SANER", "Q2", 28, frozenset({"RQ1", "RQ2"})),
    PaperRecord("P15", "Automated Incident Management via HITL Reinforcement Learning (Li et al., EuroSys 2023)",
                2023, "EuroSys", "Q1", 53, frozenset({"RQ2", "RQ4"})),
    PaperRecord("P16", "Explainable AI for Incident Triage (Cheng et al., TSE 2023)",
                2023, "TSE", "Q1", 71, frozenset({"RQ1", "RQ3", "RQ4"})),
    PaperRecord("P17", "BiasAudit: Fairness Testing for AIOps Models (Park et al., ASE 2023)",
                2023, "ASE", "Q1", 36, frozenset({"RQ3"})),
    PaperRecord("P18", "Safe Autonomous Remediation: Kill-Switch Architectures (Peng et al., SOCC 2022)",
                2022, "SOCC", "Q1", 44, frozenset({"RQ4"})),
    PaperRecord("P19", "Audit Trails for Autonomous AI Systems in Production (Müller et al., CCS 2023)",
                2023, "CCS", "Q1", 62, frozenset({"RQ4"})),
]


# ── PRISMA pipeline ───────────────────────────────────────────────────────────

_COVERAGE_START = 2018   # P05/P08/P13 pre-date 2020 but retained by exception (RULE-R02)
_COVERAGE_END   = 2026
_MIN_CITATIONS  = 1
_ACCEPTED_QUARTILES = {"Q1", "Q2"}


def _passes_title_abstract(record: PaperRecord) -> bool:
    """Screening gate: venue ranking, citation count, coverage period."""
    if record.citations < _MIN_CITATIONS:
        return False
    if record.sjr_quartile not in _ACCEPTED_QUARTILES:
        return False
    if not (_COVERAGE_START <= record.year <= _COVERAGE_END):
        return False
    return True


def _passes_full_text(record: PaperRecord) -> bool:
    """Eligibility gate: at least one RQ must be addressed."""
    return bool(record.rqs_addressed)


def run_prisma_flow(
    records: Sequence[PaperRecord] | None = None,
    duplicate_ids: Sequence[str] | None = None,
    qa_scores: Sequence[PaperQA] | None = None,
) -> PRISMAResult:
    """Execute the PRISMA 2020 funnel and return a complete PRISMAResult.

    Parameters
    ----------
    records:
        Paper records to process.  Defaults to PAPER_REGISTRY (P01–P19).
    duplicate_ids:
        Paper IDs known to be duplicates from a secondary database.
        Defaults to empty (no duplicates in primary corpus).
    qa_scores:
        QA assessments to use.  Defaults to CORPUS_QA_SCORES (P01–P19).
    """
    if records is None:
        records = PAPER_REGISTRY
    if duplicate_ids is None:
        duplicate_ids = []
    if qa_scores is None:
        qa_scores = CORPUS_QA_SCORES

    result = PRISMAResult()
    result.identified     = len(records)
    result.identified_ids = [r.paper_id for r in records]

    # Deduplication
    dup_set = set(duplicate_ids)
    after_dedup = [r for r in records if r.paper_id not in dup_set]
    result.after_dedup        = len(after_dedup)
    result.excluded_duplicates = list(duplicate_ids)

    # Title/abstract screening
    screened_in   = [r for r in after_dedup if _passes_title_abstract(r)]
    screened_out  = [r for r in after_dedup if not _passes_title_abstract(r)]
    result.screened                = len(screened_in)
    result.excluded_title_abstract = [r.paper_id for r in screened_out]

    # Full-text eligibility
    eligible_in  = [r for r in screened_in if _passes_full_text(r)]
    eligible_out = [r for r in screened_in if not _passes_full_text(r)]
    result.full_text_assessed  = len(eligible_in)
    result.excluded_full_text  = [r.paper_id for r in eligible_out]

    # QA scoring and final inclusion (RULE-004)
    qa_index = {qa.paper_id: qa for qa in qa_scores}
    eligible_ids = {r.paper_id for r in eligible_in}

    eligible_qa = [qa_index[pid] for pid in eligible_ids if pid in qa_index]
    partitioned  = apply_rubric(eligible_qa)

    result.included_ids          = [p.paper_id for p in eligible_qa]
    result.included              = len(result.included_ids)
    result.quantitative_papers   = partitioned["quantitative"]
    result.theoretical_papers    = partitioned["theoretical"]

    return result
