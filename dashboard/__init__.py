"""
Módulo dashboard para análise de dados de apostas.
"""
from .gerar_dashboard import criar_dashboard

__all__ = ['criar_dashboard', 'gerar_dashboard']

# Exportar gerar_dashboard como módulo também para compatibilidade
import sys
from . import gerar_dashboard as _gerar_dashboard_module
sys.modules[__name__ + '.gerar_dashboard'] = _gerar_dashboard_module


