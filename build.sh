#!/bin/bash
# Instalar dependências
pip install -r requirements.txt

# Inicializar o banco de dados
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Migrar dados existentes (opcional)
# python migrate_data.py
