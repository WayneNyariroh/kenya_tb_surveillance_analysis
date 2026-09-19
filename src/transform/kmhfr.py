from __future__ import annotations

import argparse
import logging
from pathlib import Path
import pandas as pd
from .common import clean_columns, coerce_numeric, ensure_dir, first_existing, write_table
from .county import normalise_county_name, validate_counties

LOGGER=logging.getLogger(__name__)

def transform_kmhfr(raw_dir: Path | str="data/raw/kmhfr", output_dir: Path | str="data/processed/kmhfr") -> dict[str, Path]:
    raw_dir, output_dir=Path(raw_dir), ensure_dir(output_dir); path=raw_dir/"facilities.csv"
    if not path.exists(): raise FileNotFoundError(path)
    df=clean_columns(pd.read_csv(path,low_memory=False))
    mapping={
      "facility_id":["id","facility_id","code","facility_code","mfl_code","keph_code"],
      "facility_name":["name","facility_name","official_name"],
      "county":["county","county_name","sub_county_county_name","location_county_name"],
      "subcounty":["sub_county","subcounty","sub_county_name","location_sub_county_name"],
      "ward":["ward","ward_name","location_ward_name"],
      "ownership":["owner","ownership","owner_name","facility_owner_name","owner_owner_name"],
      "facility_type":["facility_type","facility_type_name","type","type_name"],
      "keph_level":["keph_level","keph_level_name","level","facility_level"],
      "operational_status":["operational_status","operation_status","status","operational_status_name"],
      "latitude":["latitude","lat","coordinates_latitude"],
      "longitude":["longitude","lng","lon","coordinates_longitude"]}
    out=pd.DataFrame(index=df.index)
    for target,candidates in mapping.items():
        source=first_existing(df.columns,candidates)
        if source: out[target]=df[source]
    if "facility_name" not in out.columns: raise ValueError(f"Could not identify facility name. Columns begin: {list(df.columns[:40])}")
    if "county" in out.columns:
        out["county"]=out["county"].map(normalise_county_name); unknown=validate_counties(out["county"].dropna().tolist())
        if unknown: LOGGER.warning("Unrecognised county values: %s",unknown)
    for c in ("latitude","longitude"):
        if c in out.columns: out[c]=coerce_numeric(out[c])
    if "latitude" in out.columns: out.loc[~out["latitude"].between(-5.5,5.5),"latitude"]=pd.NA
    if "longitude" in out.columns: out.loc[~out["longitude"].between(33.0,42.5),"longitude"]=pd.NA
    for c in ["facility_name","subcounty","ward","ownership","facility_type","keph_level","operational_status"]:
        if c in out.columns: out[c]=out[c].astype("string").str.strip()
    if "facility_id" not in out.columns: out["facility_id"]=[str(i) for i in range(1,len(out)+1)]
    out["facility_id"]=out["facility_id"].astype("string").str.strip(); out=out.drop_duplicates(subset=["facility_id"]).reset_index(drop=True)
    fp=output_dir/"dim_facility.csv"; write_table(out,fp,metadata={"source":"KMHFR","grain":"facility"}); outputs={"dim_facility":fp}
    if "county" in out.columns:
        summary=out.groupby("county",dropna=False)["facility_id"].nunique().rename("facility_count").reset_index()
        if "latitude" in out.columns and "longitude" in out.columns:
            valid=out["latitude"].notna() & out["longitude"].notna(); cc=out.loc[valid].groupby("county")["facility_id"].nunique().rename("facilities_with_valid_coordinates").reset_index(); summary=summary.merge(cc,on="county",how="left"); summary["facilities_with_valid_coordinates"]=summary["facilities_with_valid_coordinates"].fillna(0).astype(int)
        sp=output_dir/"county_facility_summary.csv"; write_table(summary,sp,metadata={"source":"KMHFR","grain":"county"}); outputs["county_facility_summary"]=sp
    return outputs

def main():
    p=argparse.ArgumentParser(); p.add_argument("--raw-dir",default="data/raw/kmhfr"); p.add_argument("--output-dir",default="data/processed/kmhfr"); a=p.parse_args(); transform_kmhfr(a.raw_dir,a.output_dir)
if __name__ == "__main__": main()
