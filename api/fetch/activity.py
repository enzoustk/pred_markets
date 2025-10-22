"""
Puxar todos os metadados de Trades:
Mergesm, Redeems, etc.
"""
import time
import logging
from typing import List, Dict, Any, Set, Tuple
from api.config import PARAMS, URLS, ACTION_TYPES
from helpers import safe_request, dedupe_key


def fetch_activity_all_types(wallet: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    seen_keys: Set[Tuple] = set()
    offset = 0
    last_total = -1
    while True:
        params = {"user": wallet, "limit": PARAMS["LIMIT"], "offset": offset}
        chunk = safe_request(URLS["ACTIVITY_API"], params)
        logging.info("activity wallet=%s offset=%d got=%d", wallet, offset, len(chunk))
        if not chunk:
            break
        new_found = 0
        for t in chunk:
            if t.get("type") not in ACTION_TYPES:
                continue
            k = dedupe_key(t)
            if k not in seen_keys:
                seen_keys.add(k)
                results.append(t)
                new_found += 1
        if new_found == 0 or len(chunk) < PARAMS["LIMIT"] or len(results) == last_total:
            break
        last_total = len(results)
        offset += PARAMS["LIMIT"]
        time.sleep(PARAMS["SLEEP"])
        if len(results) >= PARAMS["MAX_RECORDS"]:
            break
    return results