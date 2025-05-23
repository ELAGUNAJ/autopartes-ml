class Config:
    """Configuración base."""
    SECRET_KEY = 'tu_clave_secreta_super_segura'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

class DevelopmentConfig(Config):
    """Configuración de desarrollo."""
    DEBUG = True
    # SQLite para simplificar (no requiere configuración de PostgreSQL)
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    # Si prefieres PostgreSQL (cambia las credenciales):
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:12345678@localhost/autopartes_ML'
    

class ProductionConfig(Config):
    """Configuración de producción."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://usuario:contraseña@localhost/autopartes_ml_prod'
    

class TestingConfig(Config):
    """Configuración de pruebas."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False