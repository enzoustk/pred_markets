"""
Funções para puxar dados da API da Polymarket
"""
import time
import logging
from api.helpers import safe_request, dedupe_key
from api.config import URLS, PARAMS
from typing import List, Dict, Any, Set, Tuple


def fetch_trades_for_wallet(
        wallet: str
        ) -> List[Dict[str, Any]]:
    """
    Puxa todas as trades para uma dada wallet e retorna-as;
    Trades: Ordens de Compras e Vendas
    """
    seen_keys: Set[Tuple] = set()
    all_trades: List[Dict[str, Any]] = []

    for taker_flag in [True, False, "true", "false", None]:
        offset = 0
        last_count = -1
        
        while True:
            params = {
                "user": wallet,
                "limit": PARAMS["LIMIT"],
                "offset": offset
                }
            
            if taker_flag is not None:
                params["takerOnly"] = taker_flag
            chunk = safe_request(URLS["TRADES_API"], params)
            
            logging.info("trades wallet=%s takerOnly=%s offset=%d got=%d", wallet, taker_flag, offset, len(chunk))
            
            if not chunk:
                break
            
            new_found = 0
            
            for t in chunk:
                t["type"] = "TRADE"
                k = dedupe_key(t)
                if k not in seen_keys:
                    seen_keys.add(k)
                    all_trades.append(t)
                    new_found += 1
            if new_found == 0 or len(chunk) < PARAMS["LIMIT"] or len(all_trades) == last_count:
                break

            last_count = len(all_trades)
            offset += PARAMS["LIMIT"]
            time.sleep(PARAMS["SLEEP"])
            if len(all_trades) >= PARAMS["MAX_RECORDS"]:
                break
    
    return all_trades
