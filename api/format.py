### Recebe os dados "crus", formata e retorna limpos e formatados
import logging
import pandas as pd
from typing import List, Dict, Any

def normalize_and_export(records: List[Dict[str, Any]], out_path: str):
    if not records:
        logging.warning("Nenhum registro para %s", out_path)
        return
    df = pd.json_normalize(records, sep=".")
    for c in ("price", "size"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "usdcSize" not in df.columns:
        p = df.get("price", pd.Series([0]*len(df)))
        s = df.get("size", pd.Series([0]*len(df)))
        df["usdcSize"] = pd.to_numeric(p, errors="coerce").fillna(0) * pd.to_numeric(s, errors="coerce")
    df["action_type"] = df.get("type", "UNKNOWN")
    if "timestamp" in df.columns:
        df["datetime_utc"] = pd.to_datetime(df["timestamp"], unit="s", utc=True, errors="coerce")
    elif "createdAt" in df.columns:
        df["datetime_utc"] = pd.to_datetime(df["createdAt"], utc=True, errors="coerce")
    df = df.sort_values("datetime_utc").reset_index(drop=True)
    df.to_csv(out_path, index=False)
    logging.info("Exportado %s (%d registros, %d colunas)", out_path, len(df), len(df.columns))
