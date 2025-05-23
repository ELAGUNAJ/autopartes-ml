from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional

from app import db
from app.models.producto import Producto
from app.models.venta import Venta
from app.models.inventario import Inventario
from app.utils.auth_utils import vendedor_required
from app.utils.date_utils import str_a_fecha, fecha_a_str
from datetime import datetime, timedelta

ventas_bp = Blueprint('ventas', __name__, url_prefix='/ventas')

# Formularios
class RegistroVentaForm(FlaskForm):
    producto_id = SelectField('Producto', coerce=int, validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[DataRequired(), NumberRange(min=1)])
    precio_unitario = DecimalField('Precio Unitario', validators=[DataRequired(), NumberRange(min=0)])
    fecha_venta = DateField('Fecha de Venta', validators=[Optional()], default=datetime.today)
    submit = SubmitField('Registrar Venta')

class FiltroVentasForm(FlaskForm):
    categoria = SelectField('Categoría', validators=[Optional()])
    modelo_carro = SelectField('Modelo de Carro', validators=[Optional()])
    fecha_inicio = DateField('Fecha Inicio', validators=[Optional()])
    fecha_fin = DateField('Fecha Fin', validators=[Optional()])
    submit = SubmitField('Filtrar')

# Rutas
@ventas_bp.route('/')
@login_required
@vendedor_required
def index():
    form = FiltroVentasForm()
    
    # Opciones para los filtros
    categorias = [(c, c) for c in db.session.query(Producto.categoria).distinct()]
    categorias.insert(0, ('', 'Todas las categorías'))
    form.categoria.choices = categorias
    
    modelos = [(m, m) for m in db.session.query(Producto.modelo_carro).distinct()]
    modelos.insert(0, ('', 'Todos los modelos'))
    form.modelo_carro.choices = modelos
    
    # Filtros
    categoria = request.args.get('categoria', '')
    modelo_carro = request.args.get('modelo_carro', '')
    fecha_inicio_str = request.args.get('fecha_inicio', '')
    fecha_fin_str = request.args.get('fecha_fin', '')
    
    fecha_inicio = str_a_fecha(fecha_inicio_str) if fecha_inicio_str else datetime.today() - timedelta(days=30)
    fecha_fin = str_a_fecha(fecha_fin_str) if fecha_fin_str else datetime.today()
    
    # Construir consulta base
    query = Venta.query.join(Producto, Venta.producto_id == Producto.id)
    
    # Aplicar filtros
    if categoria:
        query = query.filter(Producto.categoria == categoria)
    if modelo_carro:
        query = query.filter(Producto.modelo_carro == modelo_carro)
    
    query = query.filter(Venta.fecha_venta >= fecha_inicio, Venta.fecha_venta <= fecha_fin)
    
    # Ejecutar consulta
    ventas = query.order_by(Venta.fecha_venta.desc()).all()
    
    # Calcular totales
    total_ventas = sum(float(venta.precio_total) for venta in ventas)
    cantidad_total = sum(venta.cantidad for venta in ventas)
    
    return render_template(
        'ventas/index.html',
        ventas=ventas,
        form=form,
        total_ventas=total_ventas,
        cantidad_total=cantidad_total,
        fecha_inicio=fecha_a_str(fecha_inicio) if fecha_inicio else '',
        fecha_fin=fecha_a_str(fecha_fin) if fecha_fin else '',
        title='Registro de Ventas'
    )

