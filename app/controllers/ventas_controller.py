from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm  # Asegúrate de que esta línea esté presente
from wtforms import StringField, IntegerField, DecimalField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Length
from datetime import datetime, timedelta
import csv
from io import TextIOWrapper
import os

from app import db
from app.models.producto import Producto
from app.models.venta import Venta
from app.utils.auth_utils import admin_required, vendedor_required

# Definir formulario para nueva venta
class VentaForm(FlaskForm):
    producto_id = SelectField('Producto', validators=[DataRequired()], coerce=int)
    cantidad = IntegerField('Cantidad', validators=[DataRequired(), NumberRange(min=1)], default=1)
    precio_unitario = DecimalField('Precio Unitario', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Registrar Venta')

# Crear blueprint de ventas
ventas_bp = Blueprint('ventas', __name__, url_prefix='/ventas')

@ventas_bp.route('/')
@login_required
@vendedor_required
def index():
    try:
        # Crear un formulario vacío para la plantilla
        form = VentaForm()
        
        # Cargar opciones de productos para el formulario
        try:
            productos = db.session.query(Producto).all()
            opciones_productos = []
            for p in productos:
                # Construir la etiqueta con verificación de atributos
                codigo = getattr(p, 'codigo', 'Sin código')
                
                # Verificar si existe el atributo modelo_carro
                if hasattr(p, 'modelo_carro'):
                    modelo = p.modelo_carro
                else:
                    modelo = ''
                
                # Verificar si existe el atributo categoria
                if hasattr(p, 'categoria'):
                    categoria = p.categoria
                else:
                    categoria = ''
                
                etiqueta = f"{codigo}"
                if modelo:
                    etiqueta += f" - {modelo}"
                if categoria:
                    etiqueta += f" ({categoria})"
                
                opciones_productos.append((p.id, etiqueta))
            
            form.producto_id.choices = opciones_productos
        except Exception as e:
            # Si hay error, usar lista vacía
            form.producto_id.choices = []
            print(f"Error al cargar productos: {str(e)}")
        
        # Obtener parámetros de filtro
        categoria = request.args.get('categoria', '')
        modelo = request.args.get('modelo', '')
        fecha_inicio_str = request.args.get('fecha_inicio', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        fecha_fin_str = request.args.get('fecha_fin', datetime.now().strftime('%Y-%m-%d'))
        
        # Convertir fechas
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
            # Ajustar fecha_fin para incluir todo el día
            fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59)
        except ValueError:
            # Si hay un error en el formato de fecha, usar valores predeterminados
            fecha_inicio = datetime.now() - timedelta(days=30)
            fecha_fin = datetime.now()
        
        # Consulta base de ventas
        query = db.session.query(
            Venta, Producto
        ).join(
            Producto, Venta.producto_id == Producto.id
        ).filter(
            Venta.fecha_venta.between(fecha_inicio, fecha_fin)  # Cambio aquí: fecha_venta en lugar de fecha
        )
        
        # Aplicar filtros adicionales si existen los atributos
        if hasattr(Producto, 'categoria') and categoria:
            query = query.filter(Producto.categoria == categoria)
        if hasattr(Producto, 'modelo_carro') and modelo:
            query = query.filter(Producto.modelo_carro.ilike(f'%{modelo}%'))
        
        # Obtener ventas
        ventas = query.order_by(Venta.fecha_venta.desc()).all()  # Cambio aquí: fecha_venta en lugar de fecha
        
        # Calcular totales
        total_ventas = sum(venta.total for venta, _ in ventas)
        total_productos = sum(venta.cantidad for venta, _ in ventas)
        total_transacciones = len(ventas)
        
        # Obtener categorías y modelos para filtros si existen los atributos
        categorias = []
        modelos = []
        
        if hasattr(Producto, 'categoria'):
            categorias = db.session.query(Producto.categoria).distinct().all()
        
        if hasattr(Producto, 'modelo_carro'):
            modelos = db.session.query(Producto.modelo_carro).distinct().all()
        
        return render_template(
            'ventas/index.html',
            ventas=ventas,
            total_ventas=total_ventas,
            total_productos=total_productos,
            total_transacciones=total_transacciones,
            categorias=[cat[0] for cat in categorias] if categorias else [],
            modelos=[m[0] for m in modelos] if modelos else [],
            categoria_actual=categoria,
            modelo_actual=modelo,
            fecha_inicio=fecha_inicio_str,
            fecha_fin=fecha_fin_str,
            title='Gestión de Ventas',
            form=form
        )
    except Exception as e:
        flash(f'Error al cargar las ventas: {str(e)}', 'danger')
        
        # Crea un formulario vacío para la plantilla incluso en caso de error
        form = VentaForm()
        form.producto_id.choices = []
            
        return render_template(
            'ventas/index.html',
            ventas=[],
            total_ventas=0,
            total_productos=0,
            total_transacciones=0,
            categorias=[],
            modelos=[],
            categoria_actual='',
            modelo_actual='',
            fecha_inicio=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            fecha_fin=datetime.now().strftime('%Y-%m-%d'),
            title='Gestión de Ventas',
            error=str(e),
            form=form
        )

@ventas_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
@vendedor_required
def nueva_venta():
    # Crear formulario y cargar productos disponibles
    form = VentaForm()
    productos = db.session.query(Producto).all()
    form.producto_id.choices = [(p.id, f'{p.codigo} - {p.modelo_carro} ({p.categoria})') for p in productos]
    
    if form.validate_on_submit():
        try:
            producto = db.session.query(Producto).get(form.producto_id.data)
            if not producto:
                flash('Producto no encontrado', 'danger')
                return redirect(url_for('ventas.nueva_venta'))
            
            # Verificar si hay stock suficiente
            inventario = db.session.query(db.models.Inventario).filter_by(producto_id=producto.id).first()
            if inventario and inventario.stock_actual < form.cantidad.data:
                flash(f'No hay suficiente stock disponible. Stock actual: {inventario.stock_actual}', 'warning')
                return redirect(url_for('ventas.nueva_venta'))
            
            # Crear nueva venta
            nueva_venta = Venta(
                fecha=datetime.now(),
                producto_id=producto.id,
                cantidad=form.cantidad.data,
                precio_unitario=form.precio_unitario.data,
                total=form.cantidad.data * form.precio_unitario.data,
                usuario_id=current_user.id
            )
            
            db.session.add(nueva_venta)
            
            # Actualizar inventario
            if inventario:
                inventario.stock_actual -= form.cantidad.data
            
            db.session.commit()
            
            flash('Venta registrada correctamente', 'success')
            return redirect(url_for('ventas.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar la venta: {str(e)}', 'danger')
    
    return render_template(
        'ventas/nueva_venta.html',
        form=form,
        title='Registrar Nueva Venta'
    )

@ventas_bp.route('/registrar', methods=['GET', 'POST'])
@login_required
@vendedor_required
def registrar():
    # Alias para la ruta nueva_venta
    return nueva_venta()

@ventas_bp.route('/<int:venta_id>/detalle')
@login_required
@vendedor_required
def detalle_venta(venta_id):
    try:
        venta, producto = db.session.query(Venta, Producto).join(
            Producto, Venta.producto_id == Producto.id
        ).filter(Venta.id == venta_id).first_or_404()
        
        return render_template(
            'ventas/detalle_venta.html',
            venta=venta,
            producto=producto,
            title='Detalle de Venta'
        )
    except Exception as e:
        flash(f'Error al cargar el detalle de la venta: {str(e)}', 'danger')
        return redirect(url_for('ventas.index'))

@ventas_bp.route('/<int:venta_id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_venta(venta_id):
    try:
        venta = db.session.query(Venta).get_or_404(venta_id)
        
        # Actualizar inventario
        inventario = db.session.query(db.models.Inventario).filter_by(producto_id=venta.producto_id).first()
        if inventario:
            inventario.stock_actual += venta.cantidad
        
        # Eliminar venta
        db.session.delete(venta)
        db.session.commit()
        
        flash('Venta eliminada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la venta: {str(e)}', 'danger')
    
    return redirect(url_for('ventas.index'))

@ventas_bp.route('/bulk-import', methods=['GET', 'POST'])
@login_required
@admin_required
def importar_ventas():
    # Crear un formulario pequeño solo para el CSRF token
    class ImportForm(FlaskForm):
        pass
    
    form = ImportForm()
    
    if request.method == 'POST':
        try:
            # Verificar si se envió un archivo
            if 'archivo_csv' not in request.files:
                flash('No se seleccionó ningún archivo', 'danger')
                return redirect(request.url)
                
            archivo = request.files['archivo_csv']
            
            # Verificar si se seleccionó un archivo
            if archivo.filename == '':
                flash('No se seleccionó ningún archivo', 'danger')
                return redirect(request.url)
                
            # Verificar si es un archivo CSV
            if not archivo.filename.endswith('.csv'):
                flash('El archivo debe tener extensión .csv', 'danger')
                return redirect(request.url)
            
            # Procesar opciones
            ignorar_encabezados = 'ignorar_encabezados' in request.form
            actualizar_existentes = 'actualizar_existentes' in request.form
            
            # Contadores para estadísticas
            filas_procesadas = 0
            ventas_creadas = 0
            errores = 0
            
            # Lista de codificaciones a intentar
            codificaciones = ['utf-8', 'latin-1', 'ISO-8859-1', 'windows-1252']
            contenido = archivo.read()  # Leer el contenido binario una vez
            
            # Bandera para saber si se logró procesar el archivo
            procesado = False
            
            for codificacion in codificaciones:
                try:
                    # Intentar decodificar con la codificación actual
                    archivo.seek(0)  # Rebobinar el archivo
                    csv_data = contenido.decode(codificacion)
                    
                    # Si llega aquí, la decodificación fue exitosa
                    import io
                    import csv
                    
                    # Crear un StringIO a partir de los datos decodificados
                    csv_io = io.StringIO(csv_data)
                    csv_reader = csv.reader(csv_io, delimiter=',')
                    
                    # Saltar la primera fila si se debe ignorar encabezados
                    if ignorar_encabezados:
                        next(csv_reader, None)
                    
                    # Procesar cada fila
                    for row in csv_reader:
                        try:
                            if len(row) < 5:
                                # La fila no tiene suficientes columnas
                                errores += 1
                                continue
                            
                            fecha_str, codigo_producto, categoria, cantidad_str, precio_str = row[0], row[1], row[2], row[3], row[4]
                            
                            # Convertir fecha (intentar múltiples formatos)
                            fecha = None
                            formatos_fecha = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']
                            for formato in formatos_fecha:
                                try:
                                    fecha = datetime.strptime(fecha_str, formato)
                                    break
                                except ValueError:
                                    continue
                            
                            # Si no se pudo convertir la fecha con ningún formato
                            if fecha is None:
                                errores += 1
                                continue
                            
                            # Convertir cantidad y precio
                            try:
                                cantidad = int(cantidad_str)
                                precio_unitario = float(precio_str.replace(',', '.'))
                            except ValueError:
                                errores += 1
                                continue
                            
                            # Buscar el producto
                            codigo_solo = codigo_producto.split(' - ')[0] if ' - ' in codigo_producto else codigo_producto
                            producto = db.session.query(Producto).filter_by(codigo=codigo_solo).first()
                            if not producto:
                                errores += 1
                                continue
                            
                            # Crear la venta
                            nueva_venta = Venta(
                                fecha_venta=fecha,  # Usar fecha_venta en lugar de fecha
                                producto_id=producto.id,
                                cantidad=cantidad,
                                precio_unitario=precio_unitario,
                                precio_total=cantidad * precio_unitario,  # Usar precio_total en lugar de total
                                usuario_id=current_user.id
                            )
                            
                            db.session.add(nueva_venta)
                            ventas_creadas += 1
                            filas_procesadas += 1
                            
                            # Actualizar inventario
                            try:
                                from app.models.inventario import Inventario
                                inventario = Inventario.query.filter_by(producto_id=producto.id).first()
                                if inventario:
                                    inventario.stock_actual -= cantidad
                            except Exception as e:
                                # Si hay un error al actualizar el inventario, lo registramos pero continuamos
                                print(f"Error al actualizar inventario: {str(e)}")
                            
                        except Exception as e:
                            errores += 1
                            print(f"Error procesando fila: {str(e)}")
                            continue
                    
                    # Si llega aquí, el procesamiento fue exitoso
                    procesado = True
                    break
                
                except UnicodeDecodeError:
                    # Si falla con esta codificación, intentar con la siguiente
                    continue
            
            # Si no se pudo procesar con ninguna codificación
            if not procesado:
                flash('No se pudo decodificar el archivo CSV. Intente guardarlo como UTF-8.', 'danger')
                return redirect(request.url)
            
            # Guardar cambios en la base de datos
            db.session.commit()
            
            # Mostrar mensaje de éxito
            flash(f'Importación completada: {filas_procesadas} filas procesadas, {ventas_creadas} ventas creadas, {errores} errores.', 'success')
            return redirect(url_for('ventas.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al importar ventas: {str(e)}', 'danger')
            return redirect(request.url)
    
    # Si es una solicitud GET, mostrar el formulario con el CSRF token
    return render_template('ventas/importar.html', 
                          title='Importar Ventas Históricas',
                          form=form)  # Pasar el formulario a la plantilla

@ventas_bp.route('/reporte')
@login_required
@vendedor_required
def reporte_ventas():
    try:
        # Obtener parámetros de filtro
        periodo = request.args.get('periodo', 'mensual')
        categoria = request.args.get('categoria', '')
        año = request.args.get('año', str(datetime.now().year))
        
        # Preparar datos para el gráfico según el período
        if periodo == 'mensual':
            # Ventas por mes del año seleccionado
            datos_ventas = []
            etiquetas = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            
            for mes in range(1, 13):
                fecha_inicio = datetime(int(año), mes, 1)
                if mes == 12:
                    fecha_fin = datetime(int(año) + 1, 1, 1) - timedelta(days=1)
                else:
                    fecha_fin = datetime(int(año), mes + 1, 1) - timedelta(days=1)
                
                # Consulta para el mes
                query = db.session.query(
                    db.func.sum(Venta.total)
                ).join(
                    Producto, Venta.producto_id == Producto.id
                ).filter(
                    Venta.fecha.between(fecha_inicio, fecha_fin)
                )
                
                if categoria:
                    query = query.filter(Producto.categoria == categoria)
                
                total_mes = query.scalar() or 0
                datos_ventas.append(float(total_mes))
        
        elif periodo == 'diario':
            # Ventas por día de los últimos 30 días
            datos_ventas = []
            etiquetas = []
            
            for dia in range(30, 0, -1):
                fecha = datetime.now() - timedelta(days=dia)
                etiquetas.append(fecha.strftime('%d/%m'))
                
                # Consulta para el día
                query = db.session.query(
                    db.func.sum(Venta.total)
                ).join(
                    Producto, Venta.producto_id == Producto.id
                ).filter(
                    db.func.date(Venta.fecha) == fecha.date()
                )
                
                if categoria:
                    query = query.filter(Producto.categoria == categoria)
                
                total_dia = query.scalar() or 0
                datos_ventas.append(float(total_dia))
        
        # Obtener categorías para filtro
        categorias = db.session.query(Producto.categoria).distinct().all()
        
        # Obtener años disponibles
        años = db.session.query(
            db.func.extract('year', Venta.fecha).distinct()
        ).order_by(
            db.func.extract('year', Venta.fecha).desc()
        ).all()
        
        return render_template(
            'ventas/reporte.html',
            datos_ventas=datos_ventas,
            etiquetas=etiquetas,
            categorias=[cat[0] for cat in categorias],
            años=[int(a[0]) for a in años],
            categoria_actual=categoria,
            periodo_actual=periodo,
            año_actual=int(año),
            title='Reporte de Ventas'
        )
    except Exception as e:
        flash(f'Error al generar el reporte: {str(e)}', 'danger')
        return redirect(url_for('ventas.index'))

@ventas_bp.route('/api/productos/<int:producto_id>')
@login_required
def api_producto_info(producto_id):
    try:
        producto = db.session.query(Producto).get_or_404(producto_id)
        inventario = db.session.query(db.models.Inventario).filter_by(producto_id=producto_id).first()
        
        return jsonify({
            'id': producto.id,
            'codigo': producto.codigo,
            'modelo': producto.modelo_carro,
            'categoria': producto.categoria,
            'precio': float(producto.precio_unitario),
            'stock_actual': inventario.stock_actual if inventario else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500