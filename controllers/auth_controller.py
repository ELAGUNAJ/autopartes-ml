from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from app import db
from app.models.usuario import Usuario

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Formularios
class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

class RegistroForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    nombre = StringField('Nombre', validators=[DataRequired()])
    apellido = StringField('Apellido', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', 
                                    validators=[DataRequired(), EqualTo('password')])
    rol = SelectField('Rol', choices=[('vendedor', 'Vendedor'), ('admin', 'Administrador')])
    submit = SubmitField('Registrar')
    
    def validate_username(self, username):
        user = Usuario.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nombre de usuario ya está en uso. Por favor, elige otro.')
    
    def validate_email(self, email):
        user = Usuario.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este correo electrónico ya está registrado. Por favor, usa otro.')

class CambiarPasswordForm(FlaskForm):
    current_password = PasswordField('Contraseña Actual', validators=[DataRequired()])
    new_password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Nueva Contraseña', 
                                    validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Cambiar Contraseña')

# Rutas
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard.index')
            return redirect(next_page)
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('auth/login.html', form=form, title='Iniciar Sesión')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/registro', methods=['GET', 'POST'])
@login_required
def registro():
    # Solo los administradores pueden registrar nuevos usuarios
    if not current_user.is_admin():
        flash('No tienes permisos para registrar nuevos usuarios', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = RegistroForm()
    if form.validate_on_submit():
        usuario = Usuario(
            username=form.username.data,
            email=form.email.data,
            nombre=form.nombre.data,
            apellido=form.apellido.data,
            rol=form.rol.data
        )
        usuario.set_password(form.password.data)
        
        db.session.add(usuario)
        db.session.commit()
        
        flash('Usuario registrado correctamente', 'success')
        return redirect(url_for('auth.usuarios'))
    
    return render_template('auth/registro.html', form=form, title='Registrar Usuario')

@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    form = CambiarPasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Contraseña actualizada correctamente', 'success')
            return redirect(url_for('auth.perfil'))
        else:
            flash('La contraseña actual es incorrecta', 'danger')
    
    return render_template('auth/perfil.html', form=form, title='Mi Perfil')

@auth_bp.route('/usuarios')
@login_required
def usuarios():
    if not current_user.is_admin():
        flash('No tienes permisos para ver esta página', 'danger')
        return redirect(url_for('dashboard.index'))
    
    usuarios = Usuario.query.all()
    return render_template('auth/usuarios.html', usuarios=usuarios, title='Gestión de Usuarios')

@auth_bp.route('/usuarios/<int:user_id>/activar', methods=['POST'])
@login_required
def activar_usuario(user_id):
    if not current_user.is_admin():
        flash('No tienes permisos para realizar esta acción', 'danger')
        return redirect(url_for('dashboard.index'))
    
    usuario = Usuario.query.get_or_404(user_id)
    usuario.activo = True
    db.session.commit()
    
    flash(f'Usuario {usuario.username} activado correctamente', 'success')
    return redirect(url_for('auth.usuarios'))

@auth_bp.route('/usuarios/<int:user_id>/desactivar', methods=['POST'])
@login_required
def desactivar_usuario(user_id):
    if not current_user.is_admin():
        flash('No tienes permisos para realizar esta acción', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if current_user.id == user_id:
        flash('No puedes desactivar tu propio usuario', 'danger')
        return redirect(url_for('auth.usuarios'))
    
    usuario = Usuario.query.get_or_404(user_id)
    usuario.activo = False
    db.session.commit()
    
    flash(f'Usuario {usuario.username} desactivado correctamente', 'success')
    return redirect(url_for('auth.usuarios'))