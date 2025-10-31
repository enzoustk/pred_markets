"""
Configurações e constantes para chamadas às APIs da polymarket
"""

URLS = {
    "TRADES": "https://data-api.polymarket.com/trades",
    "ACTIVITY": "https://data-api.polymarket.com/activity",
    "CLOSED_POSITIONS": "https://data-api.polymarket.com/closed-positions",
    "ACTIVE_POSITIONS": "https://data-api.polymarket.com/positions",
    "MARKET": "https://gamma-api.polymarket.com/markets"
}

ACTION_TYPES = [
    "TRADE",
    "SPLIT",
    "MERGE",
    "REDEEM",
    "REWARD",
    "CONVERSION"
    ]