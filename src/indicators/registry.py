from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndicatorDefinition:
    id: str
    name: str
    unit: str
    source_table: str
    description: str
    source_variables: tuple[str, ...] = ()
    derived: bool = False
    formula: str | None = None
    caution: str | None = None


INDICATORS: dict[str, IndicatorDefinition] = {
    "population": IndicatorDefinition(
        id="population",
        name="Population",
        unit="people",
        source_table="WHO burden estimates",
        description="Population denominator supplied with the WHO burden estimates.",
        source_variables=("e_pop_num", "population"),
    ),
    "estimated_incidence_num": IndicatorDefinition(
        id="estimated_incidence_num",
        name="Estimated TB incidence",
        unit="people",
        source_table="WHO burden estimates",
        description="WHO modelled estimate of incident TB episodes/cases in the year.",
        source_variables=("e_inc_num",),
    ),
    "estimated_incidence_rate": IndicatorDefinition(
        id="estimated_incidence_rate",
        name="Estimated TB incidence rate",
        unit="per 100,000 population",
        source_table="WHO burden estimates",
        description="WHO modelled TB incidence rate.",
        source_variables=("e_inc_100k",),
    ),
    "estimated_tb_deaths_excl_hiv_num": IndicatorDefinition(
        id="estimated_tb_deaths_excl_hiv_num",
        name="Estimated TB deaths excluding HIV-associated TB deaths",
        unit="deaths",
        source_table="WHO burden estimates",
        description="WHO estimate of TB deaths among HIV-negative people.",
        source_variables=("e_mort_exc_tbhiv_num",),
    ),
    "estimated_tb_death_rate_excl_hiv": IndicatorDefinition(
        id="estimated_tb_death_rate_excl_hiv",
        name="Estimated TB mortality rate excluding HIV-associated TB deaths",
        unit="per 100,000 population",
        source_table="WHO burden estimates",
        description="WHO estimate of TB mortality among HIV-negative people.",
        source_variables=("e_mort_exc_tbhiv_100k",),
    ),
    "estimated_tbhiv_incidence_num": IndicatorDefinition(
        id="estimated_tbhiv_incidence_num",
        name="Estimated HIV-associated TB incidence",
        unit="people",
        source_table="WHO burden estimates",
        description="WHO modelled estimate of incident TB among people living with HIV.",
        source_variables=("e_inc_tbhiv_num",),
    ),
    "estimated_tbhiv_incidence_rate": IndicatorDefinition(
        id="estimated_tbhiv_incidence_rate",
        name="Estimated HIV-associated TB incidence rate",
        unit="per 100,000 population",
        source_table="WHO burden estimates",
        description="WHO modelled HIV-associated TB incidence rate.",
        source_variables=("e_inc_tbhiv_100k",),
    ),
    "estimated_tbhiv_deaths_num": IndicatorDefinition(
        id="estimated_tbhiv_deaths_num",
        name="Estimated HIV-associated TB deaths",
        unit="deaths",
        source_table="WHO burden estimates",
        description="WHO estimate of TB deaths among people living with HIV.",
        source_variables=("e_mort_tbhiv_num",),
    ),
    "notifications": IndicatorDefinition(
        id="notifications",
        name="New and relapse TB notifications",
        unit="people",
        source_table="WHO case notifications",
        description="Reported TB notifications, using the current/available WHO total new-and-relapse field.",
        source_variables=("c_newinc", "newrel", "newrel_f014"),
        caution="The resolver uses only a recognised total field. Age/sex component fields are not summed automatically.",
    ),
    "notification_rate": IndicatorDefinition(
        id="notification_rate",
        name="TB notification rate",
        unit="per 100,000 population",
        source_table="Derived",
        description="Reported notifications divided by population.",
        derived=True,
        formula="notifications / population * 100000",
    ),
    "notification_incidence_gap": IndicatorDefinition(
        id="notification_incidence_gap",
        name="Estimated incidence-to-notification gap",
        unit="people",
        source_table="Derived",
        description="Difference between WHO estimated incident TB and reported notifications.",
        derived=True,
        formula="estimated incidence - notifications",
        caution="This is not a direct count of undiagnosed people. Incidence is modelled and notifications are surveillance observations.",
    ),
    "notification_to_incidence_ratio": IndicatorDefinition(
        id="notification_to_incidence_ratio",
        name="Notification-to-incidence ratio",
        unit="percent",
        source_table="Derived",
        description="Reported notifications as a percentage of WHO estimated incidence.",
        derived=True,
        formula="notifications / estimated incidence * 100",
        caution="Do not interpret automatically as a measured case-detection rate.",
    ),
    "facility_density": IndicatorDefinition(
        id="facility_density",
        name="Registered health facilities per 100,000 population",
        unit="per 100,000 population",
        source_table="KNBS + KMHFR",
        description="Facility count divided by 2019 county population.",
        derived=True,
        formula="facility_count / population_2019 * 100000",
        caution="All registered facilities are not necessarily TB diagnostic or treatment sites.",
    ),
}
