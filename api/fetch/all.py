import logging
from api.config import PARAMS
from typing import List, Dict, Any, Set, Tuple
from api.fetch.activity import fetch_activity_all_types
from api.fetch.trades import fetch_trades_for_wallet
from api.helpers import dedupe_key

def fetch_all_data(wallet: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    all_trades: List[Dict[str, Any]] = []
    all_actions: List[Dict[str, Any]] = []
    seen_keys: Set[Tuple] = set()
    wallets_to_process = [wallet]
    processed_wallets: Set[str] = set()

    while wallets_to_process:
        w = wallets_to_process.pop(0)
        if w in processed_wallets:
            continue
        processed_wallets.add(w)
        logging.info("Processing wallet=%s (remaining=%d)", w, len(wallets_to_process))

        trades = fetch_trades_for_wallet(w)
        acts = fetch_activity_all_types(w)

        for t in trades + acts:
            proxy = t.get("proxyWallet") or t.get("proxy_wallet") or t.get("proxy")
            if proxy and isinstance(proxy, str) and proxy not in processed_wallets and proxy not in wallets_to_process:
                wallets_to_process.append(proxy)

            k = dedupe_key(t)
            if k not in seen_keys:
                seen_keys.add(k)
                if t.get("type") == "TRADE":
                    all_trades.append(t)
                else:
                    all_actions.append(t)

        if len(all_trades) + len(all_actions) >= PARAMS["MAX_RECORDS"]:
            logging.warning("Reached PARAMS[MAX_RECORDS] global limit.")
            break

    logging.info("Total trades=%d | other actions=%d", len(all_trades), len(all_actions))
    return all_trades, all_actions