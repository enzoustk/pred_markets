"""
Configurações e constantes para chamadas às APIs da polymarket
"""

URLS = {
    "TRADES": "https://data-api.polymarket.com/trades",
    "ACTIVITY": "https://data-api.polymarket.com/activity",
    "CLOSED_POSITIONS": "https://data-api.polymarket.com/closed-positions",
    "ACTIVE_POSITIONS": "https://data-api.polymarket.com/positions",
    "MARKET": "https://gamma-api.polymarket.com/markets",
    "POSITIONS_SUBGRAPH": "https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/positions-subgraph/0.0.7/gn",
    "TOTAL_TRADES": "https://data-api.polymarket.com/traded",
    "CLOB": "https://clob.polymarket.com"
}

ACTION_TYPES = [
    "TRADE",
    "SPLIT",
    "MERGE",
    "REDEEM",
    "REWARD",
    "CONVERSION"
    ]

QUERYS = {
    'CLOSED': """
        query GetUserPositions($userAddress: String!, $first: Int!, $skip: Int!) {
          userBalances(
            where: { user: $userAddress, balance: "0" }
            first: $first
            skip: $skip
            orderBy: balance
            orderDirection: desc
          ) {
            id
            user
            balance
            asset {
              id
              condition {
                id
              }
              outcomeIndex
            }
          }
        }
        """,
        
    'ACTIVE':"""
        query GetUserPositions($userAddress: String!, $first: Int!, $skip: Int!) {
          userBalances(
            where: { user: $userAddress }
            first: $first
            skip: $skip
            orderBy: balance
            orderDirection: desc
          ) {
            id
            user
            balance
            asset {
              id
              condition {
                id
              }
              outcomeIndex
            }
          }
        }
        """,

}