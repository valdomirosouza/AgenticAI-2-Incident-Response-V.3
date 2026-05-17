"""Unit tests for src/research/bias_audit.py — ADR-0026 (RQ3 research question).

RQ3: Does the Agentic Copilot exhibit measurable bias in severity classification
     or RCA accuracy across service groups?
"""

import pytest

from src.research.bias_audit import (
    SCER_OVERALL_THRESHOLD,
    CV_MTTD_THRESHOLD,
    RCRR_THRESHOLD,
    compute_cv_mttd,
    compute_rcrr,
    compute_scer,
    run_audit,
)


@pytest.mark.unit
class TestComputeScer:
    def test_perfect_classification(self) -> None:
        overall, by_group = compute_scer(["P1", "P2", "P3"], ["P1", "P2", "P3"])
        assert overall == 0.0

    def test_all_wrong(self) -> None:
        overall, _ = compute_scer(["P1", "P1", "P1"], ["P2", "P2", "P2"])
        assert overall == 1.0

    def test_half_wrong(self) -> None:
        overall, _ = compute_scer(["P1", "P2"], ["P1", "P1"])
        assert overall == pytest.approx(0.5)

    def test_group_rates_computed(self) -> None:
        preds = ["P1", "P2", "P1", "P2"]
        truth = ["P1", "P1", "P1", "P2"]
        groups = ["payment", "payment", "auth", "auth"]
        _, by_group = compute_scer(preds, truth, groups)
        assert "payment" in by_group
        assert by_group["auth"] == 0.0

    def test_corpus_p03_pattern(self) -> None:
        """Cascade incident — triage should classify P1 correctly for auth failures."""
        preds = ["P1", "P1", "P2"]
        truth = ["P1", "P1", "P1"]
        overall, _ = compute_scer(preds, truth)
        assert overall == pytest.approx(1 / 3)

    def test_empty_returns_zero(self) -> None:
        overall, by_group = compute_scer([], [])
        assert overall == 0.0
        assert by_group == {}


@pytest.mark.unit
class TestComputeCvMttd:
    def test_equal_mttd_across_groups_is_zero(self) -> None:
        mttd = {"payment": [120.0, 120.0], "auth": [120.0, 120.0]}
        assert compute_cv_mttd(mttd) == pytest.approx(0.0)

    def test_high_variance_across_groups(self) -> None:
        mttd = {"payment": [60.0], "auth": [600.0]}
        cv = compute_cv_mttd(mttd)
        assert cv > CV_MTTD_THRESHOLD

    def test_single_group_returns_zero(self) -> None:
        assert compute_cv_mttd({"payment": [100.0, 200.0]}) == 0.0

    def test_corpus_mttd_values(self) -> None:
        """Corpus values: P01=214s, P02=180s, P03=420s, P04=92s — high variance expected."""
        mttd = {
            "latency": [214.0],
            "saturation": [180.0],
            "cascade": [420.0],
            "availability": [92.0],
        }
        cv = compute_cv_mttd(mttd)
        assert cv > 0.0


@pytest.mark.unit
class TestComputeRcrr:
    def test_all_unique_root_causes_is_low(self) -> None:
        rca = ["oom", "network", "db_conn", "cpu_sat"]
        assert compute_rcrr(rca) == pytest.approx(0.25)

    def test_all_same_root_cause_is_one(self) -> None:
        assert compute_rcrr(["oom", "oom", "oom"]) == pytest.approx(1.0)

    def test_empty_returns_zero(self) -> None:
        assert compute_rcrr([]) == 0.0

    def test_corpus_root_causes(self) -> None:
        """Corpus: OOM, db_conn, replication_lag, connection_pool — balanced."""
        rca = ["connection_pool", "db_conn", "oom", "replication_lag", "db_conn"]
        rate = compute_rcrr(rca)
        assert rate == pytest.approx(0.4)
        assert rate <= RCRR_THRESHOLD


@pytest.mark.unit
class TestRunAudit:
    def test_all_pass_produces_pass_report(self) -> None:
        report = run_audit(
            scer_overall=0.05,
            scer_by_group={"payment": 0.04, "auth": 0.06},
            cv_mttd=0.20,
            rcrr=0.40,
            kl_drift=0.05,
            agent_versions={"triage": "0.5.0", "rca": "0.5.0"},
        )
        assert report.pass_fail == "PASS"
        assert report.remediation_required == []

    def test_scer_violation_produces_fail(self) -> None:
        report = run_audit(
            scer_overall=0.12,  # > 0.10 threshold
            scer_by_group={},
            cv_mttd=0.20,
            rcrr=0.40,
            kl_drift=0.05,
            agent_versions={},
        )
        assert report.pass_fail == "FAIL"
        assert any("SCER overall" in r for r in report.remediation_required)

    def test_kl_drift_violation_produces_fail(self) -> None:
        report = run_audit(
            scer_overall=0.05,
            scer_by_group={},
            cv_mttd=0.20,
            rcrr=0.40,
            kl_drift=0.15,  # > 0.10 threshold
            agent_versions={},
        )
        assert report.pass_fail == "FAIL"
        assert any("KL_drift" in r for r in report.remediation_required)
