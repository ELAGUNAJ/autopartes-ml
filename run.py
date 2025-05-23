import os
import sys
from pathlib import Path

<<<<<<< HEAD
# Obtener el directorio actual y añadirlo al path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Importar create_app desde el módulo app
try:
    from app import create_app
    app = create_app()
except ImportError as e:
    print(f"Error al importar app: {e}")
    # Fallback a una aplicación básica si la importación falla
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return "¡Aplicación en modo fallback! Error al importar módulos."

if __name__ == '__main__':
    print(f"Ejecutando aplicación desde: {current_dir}")
    print(f"Python path: {sys.path}")
=======
# Añadir el directorio raíz al Python path
current_dir = Path(__file__).parent.absolute()  # app/
parent_dir = current_dir.parent                # AUTOPARTES_ML/
sys.path.insert(0, str(parent_dir))

# Ahora importamos desde el directorio actual
from app import create_app  # Esto ahora debería funcionar

app = create_app()

if __name__ == '__main__':
>>>>>>> 32695fbfee91b1bd0b2d97bc0b6297d99ac5a67c
    app.run(debug=True)