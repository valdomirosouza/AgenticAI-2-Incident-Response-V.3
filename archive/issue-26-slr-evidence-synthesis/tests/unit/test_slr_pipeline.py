"""Unit tests for the PRISMA 2020 SLR pipeline — RULE-C01, RULE-C02.

Supports: all RQs — validates that the PRISMA funnel correctly gates papers
through identification → screening → eligibility → inclusion, enforces
RULE-004 QA threshold, and produces a consistent PRISMAResult.

Fixture data derived exclusively from real corpus papers P01–P19 (RULE-C02).
"""

from __future__ import annotations

import pytest

from src.research.quality_assessment import CORPUS_QA_SCORES, QAScore, PaperQA, score_paper
from src.research.slr_pipeline import (
    PAPER_REGISTRY,
    ExclusionCriteria,
    InclusionCriteria,
    PaperRecord,
    PRISMAResult,
    _passes_full_text,
    _passes_title_abstract,
    run_prisma_flow,
)


# ── Fixtures (real corpus data — RULE-C02) ────────────────────────────────────

@pytest.fixture()
def record_p02() -> PaperRecord:
    """P02: Ghosh et al., ICSE 2022 — highest QA score in corpus (4.0)."""
    return next(r for r in PAPER_REGISTRY if r.paper_id == "P02")


@pytest.fixture()
def record_p10() -> PaperRecord:
    """P10: Ahmed et al., IEEE ToN 2021 — boundary QA case (total=1.5)."""
    return next(r for r in PAPER_REGISTRY if r.paper_id == "P10")


@pytest.fixture()
def record_off_topic() -> PaperRecord:
    """Synthetic record that fails full-text eligibility (no RQs addressed)."""
    return PaperRecord(
        paper_id="P99",
        title="Off-topic paper",
        year=2023,
        venue="ICSE",
        sjr_quartile="Q1",
        citations=10,
        rqs_addressed=frozenset(),
    )


@pytest.fixture()
def record_low_venue() -> PaperRecord:
    """Record with Q3 venue — fails title/abstract screening (RULE-R03)."""
    return PaperRecord(
        paper_id="P98",
        title="Low-venue paper",
        year=2022,
        venue="Some Workshop",
        sjr_quartile="Q3",
        citations=5,
        rqs_addressed=frozenset({"RQ1"}),
    )


@pytest.fixture()
def record_no_citations() -> PaperRecord:
    """Record with zero citations — fails title/abstract screening (RULE-R03)."""
    return PaperRecord(
        paper_id="P97",
        title="Zero citations paper",
        year=2023,
        venue="ICSE",
        sjr_quartile="Q1",
        citations=0,
        rqs_addressed=frozenset({"RQ2"}),
    )


# ── PRISMA stage: title/abstract screening ────────────────────────────────────

class TestTitleAbstractScreening:
    def test_q1_paper_passes(self, record_p02: PaperRecord) -> None:
        assert _passes_title_abstract(record_p02) is True

    def test_q3_venue_excluded(self, record_low_venue: PaperRecord) -> None:
        assert _passes_title_abstract(record_low_venue) is False

    def test_zero_citations_excluded(self, record_no_citations: PaperRecord) -> None:
        assert _passes_title_abstract(record_no_citations) is False

    def test_q2_venue_passes(self) -> None:
        """P07 Liu ICSOC 2022 is SJR Q2 — must pass screening (RULE-R03)."""
        record_p07 = next(r for r in PAPER_REGISTRY if r.paper_id == "P07")
        assert _passes_title_abstract(record_p07) is True

    def test_pre_2018_excluded(self) -> None:
        old_record = PaperRecord(
            paper_id="P00", title="Very old paper", year=2015, venue="ICSE",
            sjr_quartile="Q1", citations=100, rqs_addressed=frozenset({"RQ1"}),
        )
        assert _passes_title_abstract(old_record) is False


# ── PRISMA stage: full-text eligibility ───────────────────────────────────────

class TestFullTextEligibility:
    def test_rq_addressed_passes(self, record_p02: PaperRecord) -> None:
        assert _passes_full_text(record_p02) is True

    def test_no_rq_excluded(self, record_off_topic: PaperRecord) -> None:
        assert _passes_full_text(record_off_topic) is False

    def test_single_rq_passes(self) -> None:
        """P17 addresses only RQ3 — must pass full-text gate."""
        record_p17 = next(r for r in PAPER_REGISTRY if r.paper_id == "P17")
        assert _passes_full_text(record_p17) is True


# ── run_prisma_flow: full funnel ──────────────────────────────────────────────

