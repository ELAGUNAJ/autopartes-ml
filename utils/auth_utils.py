from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """Decorador para requerir que el usuario sea administrador."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Acceso denegado. Se requieren permisos de administrador.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def vendedor_required(f):
    """Decorador para requerir que el usuario sea vendedor o administrador."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (not current_user.is_vendedor() and not current_user.is_admin()):
            flash('Acceso denegado. Se requieren permisos de vendedor.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def user_has_permission(user, required_role):
    """Verificar si un usuario tiene los permisos requeridos."""
    if not user or not user.is_authenticated:
        return False
    
    if required_role == 'admin':
        return user.is_admin()
    elif required_role == 'vendedor':
        return user.is_vendedor() or user.is_admin()
    
    return False