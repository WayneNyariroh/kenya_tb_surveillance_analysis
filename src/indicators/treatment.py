from __future__ import annotations

import logging
import re

import numpy as np
import pandas as pd

from .common import numeric, percentage

LOGGER = logging.getLogger(__name__)

# WHO treatment-outcome CSVs contain multiple cohorts. Rather than hard-code a
# single cohort that could change between releases, discover cohort variables
# and pair them with outcome variables sharing the same prefix.
OUTCOME_SUFFIXES = {
    "succ": "successful",
    "cur": "cured",
    "cmplt": "completed",
    "died": "died",
    "fail": "failed",
    "lost": "lost_to_follow_up",
    "neval": "not_evaluated",
}


def discover_treatment_cohorts(df: pd.DataFrame) -> list[str]:
    return sorted(c[:-4] for c in df.columns if c.endswith("_coh"))


def build_treatment_indicators(outcomes: pd.DataFrame) -> pd.DataFrame:
    if "year" not in outcomes.columns:
        raise ValueError("WHO treatment outcomes table has no year column.")

    rows = []
    for prefix in discover_treatment_cohorts(outcomes):
        cohort_col = f"{prefix}_coh"
        cohort = numeric(outcomes[cohort_col])

        found = {}
        for suffix, label in OUTCOME_SUFFIXES.items():
            col = f"{prefix}_{suffix}"
            if col in outcomes.columns:
                found[label] = col

        # Some releases provide successful treatment directly. If not, derive
        # it only when both cured and completed are available.
        direct_success = found.get("successful")
        derived_success = None
        if not direct_success and "cured" in found and "completed" in found:
            derived_success = (
                numeric(outcomes[found["cured"]])
                + numeric(outcomes[found["completed"]])
            )

        for idx, year in outcomes["year"].items():
            c = cohort.loc[idx]
            if pd.isna(c):
                continue

            row = {
                "year": int(year) if pd.notna(year) else pd.NA,
                "cohort": prefix,
                "cohort_size": c,
                "cohort_source_variable": cohort_col,
            }

            for label, col in found.items():
                if label == "successful":
                    continue
                value = numeric(outcomes[col]).loc[idx]
                row[f"{label}_num"] = value
                row[f"{label}_pct"] = (value / c * 100) if c > 0 and pd.notna(value) else np.nan
                row[f"{label}_source_variable"] = col

            if direct_success:
                success = numeric(outcomes[direct_success]).loc[idx]
                source = direct_success
            elif derived_success is not None:
                success = derived_success.loc[idx]
                source = f"{found['cured']} + {found['completed']}"
            else:
                success = np.nan
                source = None

            row["treatment_success_num"] = success
            row["treatment_success_pct"] = (
                success / c * 100 if c > 0 and pd.notna(success) else np.nan
            )
            row["treatment_success_source"] = source
            rows.append(row)

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values(["cohort", "year"]).reset_index(drop=True)
    return result
