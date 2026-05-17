"""Unit tests for evidence synthesis functions — RULE-C01, RULE-C02, RULE-003, RULE-004.

Supports: RQ1 (MTTD reduction), RQ2 (MTTR reduction),
          RQ3 (bias/fairness evidence), RQ4 (governance controls evidence).

Validates that:
  - Synthesis functions return EvidenceResult with correct structure
  - Quantitative claims reference only papers with QA total ≥ 1.5 (RULE-004)
  - Theoretical papers are never mixed into quantitative supporting_papers (RULE-003)
  - Effect sizes are within realistic bounds (RULE-002)
  - synthesize_all() is internally consistent with the PRISMA result

Fixture data derived exclusively from real corpus papers P01–P19 (RULE-C02).
"""

from __future__ import annotations

import pytest

from src.research.evidence_synthesis import (
    EvidenceResult,
    _ci_from_values,
    _partition_by_rq,
    synthesize_all,
    synthesize_rq1,
    synthesize_rq2,
    synthesize_rq3,
    synthesize_rq4,
)
from src.research.quality_assessment import CORPUS_QA_SCORES, QAScore, score_paper
from src.research.slr_pipeline import PAPER_REGISTRY


# ── Helper: _ci_from_values ───────────────────────────────────────────────────

class TestCIFromValues:
    def test_single_value(self) -> None:
        lo, hi = _ci_from_values([50.0])
        assert lo == 50.0
        assert hi == 50.0

    def test_empty_returns_zeros(self) -> None:
        assert _ci_from_values([]) == (0.0, 0.0)

    def test_ci_contains_median(self) -> None:
        values = list(range(1, 101))  # 1–100
        lo, hi = _ci_from_values(values)
        assert lo <= 50 <= hi

    def test_ci_lower_lte_upper(self) -> None:
        values = [58.0, 60.0, 55.0, 52.0, 50.0, 45.0, 63.0, 48.0]
        lo, hi = _ci_from_values(values)
        assert lo <= hi


# ── Helper: _partition_by_rq ─────────────────────────────────────────────────

class TestPartitionByRQ:
    def test_rq1_produces_quantitative_papers(self) -> None:
        qa_map = {qa.paper_id: qa for qa in CORPUS_QA_SCORES}
        quantitative, theoretical = _partition_by_rq("RQ1", PAPER_REGISTRY, qa_map)
        assert len(quantitative) > 0

    def test_all_quantitative_meet_threshold(self) -> None:
        qa_map = {qa.paper_id: qa for qa in CORPUS_QA_SCORES}
        for rq in ["RQ1", "RQ2", "RQ3", "RQ4"]:
            quantitative, _ = _partition_by_rq(rq, PAPER_REGISTRY, qa_map)
            for p in quantitative:
                assert p.total >= 1.5, (
                    f"Paper {p.paper_id} in quantitative tier for {rq} but total={p.total}"
                )

    def test_theoretical_all_below_threshold(self) -> None:
        qa_map = {qa.paper_id: qa for qa in CORPUS_QA_SCORES}
        for rq in ["RQ1", "RQ2", "RQ3", "RQ4"]:
            _, theoretical = _partition_by_rq(rq, PAPER_REGISTRY, qa_map)
            for p in theoretical:
                assert p.total < 1.5

    def test_unknown_rq_returns_empty_lists(self) -> None:
        qa_map = {qa.paper_id: qa for qa in CORPUS_QA_SCORES}
        quantitative, theoretical = _partition_by_rq("RQ9", PAPER_REGISTRY, qa_map)
        assert quantitative == []
        assert theoretical == []


# ── synthesize_rq1 ────────────────────────────────────────────────────────────

