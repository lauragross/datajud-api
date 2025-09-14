#!/usr/bin/env python3
"""
Script de inicialização para produção do DataJud API
"""
import os
from app import app

if __name__ == "__main__":
    # Configurações para produção
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    
    print(f"Iniciando DataJud API em {host}:{port}")
    print(f"Modo debug: {debug}")
    
    app.run(host=host, port=port, debug=debug)
