class Config:
    """Configuración base."""
    SECRET_KEY = 'tu_clave_secreta_super_segura'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

class DevelopmentConfig(Config):
    """Configuración de desarrollo."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://usuario:contraseña@localhost/autopartes_ml_dev'
    # Alternativa si no tienes PostgreSQL configurado:
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    

class ProductionConfig(Config):
    """Configuración de producción."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://usuario:contraseña@localhost/autopartes_ml_prod'
    # Usar variables de entorno en producción:
    # SECRET_KEY = os.environ.get('SECRET_KEY')
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    

class TestingConfig(Config):
    """Configuración de pruebas."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False