import os
import sys
from pathlib import Path

# Añadir directorio raíz al path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from app import create_app, db
from app.models.usuario import Usuario

# Crear una instancia de la aplicación
app = create_app()

# Crear el usuario admin dentro del contexto de la aplicación
with app.app_context():
    # Verificar si ya existe el usuario admin
    admin = Usuario.query.filter_by(username='admin').first()
    if admin:
        print("El usuario admin ya existe.")
    else:
        # Crear usuario admin
        admin = Usuario(
            username='admin',
            email='admin@example.com',
            nombre='Administrador',
            apellido='Sistema',
            rol='admin',
            activo=True
        )
        admin.set_password('admin123')  # ¡Cambia esta contraseña en producción!
        
        # Guardar en la base de datos
        db.session.add(admin)
        db.session.commit()
        print("Usuario admin creado exitosamente.")
        