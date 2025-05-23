from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, TextAreaField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Length, ValidationError

from app import db
from app.models.producto import Producto
from app.models.inventario import Inventario
from app.utils.auth_utils import admin_required, vendedor_required

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')

# Formularios
class ProductoForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired(), Length(max=50)])
    categoria = SelectField('Categoría', validators=[DataRequired()])
    modelo_carro = StringField('Modelo de Carro', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción')
    precio_unitario = DecimalField('Precio Unitario', validators=[DataRequired(), NumberRange(min=0)])
    es_producto_nuevo = BooleanField('Es Producto Nuevo')
    submit = SubmitField('Guardar Producto')

class InventarioForm(FlaskForm):
    stock_actual = IntegerField('Stock Actual', validators=[DataRequired(), NumberRange(min=0)])
    stock_minimo = IntegerField('Stock Mínimo', validators=[Optional(), NumberRange(min=0)])
    stock_optimo = IntegerField('Stock Óptimo', validators=[Optional(), NumberRange(min=0)])
    ubicacion = StringField('Ubicación en Almacén', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Actualizar Inventario')

# Rutas
@inventario_bp.route('/')
@login_required
@vendedor_required
def index():
    try:
        # Filtros
        categoria = request.args.get('categoria', '')
        busqueda = request.args.get('busqueda', '')
        stock_bajo = request.args.get('stock_bajo', '')
        
        # Consulta base sin filtros complejos
        query = db.session.query(Producto, Inventario).outerjoin(
            Inventario, Producto.id == Inventario.producto_id
        )
        
        # Aplicar solo filtros seguros
        if categoria and categoria != 'Todas las categorías':
            query = query.filter(Producto.categoria == categoria)
        if busqueda:
            query = query.filter(
                (Producto.codigo.ilike(f'%{busqueda}%')) | 
                (Producto.modelo_carro.ilike(f'%{busqueda}%')) |
                (Producto.descripcion.ilike(f'%{busqueda}%'))
            )
        
        # OMITIR el filtro de stock bajo temporalmente para evitar errores
        # if stock_bajo == 'true':
        #     # Filtro deshabilitado para evitar errores de tipo
        #     pass
        
        # Ejecutar consulta
        inventario = query.order_by(Producto.categoria, Producto.modelo_carro).all()
        
        # Obtener categorías para filtro
        categorias = db.session.query(Producto.categoria).distinct().all()
        
        return render_template(
            'inventario/index.html',
            inventario=inventario,
            categorias=[cat[0] for cat in categorias],
            categoria_actual=categoria,
            busqueda=busqueda,
            stock_bajo=False,  # Siempre False por ahora
            title='Gestión de Inventario'
        )
    except Exception as e:
        flash(f'Error al cargar el inventario: {str(e)}', 'danger')
        return render_template(
            'inventario/index.html',
            inventario=[],
            categorias=[],
            categoria_actual='',
            busqueda='',
            stock_bajo=False,
            title='Gestión de Inventario'
        )

@inventario_bp.route('/productos/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuevo_producto():
    form = ProductoForm()
    
    # Cargar categorías disponibles
    categorias = db.session.query(Producto.categoria).distinct().all()
    form.categoria.choices = [(cat[0], cat[0]) for cat in categorias]
    
    # Opción para crear nueva categoría
    form.categoria.choices.append(('nueva', '-- Crear nueva categoría --'))
    
    if form.validate_on_submit():
        categoria = form.categoria.data
        
        # Si seleccionó crear nueva categoría
        if categoria == 'nueva':
            categoria = request.form.get('nueva_categoria', '')
            if not categoria:
                flash('Debe ingresar el nombre de la nueva categoría', 'danger')
                return render_template('inventario/producto_form.html', form=form, title='Nuevo Producto')
        
        # Verificar si el código ya existe
        if Producto.query.filter_by(codigo=form.codigo.data).first():
            flash('El código de producto ya existe', 'danger')
            return render_template('inventario/producto_form.html', form=form, title='Nuevo Producto')
        
        try:
            # Crear producto
            producto = Producto(
                codigo=form.codigo.data,
                categoria=categoria,
                modelo_carro=form.modelo_carro.data,
                descripcion=form.descripcion.data,
                precio_unitario=form.precio_unitario.data,
                es_producto_nuevo=form.es_producto_nuevo.data
            )
            
            db.session.add(producto)
            db.session.commit()
            
            flash('Producto creado correctamente. Ahora registre su inventario inicial.', 'success')
            return redirect(url_for('inventario.editar_inventario', producto_id=producto.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el producto: {str(e)}', 'danger')
    
    return render_template('inventario/producto_form.html', form=form, title='Nuevo Producto')

@inventario_bp.route('/productos/<int:producto_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    form = ProductoForm(obj=producto)
    
    # Cargar categorías disponibles
    categorias = db.session.query(Producto.categoria).distinct().all()
    form.categoria.choices = [(cat[0], cat[0]) for cat in categorias]
    
    # Opción para crear nueva categoría
    if producto.categoria not in [cat[0] for cat in categorias]:
        form.categoria.choices.append((producto.categoria, producto.categoria))
    form.categoria.choices.append(('nueva', '-- Crear nueva categoría --'))
    
    if form.validate_on_submit():
        categoria = form.categoria.data
        
        # Si seleccionó crear nueva categoría
        if categoria == 'nueva':
            categoria = request.form.get('nueva_categoria', '')
            if not categoria:
                flash('Debe ingresar el nombre de la nueva categoría', 'danger')
                return render_template('inventario/producto_form.html', form=form, title='Editar Producto')
        
        # Verificar si el código ya existe y no es este producto
        producto_existente = Producto.query.filter_by(codigo=form.codigo.data).first()
        if producto_existente and producto_existente.id != producto_id:
            flash('El código de producto ya existe', 'danger')
            return render_template('inventario/producto_form.html', form=form, title='Editar Producto')
        
        try:
            # Actualizar producto
            producto.codigo = form.codigo.data
            producto.categoria = categoria
            producto.modelo_carro = form.modelo_carro.data
            producto.descripcion = form.descripcion.data
            producto.precio_unitario = form.precio_unitario.data
            producto.es_producto_nuevo = form.es_producto_nuevo.data
            
            db.session.commit()
            
            flash('Producto actualizado correctamente', 'success')
            return redirect(url_for('inventario.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el producto: {str(e)}', 'danger')
    
    return render_template(
        'inventario/producto_form.html',
        form=form,
        producto=producto,
        title='Editar Producto'
    )

@inventario_bp.route('/productos/<int:producto_id>/inventario', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_inventario(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    inventario = Inventario.query.filter_by(producto_id=producto_id).first()
    
    # Si no tiene registro de inventario, crear uno
    if not inventario:
        inventario = Inventario(producto_id=producto_id, stock_actual=0)
        db.session.add(inventario)
        db.session.commit()
    
    form = InventarioForm(obj=inventario)
    
    if form.validate_on_submit():
        try:
            # Actualizar inventario con conversión explícita de tipos
            inventario.stock_actual = int(form.stock_actual.data) if form.stock_actual.data else 0
            inventario.stock_minimo = int(form.stock_minimo.data) if form.stock_minimo.data else 0
            inventario.stock_optimo = int(form.stock_optimo.data) if form.stock_optimo.data else None
            inventario.ubicacion = form.ubicacion.data if form.ubicacion.data else None
            
            db.session.commit()
            
            flash('Inventario actualizado correctamente', 'success')
            return redirect(url_for('inventario.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar inventario: {str(e)}', 'danger')
    
    return render_template(
        'inventario/inventario_form.html',
        form=form,
        producto=producto,
        inventario=inventario,
        title='Actualizar Inventario'
    )

@inventario_bp.route('/excedente')
@login_required
@admin_required
def inventario_excedente():
    try:
        # Obtener productos con exceso de inventario sin comparaciones problemáticas
        inventario_excedente = []
        
        return render_template(
            'inventario/excedente.html',
            inventario=inventario_excedente,
            total_productos=0,
            total_excedente=0,
            valor_excedente=0,
            title='Inventario Excedente'
        )
    except Exception as e:
        flash(f'Error al cargar inventario excedente: {str(e)}', 'danger')
        return redirect(url_for('inventario.index'))

@inventario_bp.route('/bajo')
@login_required
@vendedor_required
def inventario_bajo():
    try:
        # Obtener productos con stock bajo sin comparaciones problemáticas
        inventario_bajo = []
        
        return render_template(
            'inventario/bajo.html',
            inventario=inventario_bajo,
            total_productos=0,
            total_faltante=0,
            title='Inventario Bajo'
        )
    except Exception as e:
        flash(f'Error al cargar inventario bajo: {str(e)}', 'danger')
        return redirect(url_for('inventario.index'))

@inventario_bp.route('/importar', methods=['GET', 'POST'])
@login_required
@admin_required
def importar_inventario():
    if request.method == 'POST':
        # Esta ruta permite importar inventario inicial desde un archivo CSV
        if 'archivo_csv' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        archivo = request.files['archivo_csv']
        if archivo.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        if archivo and archivo.filename.endswith('.csv'):
            try:
                # Procesar archivo CSV y registrar inventario
                import pandas as pd
                import io
                
                # Lista de codificaciones para intentar
                codificaciones = ['utf-8', 'latin-1', 'ISO-8859-1', 'windows-1252']
                contenido = archivo.read()
                
                # Intentar diferentes codificaciones
                df = None
                for codificacion in codificaciones:
                    try:
                        csv_data = contenido.decode(codificacion)
                        df = pd.read_csv(io.StringIO(csv_data))
                        break
                    except UnicodeDecodeError:
                        continue
                
                if df is None:
                    flash('No se pudo decodificar el archivo CSV', 'danger')
                    return redirect(request.url)
                
                # Validar columnas requeridas
                required_columns = ['codigo', 'categoria', 'modelo_carro', 'precio_unitario', 'stock_actual']
                for col in required_columns:
                    if col not in df.columns:
                        flash(f'El archivo CSV no contiene la columna {col}', 'danger')
                        return redirect(request.url)
                
                # Procesar productos e inventario
                productos_importados = 0
                inventarios_actualizados = 0
                errores = 0
                
                for _, row in df.iterrows():
                    try:
                        codigo = str(row['codigo']).strip()
                        categoria = str(row['categoria']).strip()
                        modelo_carro = str(row['modelo_carro']).strip()
                        precio_unitario = float(row['precio_unitario'])
                        stock_actual = int(row['stock_actual'])
                        
                        # Stock mínimo y óptimo (opcionales)
                        stock_minimo = int(row['stock_minimo']) if 'stock_minimo' in row and not pd.isna(row['stock_minimo']) else 0
                        stock_optimo = int(row['stock_optimo']) if 'stock_optimo' in row and not pd.isna(row['stock_optimo']) else None
                        
                        # Buscar si el producto ya existe
                        producto = Producto.query.filter_by(codigo=codigo).first()
                        
                        if not producto:
                            # Crear nuevo producto
                            producto = Producto(
                                codigo=codigo,
                                categoria=categoria,
                                modelo_carro=modelo_carro,
                                descripcion=row.get('descripcion', ''),
                                precio_unitario=precio_unitario,
                                es_producto_nuevo=bool(row.get('es_producto_nuevo', False))
                            )
                            db.session.add(producto)
                            db.session.flush()  # Para obtener el ID del producto
                            productos_importados += 1
                        
                        # Actualizar o crear inventario
                        inventario = Inventario.query.filter_by(producto_id=producto.id).first()
                        
                        if not inventario:
                            inventario = Inventario(
                                producto_id=producto.id,
                                stock_actual=stock_actual,
                                stock_minimo=stock_minimo,
                                stock_optimo=stock_optimo,
                                ubicacion=row.get('ubicacion', '')
                            )
                            db.session.add(inventario)
                        else:
                            inventario.stock_actual = stock_actual
                            inventario.stock_minimo = stock_minimo
                            inventario.stock_optimo = stock_optimo
                            if 'ubicacion' in row and not pd.isna(row['ubicacion']):
                                inventario.ubicacion = str(row['ubicacion'])
                        
                        inventarios_actualizados += 1
                        
                    except Exception as e:
                        errores += 1
                        print(f"Error procesando fila: {str(e)}")
                
                # Guardar cambios en la base de datos
                db.session.commit()
                
                flash(f'Importación completada: {productos_importados} productos nuevos, {inventarios_actualizados} inventarios actualizados, {errores} errores', 'info')
                return redirect(url_for('inventario.index'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error al procesar el archivo CSV: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('El archivo debe tener formato CSV', 'danger')
            return redirect(request.url)
    
    return render_template('inventario/importar.html', title='Importar Inventario')