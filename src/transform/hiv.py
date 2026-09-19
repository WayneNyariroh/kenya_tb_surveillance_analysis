from __future__ import annotations

import argparse, json, logging
from pathlib import Path
import pandas as pd
from .common import clean_columns, ensure_dir, write_table
from .county import normalise_county_name
LOGGER=logging.getLogger(__name__)

def _load_resource(path: Path) -> pd.DataFrame:
    s=path.suffix.lower()
    if s==".csv": return pd.read_csv(path,low_memory=False)
    if s in {".xlsx",".xls"}: return pd.read_excel(path)
    if s in {".json",".geojson"}:
        payload=json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload,dict) and "features" in payload:
            rows=[]
            for f in payload["features"]:
                row=dict(f.get("properties") or {}); geom=f.get("geometry")
                if geom is not None: row["geometry"]=json.dumps(geom)
                rows.append(row)
            return pd.DataFrame(rows)
        return pd.json_normalize(payload)
    raise ValueError(f"Unsupported HIV resource format: {path.suffix}")

def transform_hiv(raw_dir: Path | str="data/raw/hiv", output_dir: Path | str="data/processed/hiv") -> dict[str, Path]:
    raw_dir, output_dir=Path(raw_dir), ensure_dir(output_dir); manifest_path=raw_dir/"unaids_kenya_hiv_manifest.json"
    if not manifest_path.exists(): LOGGER.warning("HIV manifest not found: %s",manifest_path); return {}
    manifest=json.loads(manifest_path.read_text(encoding="utf-8")); downloaded=[r for r in manifest if r.get("status")=="downloaded" and r.get("local_path")]
    if not downloaded: LOGGER.warning("No public HIV resource files were downloaded; skipping."); return {}
    outputs={}
    for i,item in enumerate(downloaded,1):
        path=Path(item["local_path"]); path=path if path.is_absolute() else raw_dir/path
        if not path.exists(): LOGGER.warning("Manifest resource missing: %s",path); continue
        try: df=clean_columns(_load_resource(path))
        except ValueError as e: LOGGER.warning("%s",e); continue
        for c in ("county","county_name","area_name","geography"):
            if c in df.columns: df["county"]=df[c].map(normalise_county_name); break
        if "year" in df.columns: df["year"]=pd.to_numeric(df["year"],errors="coerce").astype("Int64")
        name=item.get("package_name") or f"resource_{i}"; safe="".join(c if c.isalnum() or c in "_-" else "_" for c in name); out=output_dir/f"{safe}_{i}.csv"
        write_table(df,out,metadata={"source":"UNAIDS ADR / Kenya MoH","package_title":item.get("package_title"),"resource_name":item.get("resource_name")}); outputs[f"resource_{i}"]=out
    return outputs

def main():
    p=argparse.ArgumentParser(); p.add_argument("--raw-dir",default="data/raw/hiv"); p.add_argument("--output-dir",default="data/processed/hiv"); a=p.parse_args(); transform_hiv(a.raw_dir,a.output_dir)
if __name__ == "__main__": main()
