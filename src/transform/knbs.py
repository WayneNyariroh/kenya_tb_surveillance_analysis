from __future__ import annotations

import argparse
import logging
from pathlib import Path
import pandas as pd
from .common import clean_columns, coerce_numeric, ensure_dir, first_existing, write_table
from .county import normalise_county_name, validate_counties

LOGGER=logging.getLogger(__name__)
COUNTY_FILE="knbs_2019_county_population.xlsx"
SUBCOUNTY_FILE="knbs_2019_subcounty_population.xlsx"

def _read_knbs_sheet(path: Path) -> pd.DataFrame:
    preview=pd.read_excel(path,sheet_name=0,header=None,nrows=20)
    header_idx=0
    for idx,row in preview.iterrows():
        text=" ".join(str(v).lower() for v in row.dropna().tolist())
        if "county" in text and ("population" in text or "total" in text): header_idx=idx; break
    df=pd.read_excel(path,sheet_name=0,header=header_idx)
    return clean_columns(df.dropna(how="all").reset_index(drop=True))

def _transform_county_population(df: pd.DataFrame) -> pd.DataFrame:
    county_col=first_existing(df.columns,["county","county_name","administrative_unit","area"])
    if not county_col: raise ValueError(f"Could not identify county column. Columns: {list(df.columns)}")
    out=df.copy(); out["county"]=out[county_col].map(normalise_county_name)
    out=out[~out["county"].astype("string").str.casefold().isin({"kenya","total","national","nan","<na>"})].copy()
    population_col=first_existing(out.columns,["total_population","population","total","both_sexes","total_no"])
    households_col=first_existing(out.columns,["households","number_of_households","no_of_households"])
    area_col=first_existing(out.columns,["land_area_sq_km","land_area_km2","area_sq_km","land_area"])
    density_col=first_existing(out.columns,["population_density","density","density_persons_per_sq_km"])
    if population_col: out["population_2019"]=coerce_numeric(out[population_col])
    if households_col: out["households_2019"]=coerce_numeric(out[households_col])
    if area_col: out["land_area_sq_km"]=coerce_numeric(out[area_col])
    if density_col: out["population_density_2019"]=coerce_numeric(out[density_col])
    unknown=validate_counties(out["county"].dropna().tolist())
    if unknown: LOGGER.warning("Unrecognised county-like values: %s",unknown)
    out["year"]=2019
    return out.drop_duplicates(subset=["county"]).sort_values("county").reset_index(drop=True)

def transform_knbs_population(raw_dir: Path | str="data/raw/knbs", output_dir: Path | str="data/processed/knbs") -> dict[str, Path]:
    raw_dir, output_dir=Path(raw_dir), ensure_dir(output_dir); outputs={}
    cp=raw_dir/COUNTY_FILE
    if cp.exists():
        df=_transform_county_population(_read_knbs_sheet(cp)); out=output_dir/"county_population_2019.csv"; write_table(df,out,metadata={"source":"KNBS 2019 Census","grain":"county"}); outputs["county_population"]=out
    else: LOGGER.warning("KNBS county workbook not found: %s",cp)
    sp=raw_dir/SUBCOUNTY_FILE
    if sp.exists():
        df=_read_knbs_sheet(sp); df["year"]=2019; out=output_dir/"subcounty_population_2019.csv"; write_table(df,out,metadata={"source":"KNBS 2019 Census","grain":"subcounty/raw"}); outputs["subcounty_population"]=out
    return outputs

def main():
    p=argparse.ArgumentParser(); p.add_argument("--raw-dir",default="data/raw/knbs"); p.add_argument("--output-dir",default="data/processed/knbs"); a=p.parse_args(); transform_knbs_population(a.raw_dir,a.output_dir)
if __name__ == "__main__": main()
