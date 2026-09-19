from __future__ import annotations

import re

import pandas as pd


DIAGNOSTIC_TOKENS = (
    "lab", "xpert", "xpert_mtb", "mol", "molecular", "dst", "rif", "rr_",
    "bact", "conf", "smear", "culture", "lpa", "bdq",
)


def build_diagnostic_inventory(notifications: pd.DataFrame) -> pd.DataFrame:
    """
    Build a long inventory of diagnostic-related WHO variables present in the
    current notification extract.

    No rates are invented here because the correct denominator differs by
    indicator. The inventory lets the analysis layer see exactly which
    diagnostic variables are available before defining a formula.
    """
    if "year" not in notifications.columns:
        raise ValueError("WHO notification table has no year column.")

    cols = [
        c for c in notifications.columns
        if c != "year" and any(token in c.lower() for token in DIAGNOSTIC_TOKENS)
    ]
    if not cols:
        return pd.DataFrame(columns=["year", "source_variable", "value"])

    out = notifications[["year"] + cols].melt(
        id_vars="year",
        var_name="source_variable",
        value_name="value",
    )
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna(subset=["value"]).reset_index(drop=True)
    return out
