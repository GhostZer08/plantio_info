from app import app, db

# Inicializar o banco de dados
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
