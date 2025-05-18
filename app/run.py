import os
import sys
from pathlib import Path

# Añadir el directorio raíz al Python path
current_dir = Path(__file__).parent.absolute()  # app/
parent_dir = current_dir.parent                # AUTOPARTES_ML/
sys.path.insert(0, str(parent_dir))

# Ahora importamos desde el directorio actual
from app import create_app  # Esto ahora debería funcionar

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)