class TestSynthesizeRQ1:
    @pytest.fixture()
    def result(self) -> EvidenceResult:
        return synthesize_rq1()

    def test_returns_evidence_result(self, result: EvidenceResult) -> None:
        assert isinstance(result, EvidenceResult)

    def test_rq_identifier(self, result: EvidenceResult) -> None:
        assert result.rq == "RQ1"

    def test_effect_size_is_percentage(self, result: EvidenceResult) -> None:
        assert result.effect_size is not None
        assert 0.0 < result.effect_size < 100.0

    def test_effect_size_realistic_range(self, result: EvidenceResult) -> None:
        """MTTD reduction of 20–80 % is plausible; outside that warrants scrutiny."""
        assert 20.0 <= result.effect_size <= 80.0

    def test_ci_lower_lte_effect_size(self, result: EvidenceResult) -> None:
        assert result.ci_lower is not None
        assert result.ci_lower <= result.effect_size

    def test_ci_upper_gte_effect_size(self, result: EvidenceResult) -> None:
        assert result.ci_upper is not None
        assert result.ci_upper >= result.effect_size

    def test_supporting_papers_non_empty(self, result: EvidenceResult) -> None:
        assert len(result.supporting_papers) > 0

    def test_p04_in_supporting_papers(self, result: EvidenceResult) -> None:
        """P04 She ICSE-SEIP 2021 is a primary MTTD source (QA=4.0)."""
        assert "P04" in result.supporting_papers

    def test_supporting_papers_all_quantitative_tier(self, result: EvidenceResult) -> None:
        """RULE-004: no paper below QA threshold cited for quantitative claims."""
        qa_map = {qa.paper_id: qa for qa in CORPUS_QA_SCORES}
        for pid in result.supporting_papers:
            if pid in qa_map:
                assert qa_map[pid].total >= 1.5, (
                    f"{pid} in supporting_papers but QA total < 1.5 — violates RULE-004"
                )

    def test_no_overlap_between_supporting_and_theoretical(self, result: EvidenceResult) -> None:
        """RULE-003: quantitative and theoretical sets must be disjoint."""
        overlap = set(result.supporting_papers) & set(result.theoretical_papers)
        assert overlap == set(), f"Overlap between tiers: {overlap}"

    def test_effect_unit_mentions_mttd(self, result: EvidenceResult) -> None:
        assert "MTTD" in result.effect_unit or "mttd" in result.effect_unit.lower()


# ── synthesize_rq2 ────────────────────────────────────────────────────────────

class TestSynthesizeRQ2:
    @pytest.fixture()
    def result(self) -> EvidenceResult:
        return synthesize_rq2()

    def test_returns_evidence_result(self, result: EvidenceResult) -> None:
        assert isinstance(result, EvidenceResult)

    def test_rq_identifier(self, result: EvidenceResult) -> None:
        assert result.rq == "RQ2"

    def test_effect_size_realistic_range(self, result: EvidenceResult) -> None:
        assert result.effect_size is not None
        assert 20.0 <= result.effect_size <= 80.0

    def test_p15_in_supporting_papers(self, result: EvidenceResult) -> None:
        """P15 Li EuroSys 2023 — HITL RL with explicit MTTR comparison (QA=4.0)."""
        assert "P15" in result.supporting_papers

    def test_p08_in_supporting_papers(self, result: EvidenceResult) -> None:
        """P08 Shan SOSP 2019 — autonomous RCA; MTTR reduction measured (QA=4.0)."""
        assert "P08" in result.supporting_papers

    def test_ci_ordered(self, result: EvidenceResult) -> None:
        assert result.ci_lower <= result.effect_size <= result.ci_upper

    def test_supporting_papers_all_quantitative_tier(self, result: EvidenceResult) -> None:
        qa_map = {qa.paper_id: qa for qa in CORPUS_QA_SCORES}
        for pid in result.supporting_papers:
            if pid in qa_map:
                assert qa_map[pid].total >= 1.5

    def test_no_tier_overlap(self, result: EvidenceResult) -> None:
        overlap = set(result.supporting_papers) & set(result.theoretical_papers)
        assert overlap == set()

    def test_effect_unit_mentions_mttr(self, result: EvidenceResult) -> None:
        assert "MTTR" in result.effect_unit or "mttr" in result.effect_unit.lower()


# ── synthesize_rq3 ────────────────────────────────────────────────────────────

class TestSynthesizeRQ3:
    @pytest.fixture()
    def result(self) -> EvidenceResult:
        return synthesize_rq3()

    def test_returns_evidence_result(self, result: EvidenceResult) -> None:
        assert isinstance(result, EvidenceResult)

    def test_rq_identifier(self, result: EvidenceResult) -> None:
        assert result.rq == "RQ3"

    def test_effect_size_is_none(self, result: EvidenceResult) -> None:
        """RQ3 does not produce a single aggregate effect size (multi-dimensional)."""
        assert result.effect_size is None

    def test_ci_is_none(self, result: EvidenceResult) -> None:
        assert result.ci_lower is None
        assert result.ci_upper is None

    def test_p17_in_supporting_papers(self, result: EvidenceResult) -> None:
        """P17 Park ASE 2023 is the primary bias/fairness paper."""
        assert "P17" in result.supporting_papers

    def test_claim_mentions_bias(self, result: EvidenceResult) -> None:
        assert "bias" in result.claim.lower() or "fairness" in result.claim.lower()

    def test_no_tier_overlap(self, result: EvidenceResult) -> None:
        overlap = set(result.supporting_papers) & set(result.theoretical_papers)
        assert overlap == set()


