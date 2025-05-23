class Config:
    """Configuración base."""
    SECRET_KEY = 'tu_clave_secreta_super_segura'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

class DevelopmentConfig(Config):
    """Configuración de desarrollo."""
    DEBUG = True
<<<<<<< HEAD
    # SQLite para simplificar (no requiere configuración de PostgreSQL)
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    # Si prefieres PostgreSQL (cambia las credenciales):
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:12345678@localhost/autopartes_ML'
=======
    SQLALCHEMY_DATABASE_URI = 'postgresql://usuario:contraseña@localhost/autopartes_ml_dev'
    # Alternativa si no tienes PostgreSQL configurado:
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
>>>>>>> 32695fbfee91b1bd0b2d97bc0b6297d99ac5a67c
    

class ProductionConfig(Config):
    """Configuración de producción."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://usuario:contraseña@localhost/autopartes_ml_prod'
<<<<<<< HEAD
=======
    # Usar variables de entorno en producción:
    # SECRET_KEY = os.environ.get('SECRET_KEY')
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
>>>>>>> 32695fbfee91b1bd0b2d97bc0b6297d99ac5a67c
    

class TestingConfig(Config):
    """Configuración de pruebas."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False