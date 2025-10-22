### Recebe os dados "crus", formata e retorna limpos e formatados
import logging
import pandas as pd
from typing import List, Dict, Any

def normalize(records: List[Dict[str, Any]]):
    if not records:
        logging.warning("Nenhum registro para %s")
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
    return df

def export(data: pd.DataFrame, out_path: str):
    data.to_csv(out_path, index=False)
    logging.info(f"Data exported to {out_path} sucessfully")