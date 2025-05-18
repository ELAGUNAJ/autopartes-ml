from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Usuario(UserMixin, db.Model):
    """Modelo para la tabla de usuarios del sistema."""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(100))
    apellido = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    rol = db.Column(db.String(20), nullable=False)  # 'admin', 'vendedor'
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    ventas = db.relationship('Venta', backref='usuario', lazy='dynamic')
    
    def __repr__(self):
        return f'<Usuario {self.username} - {self.rol}>'
    
    def to_dict(self):
        """Convertir objeto a diccionario para API/JSON (sin incluir contraseña)."""
        return {
            'id': self.id,
            'username': self.username,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'email': self.email,
            'rol': self.rol,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat()
        }
    
    def set_password(self, password):
        """Establecer contraseña encriptada."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verificar contraseña."""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Verificar si el usuario es administrador."""
        return self.rol == 'admin'
    
    def is_vendedor(self):
        """Verificar si el usuario es vendedor."""
        return self.rol == 'vendedor'
    
    @classmethod
    def crear_usuario(cls, username, password, rol, email=None, nombre=None, apellido=None):
        """Crear un nuevo usuario."""
        usuario = cls(
            username=username,
            email=email,
            nombre=nombre,
            apellido=apellido,
            rol=rol
        )
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()
        return usuario


@login_manager.user_loader
def load_user(id):
    """Función requerida por Flask-Login para cargar un usuario."""
    return Usuario.query.get(int(id))