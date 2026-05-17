"""Bias audit — SCER, CV_MTTD, RCRR, KL_drift metrics (ADR-0026, skill: ethics/bias-fairness).

RQ3: Does the Agentic Copilot exhibit measurable bias in severity classification or RCA accuracy
     across service groups?
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

logger = logging.getLogger(__name__)

# Thresholds — ADR-0026
SCER_OVERALL_THRESHOLD: float = 0.10
SCER_GROUP_THRESHOLD: float = 0.15
CV_MTTD_THRESHOLD: float = 0.30
RCRR_THRESHOLD: float = 0.60
KL_DRIFT_THRESHOLD: float = 0.10


@dataclass
class BiasAuditReport:
    """Quarterly bias audit report — schema matches skill/ethics/bias-fairness.md."""

    audit_date: str
    agent_versions: dict
    scer_overall: float
    scer_by_group: dict[str, float]
    cv_mttd: float
    rcrr: float
    kl_drift: float
    pass_fail: str
    remediation_required: list[str]


def compute_scer(
    predictions: Sequence[str],
    ground_truth: Sequence[str],
    groups: Sequence[str] | None = None,
) -> tuple[float, dict[str, float]]:
    """Severity Classification Error Rate — overall and per service group.

    SCER = (incorrect severity classifications) / (total classifications)
    """
    if not predictions:
        return 0.0, {}

    errors = [p != g for p, g in zip(predictions, ground_truth)]
    overall = sum(errors) / len(errors)

    by_group: dict[str, list[bool]] = {}
    if groups:
        for err, grp in zip(errors, groups):
            by_group.setdefault(grp, []).append(err)

    group_rates = {g: sum(v) / len(v) for g, v in by_group.items()}
    return overall, group_rates


def compute_cv_mttd(mttd_by_group: dict[str, list[float]]) -> float:
    """Coefficient of Variation of MTTD across service groups.

    CV_MTTD = std(group_mean_mttd) / mean(group_mean_mttd)
    """
    import statistics

    group_means = [statistics.mean(v) for v in mttd_by_group.values() if v]
    if len(group_means) < 2:
        return 0.0
    mean = statistics.mean(group_means)
    if mean == 0:
        return 0.0
    return statistics.stdev(group_means) / mean


def compute_rcrr(
    rca_predictions: Sequence[str],
    ground_truth: Sequence[str],
) -> float:
    """Root Cause Repetition Rate — fraction of incidents with same root cause prediction.

    RCRR = max(count(rc)) / total for top repeated root cause
    """
    if not rca_predictions:
        return 0.0
    from collections import Counter
    counts = Counter(rca_predictions)
    return counts.most_common(1)[0][1] / len(rca_predictions)


def compute_kl_drift(
    reference: Sequence[float],
    current: Sequence[float],
) -> float:
    """KL divergence between reference and current confidence distributions.

    Uses scipy.stats.entropy with smoothing to avoid log(0).
    """
    try:
        from scipy.stats import entropy  # type: ignore[import]
        import numpy as np  # type: ignore[import]

        eps = 1e-10
        ref = np.array(reference, dtype=float) + eps
        cur = np.array(current, dtype=float) + eps
        ref /= ref.sum()
        cur /= cur.sum()
        return float(entropy(ref, cur))
    except ImportError:
        logger.warning("scipy_not_installed_kl_drift_skipped")
        return 0.0


def run_audit(
    *,
    scer_overall: float,
    scer_by_group: dict[str, float],
    cv_mttd: float,
    rcrr: float,
    kl_drift: float,
    agent_versions: dict,
) -> BiasAuditReport:
    """Evaluate metrics against thresholds; produce pass/fail report."""
    remediation: list[str] = []

    if scer_overall > SCER_OVERALL_THRESHOLD:
        remediation.append(f"SCER overall {scer_overall:.1%} > threshold {SCER_OVERALL_THRESHOLD:.0%}")
    for grp, rate in scer_by_group.items():
        if rate > SCER_GROUP_THRESHOLD:
            remediation.append(f"SCER group '{grp}' {rate:.1%} > threshold {SCER_GROUP_THRESHOLD:.0%}")
    if cv_mttd > CV_MTTD_THRESHOLD:
        remediation.append(f"CV_MTTD {cv_mttd:.3f} > threshold {CV_MTTD_THRESHOLD}")
    if rcrr > RCRR_THRESHOLD:
        remediation.append(f"RCRR {rcrr:.1%} > threshold {RCRR_THRESHOLD:.0%}")
    if kl_drift > KL_DRIFT_THRESHOLD:
        remediation.append(f"KL_drift {kl_drift:.4f} > threshold {KL_DRIFT_THRESHOLD}")

    return BiasAuditReport(
        audit_date=datetime.now(tz=timezone.utc).date().isoformat(),
        agent_versions=agent_versions,
        scer_overall=scer_overall,
        scer_by_group=scer_by_group,
        cv_mttd=cv_mttd,
        rcrr=rcrr,
        kl_drift=kl_drift,
        pass_fail="FAIL" if remediation else "PASS",
        remediation_required=remediation,
    )