@ventas_bp.route('/registrar', methods=['GET', 'POST'])
@login_required
@vendedor_required
def registrar():
    form = RegistroVentaForm()
    
    # Obtener productos disponibles para venta (con stock > 0)
    productos_con_stock = db.session.query(Producto, Inventario.stock_actual).join(
        Inventario, Producto.id == Inventario.producto_id
    ).filter(Inventario.stock_actual > 0).all()
    
    # Crear opciones para el select de productos
    opciones_producto = [(p.id, f"{p.codigo} - {p.categoria} {p.modelo_carro} (Stock: {stock})") 
                         for p, stock in productos_con_stock]
    form.producto_id.choices = opciones_producto
    
    if form.validate_on_submit():
        producto_id = form.producto_id.data
        cantidad = form.cantidad.data
        precio_unitario = form.precio_unitario.data
        fecha_venta = form.fecha_venta.data or datetime.today()
        
        # Verificar stock disponible
        inventario = Inventario.query.filter_by(producto_id=producto_id).first()
        if not inventario or inventario.stock_actual < cantidad:
            flash('Stock insuficiente para completar la venta', 'danger')
            return redirect(url_for('ventas.registrar'))
        
        # Calcular precio total
        precio_total = precio_unitario * cantidad
        
        # Registrar venta
        venta = Venta(
            producto_id=producto_id,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            precio_total=precio_total,
            fecha_venta=fecha_venta,
            usuario_id=current_user.id
        )
        
        # Actualizar inventario
        inventario.stock_actual -= cantidad
        
        # Guardar cambios
        db.session.add(venta)
        db.session.commit()
        
        flash('Venta registrada correctamente', 'success')
        return redirect(url_for('ventas.index'))
    
    return render_template('ventas/registrar.html', form=form, title='Registrar Venta')

@ventas_bp.route('/detalle/<int:venta_id>')
@login_required
@vendedor_required
def detalle(venta_id):
    venta = Venta.query.get_or_404(venta_id)
    producto = Producto.query.get(venta.producto_id)
    
    return render_template(
        'ventas/detalle.html',
        venta=venta,
        producto=producto,
        title='Detalle de Venta'
    )

@ventas_bp.route('/api/productos/<int:producto_id>')
@login_required
@vendedor_required
def api_producto_info(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    inventario = Inventario.query.filter_by(producto_id=producto_id).first()
    
    return jsonify({
        'id': producto.id,
        'codigo': producto.codigo,
        'categoria': producto.categoria,
        'modelo_carro': producto.modelo_carro,
        'precio_unitario': float(producto.precio_unitario),
        'stock_actual': inventario.stock_actual if inventario else 0
    })

@ventas_bp.route('/bulk-import', methods=['GET', 'POST'])
@login_required
@vendedor_required
def importar_ventas():
    if request.method == 'POST':
        # Esta ruta permite importar ventas históricas desde un archivo CSV
        if 'archivo_csv' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        archivo = request.files['archivo_csv']
        if archivo.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        if archivo and archivo.filename.endswith('.csv'):
            try:
                # Procesar archivo CSV y registrar ventas
                # Este es un ejemplo simplificado
                import pandas as pd
                import io
                
                # Leer CSV
                csv_data = archivo.read().decode('utf-8')
                df = pd.read_csv(io.StringIO(csv_data))
                
                # Validar columnas requeridas
                required_columns = ['producto_id', 'cantidad', 'precio_unitario', 'fecha_venta']
                for col in required_columns:
                    if col not in df.columns:
                        flash(f'El archivo CSV no contiene la columna {col}', 'danger')
                        return redirect(request.url)
                
                # Procesar ventas
                ventas_importadas = 0
                errores = 0
                
                for _, row in df.iterrows():
                    try:
                        producto_id = int(row['producto_id'])
                        cantidad = int(row['cantidad'])
                        precio_unitario = float(row['precio_unitario'])
                        fecha_venta = str_a_fecha(row['fecha_venta'])
                        
                        # Validar producto y stock
                        producto = Producto.query.get(producto_id)
                        if not producto:
                            errores += 1
                            continue
                        
                        # Registrar venta histórica
                        precio_total = precio_unitario * cantidad
                        venta = Venta(
                            producto_id=producto_id,
                            cantidad=cantidad,
                            precio_unitario=precio_unitario,
                            precio_total=precio_total,
                            fecha_venta=fecha_venta,
                            usuario_id=current_user.id
                        )
                        
                        db.session.add(venta)
                        ventas_importadas += 1
                        
                    except Exception as e:
                        errores += 1
                
                # Guardar cambios en la base de datos
                db.session.commit()
                
                flash(f'Importación completada: {ventas_importadas} ventas importadas, {errores} errores', 'info')
                return redirect(url_for('ventas.index'))
                
            except Exception as e:
                flash(f'Error al procesar el archivo CSV: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('El archivo debe tener formato CSV', 'danger')
            return redirect(request.url)
    
    return render_template('ventas/importar.html', title='Importar Ventas Históricas')