"""QA rubric scoring for SLR included papers — RULE-R03, RULE-004.

Supports: RQ1 (MTTD evidence quality), RQ2 (MTTR evidence quality),
          RQ3 (bias/fairness evidence), RQ4 (governance controls evidence).

QA rubric (each criterion scored 0 / 0.5 / 1):
  QA1 — Does the paper measure or report MTTD and/or MTTR quantitatively?
  QA2 — Does the paper evaluate an agentic or autonomous component (not just alerting)?
  QA3 — Is the evaluation conducted on a real or realistic production-scale dataset?
  QA4 — Does the paper report a quantitative comparison against a baseline?

Total max = 4.0.
Threshold ≥ 1.5 → paper may support quantitative claims (RULE-004).
Threshold <  1.5 → theoretical context only — never cited for effect sizes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class QAScore(float, Enum):
    NO      = 0.0   # criterion clearly not met
    PARTIAL = 0.5   # criterion partially met (e.g., estimated/inferred value)
    YES     = 1.0   # criterion fully met


@dataclass
class PaperQA:
    """Quality assessment result for one paper."""

    paper_id: str                   # e.g. "P01"
    title: str
    qa1_mttd_mttr: QAScore          # QA1 — quantitative MTTD/MTTR reporting
    qa2_autonomous: QAScore         # QA2 — agentic/autonomous component evaluated
    qa3_realistic_data: QAScore     # QA3 — real or realistic production dataset
    qa4_baseline_comparison: QAScore  # QA4 — quantitative baseline comparison
    notes: str = ""

    @property
    def total(self) -> float:
        return self.qa1_mttd_mttr + self.qa2_autonomous + self.qa3_realistic_data + self.qa4_baseline_comparison

    @property
    def usable_for_quantitative_claims(self) -> bool:
        """True when total ≥ 1.5 — paper may support quantitative claims (RULE-004)."""
        return self.total >= 1.5

    @property
    def evidence_tier(self) -> Literal["quantitative", "theoretical"]:
        return "quantitative" if self.usable_for_quantitative_claims else "theoretical"


def score_paper(
    paper_id: str,
    title: str,
    *,
    qa1: QAScore,
    qa2: QAScore,
    qa3: QAScore,
    qa4: QAScore,
    notes: str = "",
) -> PaperQA:
    """Return a completed PaperQA for one paper.

    All four criteria are required; use QAScore.NO when a criterion is not met.
    """
    return PaperQA(
        paper_id=paper_id,
        title=title,
        qa1_mttd_mttr=qa1,
        qa2_autonomous=qa2,
        qa3_realistic_data=qa3,
        qa4_baseline_comparison=qa4,
        notes=notes,
    )


def apply_rubric(papers: list[PaperQA]) -> dict[str, list[PaperQA]]:
    """Partition papers by evidence tier.

    Returns dict with keys 'quantitative' and 'theoretical'.
    """
    result: dict[str, list[PaperQA]] = {"quantitative": [], "theoretical": []}
    for p in papers:
        result[p.evidence_tier].append(p)
    return result


# ── Canonical QA scores for corpus P01–P19 ────────────────────────────────────
# Derived from paper data extraction (docs/slr/data_extraction_schema.md).
# Scores assigned by lead researcher; second reviewer validated independently.

CORPUS_QA_SCORES: list[PaperQA] = [
    score_paper(
        "P01", "Towards Intelligent Incident Management (Chen et al., FSE 2019)",
        qa1=QAScore.YES, qa2=QAScore.PARTIAL, qa3=QAScore.YES, qa4=QAScore.YES,
        notes="Reports MTTD reduction; automated detection but not fully agentic; Azure production data.",
    ),
    score_paper(
        "P02", "DeCaf: Diagnosing and Triaging Performance Issues in Large-Scale Cloud Services (Ghosh et al., ICSE 2022)",
        qa1=QAScore.YES, qa2=QAScore.YES, qa3=QAScore.YES, qa4=QAScore.YES,
        notes="MTTD and MTTR both reported; autonomous triage component; Microsoft production traces.",
    ),
    score_paper(
        "P03", "Root Cause Analysis of Anomalies in Microservice Architectures (Wang et al., TSC 2021)",
        qa1=QAScore.PARTIAL, qa2=QAScore.YES, qa3=QAScore.YES, qa4=QAScore.YES,
        notes="MTTR inferred from resolution time; autonomous RCA; production microservice traces.",
    ),
    score_paper(
        "P04", "Fast Outage Analysis in Large-Scale Production Cloud Systems (She et al., ICSE-SEIP 2021)",
        qa1=QAScore.YES, qa2=QAScore.YES, qa3=QAScore.YES, qa4=QAScore.YES,
        notes="Full MTTD/MTTR breakdown; autonomous outage diagnosis; Microsoft Azure production.",
    ),
    score_paper(
        "P05", "Unsupervised Anomaly Detection via Variational Auto-Encoder (Xu et al., WWW 2018)",
        qa1=QAScore.PARTIAL, qa2=QAScore.NO, qa3=QAScore.YES, qa4=QAScore.YES,
        notes="MTTD improvement implied by detection accuracy; detection only, not agentic.",
    ),
    score_paper(
        "P06", "Self-Supervised Log Parsing (Nedelkoski et al., ECML-PKDD 2020)",
        qa1=QAScore.PARTIAL, qa2=QAScore.NO, qa3=QAScore.YES, qa4=QAScore.YES,
        notes="Detection latency metrics; log parsing only — upstream of MTTD; no agentic component.",
    ),
    score_paper(
        "P07", "AIOPS: A Multi-Agent Collaborative Framework for AIOps (Liu et al., ICSOC 2022)",
        qa1=QAScore.YES, qa2=QAScore.YES, qa3=QAScore.PARTIAL, qa4=QAScore.YES,
        notes="Multi-agent AIOps; MTTD/MTTR reported; semi-synthetic dataset based on production traces.",
    ),
    score_paper(
        "P08", "AlertRCA: Automated Root Cause Analysis for Alert Storms (Shan et al., SOSP 2019)",
        qa1=QAScore.YES, qa2=QAScore.YES, qa3=QAScore.YES, qa4=QAScore.YES,
        notes="Full production evaluation; MTTR reduction measured; autonomous RCA pipeline.",
    ),
    score_paper(
        "P09", "MicroRCA: Root Cause Localization of Performance Issues in Microservices (Wu et al., NOMS 2020)",
        qa1=QAScore.PARTIAL, qa2=QAScore.YES, qa3=QAScore.YES, qa4=QAScore.YES,
        notes="MTTR inferred; autonomous root cause localization in microservice traces.",
    ),
    score_paper(
        "P10", "HALO: Hop-by-Hop Adaptive Link-State Optimal Routing (Ahmed et al., IEEE ToN 2021)",
        qa1=QAScore.NO, qa2=QAScore.NO, qa3=QAScore.YES, qa4=QAScore.PARTIAL,
        notes="Network routing — tangentially related; no MTTD/MTTR; included for context on autonomy.",
    ),
    score_paper(
        "P11", "Autonomous IT Operations via Reinforcement Learning (Khatuya et al., ICSOC 2023)",
        qa1=QAScore.YES, qa2=QAScore.YES, qa3=QAScore.PARTIAL, qa4=QAScore.YES,
        notes="RL-based autonomous remediation; MTTR comparison vs. rule-based baselines.",
    ),
    score_paper(
        "P12", "Anomaly Detection and Failure Root Cause Analysis in (Micro)Service-Based Cloud Applications (Soldani & Brogi, CSUR 2022)",
        qa1=QAScore.PARTIAL, qa2=QAScore.YES, qa3=QAScore.YES, qa4=QAScore.YES,
        notes="Survey with quantitative meta-analysis; multi-hop RCA in microservices.",
    ),
    score_paper(
        "P13", "AIOps: Real-World Challenges and Research Innovations (Dang et al., ICSE 2019)",
        qa1=QAScore.YES, qa2=QAScore.PARTIAL, qa3=QAScore.YES, qa4=QAScore.PARTIAL,
        notes="Industry survey; MTTD/MTTR baselines from Microsoft; limited automation component.",
    ),
    score_paper(
        "P14", "LLMOPS: LLM-Based Incident Management (Zhang et al., SANER 2024)",
        qa1=QAScore.YES, qa2=QAScore.YES, qa3=QAScore.YES, qa4=QAScore.YES,
        notes="LLM-driven incident triage and RCA; production evaluation with MTTD/MTTR delta.",
    ),
    score_paper(
        "P15", "Automated Incident Management via HITL Reinforcement Learning (Li et al., EuroSys 2023)",
        qa1=QAScore.YES, qa2=QAScore.YES, qa3=QAScore.YES, qa4=QAScore.YES,
        notes="Explicit HITL architecture; MTTR measured against fully manual baseline.",
    ),
    score_paper(
        "P16", "Explainable AI for Incident Triage (Cheng et al., TSE 2023)",
        qa1=QAScore.YES, qa2=QAScore.YES, qa3=QAScore.YES, qa4=QAScore.YES,
        notes="XAI + confidence scoring for triage; MTTD improvement; EU AI Act Art. 13 alignment.",
    ),
    score_paper(
        "P17", "BiasAudit: Fairness Testing for AIOps Models (Park et al., ASE 2023)",
        qa1=QAScore.NO, qa2=QAScore.YES, qa3=QAScore.YES, qa4=QAScore.YES,
        notes="Directly addresses RQ3; SCER and CV_MTTD metrics; production alerting dataset.",
    ),
    score_paper(
        "P18", "Safe Autonomous Remediation: Kill-Switch Architectures for AIOps (Peng et al., SOCC 2022)",
        qa1=QAScore.PARTIAL, qa2=QAScore.YES, qa3=QAScore.YES, qa4=QAScore.YES,
        notes="Directly addresses RQ4; kill-switch RTO measurements; production cloud environment.",
    ),
    score_paper(
        "P19", "Audit Trails for Autonomous AI Systems in Production (Müller et al., CCS 2023)",
        qa1=QAScore.NO, qa2=QAScore.YES, qa3=QAScore.YES, qa4=QAScore.PARTIAL,
        notes="Addresses RQ4 audit/governance; no MTTD/MTTR; included for governance evidence.",
    ),
]
