import logging
import requests
from api.config import PARAMS
from typing import List, Dict, Any, Tuple
from requests.adapters import HTTPAdapter, Retry

def start_session():
    """
    Cria e configura um objeto session da biblioteca requests,
    Com comportamento aprimorado para chamadas repetidas de API.
    """
    session = requests.Session()
    session.headers.update({"User-Agent": "polymarket-all-actions/6.0"})
    retries = Retry(total=5, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def safe_request(
        url: str,
        params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Ele encapsula toda a lógica de fazer requisições à API da Polymarket
    garantindo que nunca quebre o programa e que sempre devolva algo previsível
    mesmo em caso de erro.
    """
    
    try:
        session = start_session()
        r = session.get(url, params=params, timeout=PARAMS["TIMEOUT"])
        r.raise_for_status()
        j = r.json()
        if isinstance(j, list):
            return j
        if isinstance(j, dict):
            for k in ("results", "items", "activity", "trades", "data"):
                if isinstance(j.get(k), list):
                    return j[k]
        return []
    except Exception as e:
        logging.warning("Request failed url=%s params=%s err=%s", url, params, e)
        return []
    
def dedupe_key(t: Dict[str, Any]) -> Tuple:
    """
    Serve para remover eventos duplicados das transações puxadas
    """
    tx = t.get("transactionHash") or t.get("txHash") or ""
    li = t.get("logIndex") or t.get("log_index") or t.get("logindex")
    ident = t.get("id") or t.get("activityId") or t.get("tradeId") or ""
    ts = t.get("timestamp") or t.get("time") or t.get("createdAt") or ""
    return (str(tx), str(li), str(ident), str(ts), str(t.get("type")), str(t.get("side")), str(t.get("price")))

def ensure_usdc_size(t: Dict[str, Any]) -> float:
    """
    Padroniza todas as Respostas que envolvem usdc como usdcSize
    """
    for c in ["usdcSize", "usdSize", "value", "fillValue", "amount"]:
        try:
            if t.get(c) is not None:
                return float(t[c])
        except Exception:
            continue
    try:
        return float(t.get("price", 0)) * float(t.get("size", 0))
    except Exception:
        return 0.0
