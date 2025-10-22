"""
Configurações e constantes para chamadas às APIs da polymarket
"""

URLS = {
    "TRADES_API": "https://data-api.polymarket.com/trades",
    "ACTIVITY_API": "https://data-api.polymarket.com/activity",
}

PARAMS = {
    "LIMIT": 500,
    "TIMEOUT": 20,
    "SLEEP": 0.25,
    "MAX_PAGES": 20_000,
    "MAX_RECORDS": 300_000
}

ACTION_TYPES = [
    "TRADE",
    "SPLIT",
    "MERGE",
    "REDEEM",
    "REWARD",
    "CONVERSION"
    ]