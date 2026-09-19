from __future__ import annotations

import logging
from pathlib import Path
import pandas as pd
from .common import ensure_dir, safe_rate, write_table
LOGGER=logging.getLogger(__name__)

def build_dim_county(processed_root: Path | str="data/processed", output_dir: Path | str="data/model") -> Path | None:
    processed_root, output_dir=Path(processed_root), ensure_dir(output_dir); pop=processed_root/"knbs"/"county_population_2019.csv"
    if not pop.exists(): LOGGER.warning("Cannot build dim_county without %s",pop); return None
    county=pd.read_csv(pop); fac=processed_root/"kmhfr"/"county_facility_summary.csv"
    if fac.exists(): county=county.merge(pd.read_csv(fac),on="county",how="left")
    if "population_2019" in county.columns and "facility_count" in county.columns: county["facilities_per_100k_2019"]=safe_rate(county["facility_count"],county["population_2019"],100000)
    county=county.sort_values("county").reset_index(drop=True); county.insert(0,"county_key",range(1,len(county)+1)); out=output_dir/"dim_county.csv"; write_table(county,out,metadata={"grain":"county"}); return out

def build_national_tb_year(processed_root: Path | str="data/processed", output_dir: Path | str="data/model") -> Path | None:
    processed_root, output_dir=Path(processed_root), ensure_dir(output_dir)
    paths={"est":processed_root/"who_tb"/"estimates_kenya.csv","notif":processed_root/"who_tb"/"notifications_kenya.csv","outc":processed_root/"who_tb"/"outcomes_kenya.csv"}
    frames={k:pd.read_csv(p,low_memory=False) for k,p in paths.items() if p.exists()}
    if not frames: LOGGER.warning("No processed WHO files found"); return None
    keys=[k for k in ("year","country","iso3") if all(k in f.columns for f in frames.values())]
    if "year" not in keys: raise ValueError("Processed WHO datasets do not share a year column")
    merged=None
    for prefix,frame in frames.items():
        frame=frame.rename(columns={c:f"{prefix}_{c}" for c in frame.columns if c not in keys}); merged=frame if merged is None else merged.merge(frame,on=keys,how="outer")
    merged=merged.sort_values("year").reset_index(drop=True); out=output_dir/"fact_national_tb_year.csv"; write_table(merged,out,metadata={"grain":"country-year","country":"Kenya"}); return out
