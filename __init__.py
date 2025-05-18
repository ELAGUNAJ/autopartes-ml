from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Inicialización de extensiones
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__, 
                template_folder='views',
                static_folder='static')
    
    # Configuración
    if config_name == 'default':
        app.config.from_object('config.DevelopmentConfig')
    elif config_name == 'production':
        app.config.from_object('config.ProductionConfig')
    elif config_name == 'testing':
        app.config.from_object('config.TestingConfig')
    
    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Registrar blueprints
    with app.app_context():
        try:
            from app.controllers.auth_controller import auth_bp
            from app.controllers.ventas_controller import ventas_bp
            from app.controllers.inventario_controller import inventario_bp
            from app.controllers.ml_controller import ml_bp
            from app.controllers.dashboard_controller import dashboard_bp
            
            app.register_blueprint(auth_bp)
            app.register_blueprint(ventas_bp)
            app.register_blueprint(inventario_bp)
            app.register_blueprint(ml_bp)
            app.register_blueprint(dashboard_bp)
        except ImportError as e:
            print(f"Error al importar blueprints: {e}")
    
    return app