class TestRunPrismaFlow:
    @pytest.fixture()
    def result(self) -> PRISMAResult:
        return run_prisma_flow()

    def test_identified_count_equals_registry_size(self, result: PRISMAResult) -> None:
        assert result.identified == len(PAPER_REGISTRY)

    def test_all_p01_to_p19_included(self, result: PRISMAResult) -> None:
        for pid in [f"P{i:02d}" for i in range(1, 20)]:
            assert pid in result.included_ids, f"{pid} missing from included set"

    def test_included_count_is_19(self, result: PRISMAResult) -> None:
        assert result.included == 19

    def test_no_duplicates_in_default_run(self, result: PRISMAResult) -> None:
        assert result.excluded_duplicates == []

    def test_exclusion_rate_below_1(self, result: PRISMAResult) -> None:
        assert 0.0 <= result.exclusion_rate < 1.0

    def test_quantitative_papers_non_empty(self, result: PRISMAResult) -> None:
        assert len(result.quantitative_papers) > 0

    def test_quantitative_papers_all_meet_threshold(self, result: PRISMAResult) -> None:
        for paper in result.quantitative_papers:
            assert paper.total >= 1.5, (
                f"{paper.paper_id} in quantitative tier but total={paper.total}"
            )

    def test_theoretical_papers_all_below_threshold(self, result: PRISMAResult) -> None:
        for paper in result.theoretical_papers:
            assert paper.total < 1.5, (
                f"{paper.paper_id} in theoretical tier but total={paper.total}"
            )

    def test_p04_in_quantitative_tier(self, result: PRISMAResult) -> None:
        """P04 She ICSE-SEIP 2021 has QA total=4.0 — must be quantitative."""
        quant_ids = {p.paper_id for p in result.quantitative_papers}
        assert "P04" in quant_ids

    def test_duplicate_removal_works(self) -> None:
        result = run_prisma_flow(duplicate_ids=["P01", "P02"])
        assert result.after_dedup == len(PAPER_REGISTRY) - 2
        assert "P01" in result.excluded_duplicates
        assert "P02" in result.excluded_duplicates
        assert "P01" not in result.included_ids
        assert "P02" not in result.included_ids

    def test_off_topic_record_excluded(self) -> None:
        off_topic = PaperRecord(
            paper_id="P99", title="Unrelated paper", year=2023, venue="ICSE",
            sjr_quartile="Q1", citations=10, rqs_addressed=frozenset(),
        )
        result = run_prisma_flow(records=[off_topic])
        assert result.included == 0
        assert "P99" in result.excluded_full_text

    def test_low_qa_record_excluded_from_quantitative(self) -> None:
        """A paper passing PRISMA but with QA total < 1.5 lands in theoretical tier."""
        low_qa_record = PaperRecord(
            paper_id="P20", title="Low QA paper", year=2022, venue="ICSE",
            sjr_quartile="Q1", citations=5, rqs_addressed=frozenset({"RQ1"}),
        )
        low_qa = score_paper(
            "P20", "Low QA paper",
            qa1=QAScore.NO, qa2=QAScore.NO, qa3=QAScore.YES, qa4=QAScore.NO,
            notes="QA total=1.0 — theoretical only",
        )
        result = run_prisma_flow(
            records=[low_qa_record],
            qa_scores=[low_qa],
        )
        assert low_qa.total < 1.5
        quant_ids = {p.paper_id for p in result.quantitative_papers}
        assert "P20" not in quant_ids


# ── PRISMAResult properties ───────────────────────────────────────────────────

class TestPRISMAResult:
    def test_exclusion_rate_zero_when_all_pass(self) -> None:
        r = PRISMAResult(identified=10, included=10)
        assert r.exclusion_rate == 0.0

    def test_exclusion_rate_correct(self) -> None:
        r = PRISMAResult(identified=100, included=19)
        assert r.exclusion_rate == pytest.approx(0.81, abs=0.01)

    def test_exclusion_rate_zero_when_identified_zero(self) -> None:
        r = PRISMAResult(identified=0, included=0)
        assert r.exclusion_rate == 0.0


# ── InclusionCriteria / ExclusionCriteria enum completeness ───────────────────

class TestCriteriaEnums:
    def test_inclusion_criteria_has_four_items(self) -> None:
        assert len(list(InclusionCriteria)) == 4

    def test_exclusion_criteria_has_seven_items(self) -> None:
        assert len(list(ExclusionCriteria)) == 7

    def test_ic_coverage_period_value(self) -> None:
        assert InclusionCriteria.COVERAGE_PERIOD.value == "IC1"

    def test_ec_low_qa_score_value(self) -> None:
        assert ExclusionCriteria.LOW_QA_SCORE.value == "EC7"


# ── RULE-R03: venue ranking enforcement ──────────────────────────────────────

class TestVenueRankingRule:
    """RULE-R03: SJR Q1 or Q2 required; Q3/Q4 must be excluded."""

    @pytest.mark.parametrize("quartile", ["Q1", "Q2"])
    def test_accepted_quartiles_pass(self, quartile: str) -> None:
        r = PaperRecord(
            paper_id="Px", title="Test", year=2022, venue="Venue",
            sjr_quartile=quartile, citations=5, rqs_addressed=frozenset({"RQ1"}),
        )
        assert _passes_title_abstract(r) is True

    @pytest.mark.parametrize("quartile", ["Q3", "Q4", "N/A"])
    def test_rejected_quartiles_fail(self, quartile: str) -> None:
        r = PaperRecord(
            paper_id="Px", title="Test", year=2022, venue="Venue",
            sjr_quartile=quartile, citations=5, rqs_addressed=frozenset({"RQ1"}),
        )
        assert _passes_title_abstract(r) is False
