"""
Servidor Flask para servir o dashboard e processar requisições de CLV.
"""
import os
import json
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dashboard.clv.clv_analysis import calculate_clv_analysis

# Caminho base do dashboard
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DASHBOARD_OUTPUT_DIR = os.path.join(BASE_DIR, 'dashboard_output')

app = Flask(__name__, static_folder=DASHBOARD_OUTPUT_DIR, static_url_path='')
CORS(app)  # Permitir CORS para requisições do frontend


@app.route('/api/calculate_clv', methods=['POST'])
def calculate_clv_endpoint():
    """
    Endpoint para calcular CLV.
    Recebe um DataFrame (JSON) e user_address, retorna estatísticas de CLV.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Nenhum dado fornecido'}), 400
        
        # Extrair dados
        df_data = data.get('df_data', [])
        user_address = data.get('user_address', '')
        
        if not df_data:
            return jsonify({'error': 'DataFrame vazio'}), 400
        
        if not user_address:
            return jsonify({'error': 'user_address não fornecido'}), 400
        
        # Converter JSON para DataFrame
        df = pd.DataFrame(df_data)
        
        # Calcular CLV
        stats = calculate_clv_analysis(df, user_address)
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    """Serve a página principal do dashboard."""
    return send_from_directory(DASHBOARD_OUTPUT_DIR, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve arquivos estáticos do dashboard."""
    return send_from_directory(DASHBOARD_OUTPUT_DIR, path)


if __name__ == '__main__':
    print(f"Servidor Flask iniciado. Dashboard disponível em http://localhost:5000")
    print(f"Diretório do dashboard: {DASHBOARD_OUTPUT_DIR}")
    app.run(debug=True, port=5000)

