from __future__ import annotations

import logging

import pandas as pd

from .common import first_present, percentage, tidy_metric

LOGGER = logging.getLogger(__name__)


def build_tbhiv_indicators(
    estimates: pd.DataFrame,
    notifications: pd.DataFrame | None = None,
) -> pd.DataFrame:
    parts = []

    specs = [
        ("e_inc_tbhiv_num", "estimated_tbhiv_incidence_num", "Estimated HIV-associated TB incidence", "people"),
        ("e_inc_tbhiv_100k", "estimated_tbhiv_incidence_rate", "Estimated HIV-associated TB incidence rate", "per 100,000 population"),
        ("e_mort_tbhiv_num", "estimated_tbhiv_deaths_num", "Estimated HIV-associated TB deaths", "deaths"),
        ("e_mort_tbhiv_100k", "estimated_tbhiv_death_rate", "Estimated HIV-associated TB mortality rate", "per 100,000 population"),
    ]

    for variable, indicator_id, name, unit in specs:
        if variable in estimates.columns:
            parts.append(
                tidy_metric(
                    estimates,
                    year_col="year",
                    value_col=variable,
                    indicator_id=indicator_id,
                    indicator_name=name,
                    unit=unit,
                    source="WHO Global TB Database: burden estimates",
                )
            )

    # Country-reported TB/HIV variables have changed over time. Use a small set
    # of recognised aliases and only derive percentages when both operands exist.
    if notifications is not None and "year" in notifications.columns:
        tested = first_present(
            notifications.columns,
            ("hivtest", "hiv_tested", "hiv_tst"),
        )
        positive = first_present(
            notifications.columns,
            ("hiv_pos", "hiv_positive", "hivpos"),
        )
        art = first_present(
            notifications.columns,
            ("art", "hiv_art", "art_num"),
        )

        tmp = notifications.copy()
        if tested and positive:
            tmp["tb_hiv_positivity_pct"] = percentage(tmp[positive], tmp[tested])
            parts.append(
                tidy_metric(
                    tmp,
                    year_col="year",
                    value_col="tb_hiv_positivity_pct",
                    indicator_id="tb_hiv_positivity_among_tested",
                    indicator_name="HIV positivity among TB patients tested for HIV",
                    unit="percent",
                    source="Derived from WHO country-reported TB/HIV variables",
                    notes=f"Formula: {positive} / {tested} * 100",
                )
            )

        if positive and art:
            tmp["art_coverage_tbhiv_pct"] = percentage(tmp[art], tmp[positive])
            parts.append(
                tidy_metric(
                    tmp,
                    year_col="year",
                    value_col="art_coverage_tbhiv_pct",
                    indicator_id="art_coverage_among_hiv_positive_tb",
                    indicator_name="ART coverage among HIV-positive TB patients",
                    unit="percent",
                    source="Derived from WHO country-reported TB/HIV variables",
                    notes=f"Formula: {art} / {positive} * 100",
                )
            )

    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)
