from __future__ import annotations

import argparse, json, logging
from pathlib import Path
from .who_tb import transform_who_tb
from .knbs import transform_knbs_population
from .kmhfr import transform_kmhfr
from .hiv import transform_hiv
from .model import build_dim_county, build_national_tb_year
LOGGER=logging.getLogger(__name__)

def run_transform_pipeline(raw_root: Path | str="data/raw", processed_root: Path | str="data/processed", model_root: Path | str="data/model") -> dict:
    raw_root, processed_root, model_root=Path(raw_root),Path(processed_root),Path(model_root); results={}
    steps=[
      ("who_tb",lambda:transform_who_tb(raw_root/"who_tb",processed_root/"who_tb")),
      ("knbs",lambda:transform_knbs_population(raw_root/"knbs",processed_root/"knbs")),
      ("kmhfr",lambda:transform_kmhfr(raw_root/"kmhfr",processed_root/"kmhfr")),
      ("hiv",lambda:transform_hiv(raw_root/"hiv",processed_root/"hiv"))]
    for name,fn in steps:
        try: results[name]={"status":"ok","outputs":{k:str(v) for k,v in fn().items()}}
        except FileNotFoundError as e: results[name]={"status":"skipped","reason":str(e)}; LOGGER.warning("%s skipped: %s",name,e)
        except Exception as e: results[name]={"status":"failed","reason":str(e)}; LOGGER.exception("%s failed",name)
    model={}
    try:
        p=build_dim_county(processed_root,model_root)
        if p: model["dim_county"]=str(p)
    except Exception as e: model["dim_county_error"]=str(e)
    try:
        p=build_national_tb_year(processed_root,model_root)
        if p: model["fact_national_tb_year"]=str(p)
    except Exception as e: model["fact_national_tb_year_error"]=str(e)
    results["model"]=model; model_root.mkdir(parents=True,exist_ok=True); (model_root/"transform_run.json").write_text(json.dumps(results,indent=2),encoding="utf-8"); return results

def main():
    p=argparse.ArgumentParser(); p.add_argument("--raw-root",default="data/raw"); p.add_argument("--processed-root",default="data/processed"); p.add_argument("--model-root",default="data/model"); a=p.parse_args(); print(json.dumps(run_transform_pipeline(a.raw_root,a.processed_root,a.model_root),indent=2))
if __name__ == "__main__": main()