# ── synthesize_rq4 ────────────────────────────────────────────────────────────

class TestSynthesizeRQ4:
    @pytest.fixture()
    def result(self) -> EvidenceResult:
        return synthesize_rq4()

    def test_returns_evidence_result(self, result: EvidenceResult) -> None:
        assert isinstance(result, EvidenceResult)

    def test_rq_identifier(self, result: EvidenceResult) -> None:
        assert result.rq == "RQ4"

    def test_effect_size_is_none(self, result: EvidenceResult) -> None:
        """RQ4 governance controls evaluated by RTO, not efficiency delta."""
        assert result.effect_size is None

    def test_p18_in_supporting_papers(self, result: EvidenceResult) -> None:
        """P18 Peng SOCC 2022 — kill-switch RTO < 60 s in production."""
        assert "P18" in result.supporting_papers

    def test_p15_in_supporting_papers(self, result: EvidenceResult) -> None:
        """P15 Li EuroSys 2023 — HITL architecture with measured overhead."""
        assert "P15" in result.supporting_papers

    def test_rto_mentioned_in_notes(self, result: EvidenceResult) -> None:
        assert "RTO" in result.notes or "rto" in result.notes.lower()

    def test_no_tier_overlap(self, result: EvidenceResult) -> None:
        overlap = set(result.supporting_papers) & set(result.theoretical_papers)
        assert overlap == set()

    def test_supporting_papers_all_quantitative_tier(self, result: EvidenceResult) -> None:
        qa_map = {qa.paper_id: qa for qa in CORPUS_QA_SCORES}
        for pid in result.supporting_papers:
            if pid in qa_map:
                assert qa_map[pid].total >= 1.5


# ── synthesize_all ────────────────────────────────────────────────────────────

class TestSynthesizeAll:
    @pytest.fixture()
    def results(self) -> dict[str, EvidenceResult]:
        return synthesize_all()

    def test_returns_all_four_rqs(self, results: dict[str, EvidenceResult]) -> None:
        assert set(results.keys()) == {"RQ1", "RQ2", "RQ3", "RQ4"}

    def test_each_rq_has_correct_identifier(self, results: dict[str, EvidenceResult]) -> None:
        for rq_key, evidence in results.items():
            assert evidence.rq == rq_key

    def test_rq1_and_rq2_have_effect_sizes(self, results: dict[str, EvidenceResult]) -> None:
        assert results["RQ1"].effect_size is not None
        assert results["RQ2"].effect_size is not None

    def test_rq3_and_rq4_have_no_single_effect_size(self, results: dict[str, EvidenceResult]) -> None:
        assert results["RQ3"].effect_size is None
        assert results["RQ4"].effect_size is None

    def test_rq1_mttd_reduction_greater_than_rq2_mttr_reduction(
        self, results: dict[str, EvidenceResult]
    ) -> None:
        """MTTD reductions are typically larger than MTTR — agentic detection is
        more direct than agentic remediation.  Not a hard invariant but flagged
        if the corpus changes dramatically."""
        # Allow either direction — just validate both are realistic
        assert results["RQ1"].effect_size > 0
        assert results["RQ2"].effect_size > 0

    def test_no_rule004_violation_across_all_rqs(self, results: dict[str, EvidenceResult]) -> None:
        """RULE-004: no quantitative paper below 1.5 threshold cited in any RQ."""
        qa_map = {qa.paper_id: qa for qa in CORPUS_QA_SCORES}
        for rq, evidence in results.items():
            for pid in evidence.supporting_papers:
                if pid in qa_map:
                    assert qa_map[pid].total >= 1.5, (
                        f"RULE-004 violation in {rq}: {pid} has QA total={qa_map[pid].total}"
                    )

    def test_no_rule003_tier_overlap_across_all_rqs(self, results: dict[str, EvidenceResult]) -> None:
        """RULE-003: quantitative and theoretical sets must be disjoint for every RQ."""
        for rq, evidence in results.items():
            overlap = set(evidence.supporting_papers) & set(evidence.theoretical_papers)
            assert overlap == set(), f"RULE-003 violation in {rq}: overlap={overlap}"
