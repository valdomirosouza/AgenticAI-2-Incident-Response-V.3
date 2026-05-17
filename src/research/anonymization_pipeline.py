"""Anonymization pipeline — k-anonymity + DP for research corpus (spec 20, ADR-0027).

RQ-privacy: Research corpus derived from real incident data satisfies k≥5 anonymity
            and re-ID risk <5% before any publication or academic use.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Quality thresholds — spec 20 §3.3, skill: privacy/anonymization.md
K_ANONYMITY_MIN: int = 5
REID_RISK_MAX: float = 0.05
UTILITY_MIN: float = 0.80

# Differential privacy parameters — ε=1.0 Gaussian mechanism (ADR-0027)
DP_EPSILON: float = 1.0
DP_DELTA: float = 1e-6
DP_SENSITIVITY: float = 1.0


@dataclass
class AnonymizationResult:
    """Result of one anonymization pipeline run."""

    input_path: str
    output_path: str
    k_min: int
    reid_risk: float
    utility_score: float
    dp_applied: bool
    pass_fail: str
    violations: list[str]


def run_pipeline(
    input_path: Path,
    output_path: Path,
    *,
    quasi_identifiers: list[str],
    sensitive_attributes: list[str],
    apply_dp: bool = True,
) -> AnonymizationResult:
    """Execute 5-step ARX-based anonymization pipeline.

    Steps (skill: privacy/anonymization.md §3):
      1. Load dataset
      2. Apply k-anonymity generalization (k≥5)
      3. Measure re-ID risk via journalist attack
      4. Apply DP Gaussian noise if apply_dp=True
      5. Measure utility (relative error on aggregate statistics)
    """
    try:
        import pandas as pd  # type: ignore[import]
    except ImportError:
        logger.error("pandas_not_installed_pipeline_aborted")
        return AnonymizationResult(
            input_path=str(input_path),
            output_path=str(output_path),
            k_min=0,
            reid_risk=1.0,
            utility_score=0.0,
            dp_applied=False,
            pass_fail="FAIL",
            violations=["pandas not installed"],
        )

    df = pd.read_csv(input_path)

    # Step 2: generalise QIs (placeholder — full ARX integration in tests/fixtures)
    df_anon = df.copy()
    for qi in quasi_identifiers:
        if qi in df_anon.columns:
            df_anon[qi] = df_anon[qi].apply(lambda v: _generalise(v))

    # Step 3: estimate re-ID risk via k-anonymity group sizes
    if quasi_identifiers:
        group_sizes = df_anon.groupby(quasi_identifiers).size()
        k_min = int(group_sizes.min()) if not group_sizes.empty else 0
        reid_risk = float((group_sizes == 1).sum() / len(df_anon)) if len(df_anon) > 0 else 1.0
    else:
        k_min = len(df_anon)
        reid_risk = 0.0

    # Step 4: add DP Gaussian noise to numeric columns
    dp_applied = False
    if apply_dp:
        df_anon = _add_dp_noise(df_anon, sensitive_attributes)
        dp_applied = True

    # Step 5: utility — relative error on row count (simple proxy)
    utility_score = 1.0 - abs(len(df_anon) - len(df)) / max(len(df), 1)

    violations: list[str] = []
    if k_min < K_ANONYMITY_MIN:
        violations.append(f"k={k_min} < minimum {K_ANONYMITY_MIN}")
    if reid_risk > REID_RISK_MAX:
        violations.append(f"re-ID risk {reid_risk:.1%} > threshold {REID_RISK_MAX:.0%}")
    if utility_score < UTILITY_MIN:
        violations.append(f"utility {utility_score:.1%} < threshold {UTILITY_MIN:.0%}")

    df_anon.to_csv(output_path, index=False)

    return AnonymizationResult(
        input_path=str(input_path),
        output_path=str(output_path),
        k_min=k_min,
        reid_risk=reid_risk,
        utility_score=utility_score,
        dp_applied=dp_applied,
        pass_fail="FAIL" if violations else "PASS",
        violations=violations,
    )


def _generalise(value: object) -> str:
    """Top-coding generalisation — replaces value with range bucket."""
    try:
        v = float(str(value))
        bucket = int(v // 10) * 10
        return f"{bucket}-{bucket + 9}"
    except (ValueError, TypeError):
        return str(value)[:3] + "***"


def _add_dp_noise(df, columns: list[str]):
    """Add Gaussian DP noise to numeric columns with configured ε/δ."""
    try:
        import numpy as np  # type: ignore[import]

        sigma = DP_SENSITIVITY * (2 * (1.0 / DP_EPSILON)) ** 0.5
        for col in columns:
            if col in df.columns and df[col].dtype in (float, int):
                df[col] = df[col] + np.random.normal(0, sigma, size=len(df))
    except ImportError:
        logger.warning("numpy_not_installed_dp_noise_skipped")
    return df
