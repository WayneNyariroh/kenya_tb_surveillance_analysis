from __future__ import annotations

from pathlib import Path

import pandas as pd


def ensure_dir(path: Path | str) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_required_csv(path: Path | str, required: set[str] | None = None) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path, low_memory=False)

    if required:
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"{path.name} is missing required columns: {sorted(missing)}")

    return df


def clean_indicator_label(value: str) -> str:
    return (
        str(value)
        .replace("_", " ")
        .replace("tb hiv", "TB/HIV")
        .replace("tb", "TB")
        .title()
        .replace("Tb", "TB")
        .replace("Hiv", "HIV")
    )
