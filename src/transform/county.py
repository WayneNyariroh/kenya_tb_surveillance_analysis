from __future__ import annotations

import re
import unicodedata
from difflib import get_close_matches

KENYA_COUNTIES = [
    "Baringo","Bomet","Bungoma","Busia","Elgeyo-Marakwet","Embu","Garissa","Homa Bay","Isiolo","Kajiado",
    "Kakamega","Kericho","Kiambu","Kilifi","Kirinyaga","Kisii","Kisumu","Kitui","Kwale","Laikipia","Lamu",
    "Machakos","Makueni","Mandera","Marsabit","Meru","Migori","Mombasa","Murang'a","Nairobi","Nakuru","Nandi",
    "Narok","Nyamira","Nyandarua","Nyeri","Samburu","Siaya","Taita-Taveta","Tana River","Tharaka-Nithi",
    "Trans Nzoia","Turkana","Uasin Gishu","Vihiga","Wajir","West Pokot"
]

def _key(value: object) -> str:
    text = unicodedata.normalize("NFKD", "" if value is None else str(value))
    text = text.replace("’", "'").replace("`", "'")
    text = re.sub(r"\bcounty\b", "", text, flags=re.I)
    text = re.sub(r"[^a-zA-Z0-9']+", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()

CANONICAL = {_key(c): c for c in KENYA_COUNTIES}
CANONICAL.update({
    "homabay":"Homa Bay", "homa bay":"Homa Bay", "muranga":"Murang'a", "murang'a":"Murang'a",
    "elgeyo marakwet":"Elgeyo-Marakwet", "taita taveta":"Taita-Taveta", "tharaka nithi":"Tharaka-Nithi",
    "trans nzoia":"Trans Nzoia", "uasin gishu":"Uasin Gishu", "west pokot":"West Pokot", "nairobi city":"Nairobi"
})

def normalise_county_name(value: object, *, strict: bool = False, fuzzy: bool = False) -> str | None:
    if value is None or not str(value).strip(): return None
    raw = str(value).strip()
    key = _key(raw)
    if key in CANONICAL: return CANONICAL[key]
    if fuzzy:
        matches = get_close_matches(key, list(CANONICAL), n=1, cutoff=0.88)
        if matches: return CANONICAL[matches[0]]
    if strict: raise ValueError(f"Unrecognised Kenya county name: {raw!r}")
    return raw

def validate_counties(values) -> list[str]:
    valid = set(KENYA_COUNTIES)
    unknown = []
    for value in values:
        n = normalise_county_name(value)
        if n is not None and n not in valid: unknown.append(str(value))
    return sorted(set(unknown))
