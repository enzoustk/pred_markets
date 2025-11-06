"""
Módulos utilitários para o dashboard.
"""
from .formatters import (
    format_currency,
    format_percentage,
    format_integer,
    format_date,
    get_profit_loss_class
)
from .data_preparation import (
    prepare_df_columns,
    calculate_flat_profit_by_period,
    calculate_deciles
)

# Importar safe_divide do arquivo utils.py na raiz do dashboard
# Usar importlib para evitar conflito de nomes
import importlib.util
import os
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_utils_file_path = os.path.join(_parent_dir, 'utils.py')

if os.path.exists(_utils_file_path):
    spec = importlib.util.spec_from_file_location("dashboard_utils_root", _utils_file_path)
    _utils_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_utils_module)
    safe_divide = _utils_module.safe_divide
else:
    # Fallback: tentar importar normalmente (pode falhar se houver conflito)
    import sys
    import importlib
    try:
        # Tentar importar do módulo na raiz
        _utils_module = importlib.import_module('dashboard.utils')
        # Se utils.py existe, tentar acessar diretamente
        if hasattr(_utils_module, 'safe_divide'):
            safe_divide = _utils_module.safe_divide
        else:
            raise AttributeError("safe_divide não encontrado")
    except Exception:
        raise ImportError(f"Não foi possível importar safe_divide. Verifique se {_utils_file_path} existe.")

__all__ = [
    'format_currency',
    'format_percentage',
    'format_integer',
    'format_date',
    'get_profit_loss_class',
    'safe_divide',
    'prepare_df_columns',
    'calculate_flat_profit_by_period',
    'calculate_deciles'
]

