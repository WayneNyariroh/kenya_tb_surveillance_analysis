from __future__ import annotations

import logging

import pandas as pd

from .common import first_present, numeric, percentage, rate_per_100k, tidy_metric

LOGGER = logging.getLogger(__name__)

NOTIFICATION_TOTAL_CANDIDATES = (
    "c_newinc",
    "newrel",
)

POPULATION_CANDIDATES = ("e_pop_num", "population")
INCIDENCE_CANDIDATES = ("e_inc_num",)


def build_notification_indicators(
    notifications: pd.DataFrame,
    estimates: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if "year" not in notifications.columns:
        raise ValueError("WHO notification table has no year column.")

    total_col = first_present(notifications.columns, NOTIFICATION_TOTAL_CANDIDATES)
    if not total_col:
        LOGGER.warning(
            "No recognised total notification field found. Tried: %s",
            NOTIFICATION_TOTAL_CANDIDATES,
        )
        return pd.DataFrame()

    parts = [
        tidy_metric(
            notifications,
            year_col="year",
            value_col=total_col,
            indicator_id="notifications",
            indicator_name="New and relapse TB notifications",
            unit="people",
            source="WHO Global TB Database: case notifications",
            notes="Reported surveillance/programme observations.",
        )
    ]

    if estimates is None or "year" not in estimates.columns:
        return pd.concat(parts, ignore_index=True)

    keep = ["year"]
    pop_col = first_present(estimates.columns, POPULATION_CANDIDATES)
    inc_col = first_present(estimates.columns, INCIDENCE_CANDIDATES)
    if pop_col:
        keep.append(pop_col)
    if inc_col:
        keep.append(inc_col)

    merged = notifications[["year", total_col]].merge(
        estimates[keep], on="year", how="left"
    )

    if pop_col:
        merged["notification_rate"] = rate_per_100k(
            merged[total_col], merged[pop_col]
        )
        parts.append(
            tidy_metric(
                merged,
                year_col="year",
                value_col="notification_rate",
                indicator_id="notification_rate",
                indicator_name="TB notification rate",
                unit="per 100,000 population",
                source="Derived from WHO notifications and WHO population",
                notes=f"Formula: {total_col} / {pop_col} * 100000",
            )
        )

    if inc_col:
        merged["notification_incidence_gap"] = (
            numeric(merged[inc_col]) - numeric(merged[total_col])
        )
        merged["notification_to_incidence_ratio"] = percentage(
            merged[total_col], merged[inc_col]
        )

        parts.append(
            tidy_metric(
                merged,
                year_col="year",
                value_col="notification_incidence_gap",
                indicator_id="notification_incidence_gap",
                indicator_name="Estimated incidence-to-notification gap",
                unit="people",
                source="Derived from WHO burden estimates and notifications",
                notes=(
                    "Estimated incidence minus notifications. This is not a direct "
                    "count of undiagnosed people."
                ),
            )
        )
        parts.append(
            tidy_metric(
                merged,
                year_col="year",
                value_col="notification_to_incidence_ratio",
                indicator_id="notification_to_incidence_ratio",
                indicator_name="Notification-to-incidence ratio",
                unit="percent",
                source="Derived from WHO burden estimates and notifications",
                notes=(
                    "Notifications / estimated incidence * 100. Do not interpret "
                    "automatically as a measured case-detection rate."
                ),
            )
        )

    return pd.concat(parts, ignore_index=True)
