import ast
import sys
import time
import threading
import pandas as pd
from contextlib import contextmanager

def safe_divide(num, den, fallback=None):
    try: return num/den
    except: return fallback

def to_list(x):
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        try:
            v = ast.literal_eval(x)
            return v if isinstance(v, list) else []
        except:
            return []
    return []

def get_exploded_df(df: pd.DataFrame, exclude_tags: list = []) -> pd.DataFrame:
    """
    Cria DataFrame exploded com tags para análise detalhada.
    Usa a lógica de 'tag_analysis' para duplicar a funcionalidade.
    """
    df = df.copy()
    removed_tags = ['Games', 'Sports'] + exclude_tags
    
    tmp = df.copy()
    tmp['__tags_list'] = tmp['tags'].apply(to_list)
    exploded = tmp.explode('__tags_list', ignore_index=True)
    exploded = exploded.rename(columns={'__tags_list': 'tag'})
    exploded = exploded[exploded['tag'].notna()]
    exploded = exploded[~exploded['tag'].isin(removed_tags)]
    
    # Usar apenas realizedPnl para evitar duplicação
    if 'realizedPnl' not in exploded.columns:
        exploded['realizedPnl'] = 0
        
    exploded['total_profit'] = exploded['realizedPnl'].fillna(0)
    exploded['volume'] = exploded['totalBought'] * exploded['avgPrice']
    exploded['staked'] = exploded['totalBought'] * exploded['avgPrice']
    

    exploded['roi'] = safe_divide(exploded['total_profit'], exploded['volume'])

    
    return exploded

def sep():
    return str(20 * '=')

def _animate_loading(stop_event: threading.Event, status_data: dict):
    """
    (Função auxiliar) Exibe animação lendo a mensagem de um dict.
    """
    chars = ["   ", ".  ", ".. ", "..."]
    idx = 0
    last_line_len = 0 # Para limpar a linha corretamente

    while not stop_event.is_set():
        # --- MUDANÇA: Lê a mensagem do dicionário a cada iteração ---
        message = status_data.get('message', 'Carregando')
        dots = chars[idx % len(chars)]
        
        # Prepara a linha para impressão
        line = f"\r{message}{dots}"
        current_line_len = len(line)

        # Adiciona "padding" (espaços em branco) se a linha atual
        # for mais curta que a anterior, para apagar os caracteres antigos.
        padding = " " * max(0, last_line_len - current_line_len)
        
        sys.stdout.write(line + padding)
        sys.stdout.flush()
        
        last_line_len = current_line_len # Guarda o tamanho da linha
        idx += 1
        time.sleep(0.3)
    
    # Limpa a linha ao terminar
    sys.stdout.write("\r" + " " * last_line_len + "\r")
    sys.stdout.flush()

@contextmanager
def loading_animation(initial_message: str = "Carregando..."):
    """
    Gerenciador de contexto que exibe uma animação e 'yields'
    o dicionário de status para permitir atualizações da mensagem.
    """
    # --- MUDANÇA: Cria um dicionário para compartilhar o status ---
    status_data = {'message': initial_message}
    stop_event = threading.Event()
    
    animation_thread = threading.Thread(
        target=_animate_loading,
        # --- MUDANÇA: Passa o dicionário para a thread ---
        args=(stop_event, status_data)
    )
    animation_thread.start()
    
    try:
        # --- MUDANÇA: 'Entrega' o dicionário para o bloco 'with' ---
        yield status_data
    finally:
        # Garante que a thread pare
        stop_event.set()
        animation_thread.join()