from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .common import first_present, tidy_metric

LOGGER = logging.getLogger(__name__)


BURDEN_SPECS = [
    {
        "id": "population",
        "name": "Population",
        "unit": "people",
        "value": ("e_pop_num", "population"),
    },
    {
        "id": "estimated_incidence_num",
        "name": "Estimated TB incidence",
        "unit": "people",
        "value": ("e_inc_num",),
        "lower": ("e_inc_num_lo",),
        "upper": ("e_inc_num_hi",),
    },
    {
        "id": "estimated_incidence_rate",
        "name": "Estimated TB incidence rate",
        "unit": "per 100,000 population",
        "value": ("e_inc_100k",),
        "lower": ("e_inc_100k_lo",),
        "upper": ("e_inc_100k_hi",),
    },
    {
        "id": "estimated_tb_deaths_excl_hiv_num",
        "name": "Estimated TB deaths excluding HIV-associated TB deaths",
        "unit": "deaths",
        "value": ("e_mort_exc_tbhiv_num",),
        "lower": ("e_mort_exc_tbhiv_num_lo",),
        "upper": ("e_mort_exc_tbhiv_num_hi",),
    },
    {
        "id": "estimated_tb_death_rate_excl_hiv",
        "name": "Estimated TB mortality rate excluding HIV-associated TB deaths",
        "unit": "per 100,000 population",
        "value": ("e_mort_exc_tbhiv_100k",),
        "lower": ("e_mort_exc_tbhiv_100k_lo",),
        "upper": ("e_mort_exc_tbhiv_100k_hi",),
    },
    {
        "id": "estimated_tbhiv_incidence_num",
        "name": "Estimated HIV-associated TB incidence",
        "unit": "people",
        "value": ("e_inc_tbhiv_num",),
        "lower": ("e_inc_tbhiv_num_lo",),
        "upper": ("e_inc_tbhiv_num_hi",),
    },
    {
        "id": "estimated_tbhiv_incidence_rate",
        "name": "Estimated HIV-associated TB incidence rate",
        "unit": "per 100,000 population",
        "value": ("e_inc_tbhiv_100k",),
        "lower": ("e_inc_tbhiv_100k_lo",),
        "upper": ("e_inc_tbhiv_100k_hi",),
    },
    {
        "id": "estimated_tbhiv_deaths_num",
        "name": "Estimated HIV-associated TB deaths",
        "unit": "deaths",
        "value": ("e_mort_tbhiv_num",),
        "lower": ("e_mort_tbhiv_num_lo",),
        "upper": ("e_mort_tbhiv_num_hi",),
    },
]


def build_burden_indicators(estimates: pd.DataFrame) -> pd.DataFrame:
    if "year" not in estimates.columns:
        raise ValueError("WHO estimates table has no year column.")

    parts = []
    for spec in BURDEN_SPECS:
        value = first_present(estimates.columns, spec["value"])
        if not value:
            LOGGER.info("Burden indicator %s unavailable", spec["id"])
            continue
        lower = first_present(estimates.columns, spec.get("lower", ()))
        upper = first_present(estimates.columns, spec.get("upper", ()))
        parts.append(
            tidy_metric(
                estimates,
                year_col="year",
                value_col=value,
                lower_col=lower,
                upper_col=upper,
                indicator_id=spec["id"],
                indicator_name=spec["name"],
                unit=spec["unit"],
                source="WHO Global TB Database: burden estimates",
            )
        )

    if not parts:
        return pd.DataFrame(columns=[
            "year", "indicator_id", "indicator_name", "value", "unit",
            "source", "source_variable", "lower", "upper", "notes"
        ])
    return pd.concat(parts, ignore_index=True)
