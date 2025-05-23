import os
import sys
from flask import redirect, url_for
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Añadir directorio raíz al sys.path para importaciones absolutas
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Inicialización de extensiones
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_name='default'):
    # Especificar explícitamente la carpeta de plantillas como 'views'
    app = Flask(__name__, template_folder='views')
    
    # Configuración
    try:
        if config_name == 'default':
            from config import DevelopmentConfig
            app.config.from_object(DevelopmentConfig)
        elif config_name == 'production':
            from config import ProductionConfig
            app.config.from_object(ProductionConfig)
        elif config_name == 'testing':
            from config import TestingConfig
            app.config.from_object(TestingConfig)
    except ImportError:
        # Configuración fallback si no se puede importar config.py
        print("ADVERTENCIA: No se pudo importar el módulo config. Usando configuración básica.")
        app.config['SECRET_KEY'] = 'clave_secreta_fallback'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
        app.config['DEBUG'] = True
    
    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configurar Login Manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'
    
    # Registrar blueprints
    with app.app_context():
        try:
            # Intentar importar y registrar blueprints
            try:
                from app.controllers.auth_controller import auth_bp
                app.register_blueprint(auth_bp)
                print("Blueprint auth_bp registrado correctamente")
            except ImportError as e:
                print(f"Error al registrar auth_bp: {e}")
            
            try:
                from app.controllers.ventas_controller import ventas_bp
                app.register_blueprint(ventas_bp)
                print("Blueprint ventas_bp registrado correctamente")
            except ImportError as e:
                print(f"Error al registrar ventas_bp: {e}")
            
            try:
                from app.controllers.inventario_controller import inventario_bp
                app.register_blueprint(inventario_bp)
                print("Blueprint inventario_bp registrado correctamente")
            except ImportError as e:
                print(f"Error al registrar inventario_bp: {e}")
            
            try:
                from app.controllers.ml_controller import ml_bp
                app.register_blueprint(ml_bp)
                print("Blueprint ml_bp registrado correctamente")
            except ImportError as e:
                print(f"Error al registrar ml_bp: {e}")
            
            try:
                from app.controllers.dashboard_controller import dashboard_bp
                app.register_blueprint(dashboard_bp)
                print("Blueprint dashboard_bp registrado correctamente")
            except ImportError as e:
                print(f"Error al registrar dashboard_bp: {e}")
                
            @app.route('/')
            def index():
            # Redirigir a la página de login en lugar de mostrar un mensaje
                return redirect(url_for('auth.login')) 
            
        except Exception as e:
            print(f"Error general al configurar la aplicación: {e}")
            
            # Ruta de fallback si hay errores
            @app.route('/')
            def index_fallback():
                return "Aplicación en modo fallback. Hubo errores al configurar la aplicación."
    
    # Crear directorio para modelos ML si no existe
    os.makedirs(os.path.join(app.instance_path, 'ml_models'), exist_ok=True)
    
    return app