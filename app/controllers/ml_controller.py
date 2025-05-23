from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional

from app import db
from app.models.producto import Producto
from app.models.venta import Venta
from app.models.inventario import Inventario
from app.models.prediccion import Prediccion
from app.models.resultado import ResultadoComparativo
from app.utils.auth_utils import admin_required
from app.utils.date_utils import str_a_fecha
from app.ml.preprocessing import preparar_datos
from app.ml.feature_engineering import crear_features
from app.ml.model_training import entrenar_modelo
from app.ml.model_evaluation import evaluar_modelo
from app.ml.prediction import generar_predicciones

from datetime import datetime, timedelta
import joblib
import os
import pandas as pd
import numpy as np

ml_bp = Blueprint('ml', __name__, url_prefix='/ml')

# Formularios
class EntrenamientoForm(FlaskForm):
    fecha_inicio = DateField('Fecha Inicio', validators=[DataRequired()])
    fecha_fin = DateField('Fecha Fin', validators=[DataRequired()])
    submit = SubmitField('Entrenar Modelo')

class PrediccionForm(FlaskForm):
    categoria = SelectField('Categoría de Productos', validators=[Optional()])
    periodo_prediccion = SelectField('Período de Predicción', 
                                    choices=[
                                        ('7', 'Próximos 7 días'),
                                        ('14', 'Próximos 14 días'),
                                        ('30', 'Próximos 30 días'),
                                    ],
                                    validators=[DataRequired()])
    submit = SubmitField('Generar Predicciones')

class EvaluacionForm(FlaskForm):
    metrica = SelectField('Métrica de Evaluación', 
                         choices=[
                             ('mae', 'Error Absoluto Medio (MAE)'),
                             ('rmse', 'Error Cuadrático Medio (RMSE)'),
                             ('r2', 'Coeficiente de Determinación (R²)')
                         ],
                         validators=[DataRequired()])
    periodo_evaluacion = SelectField('Período de Evaluación',
                                   choices=[
                                       ('7', 'Últimos 7 días'),
                                       ('30', 'Últimos 30 días'),
                                       ('90', 'Últimos 90 días'),
                                       ('custom', 'Personalizado')
                                   ],
                                   validators=[DataRequired()])
    fecha_inicio = DateField('Fecha Inicio', validators=[Optional()])
    fecha_fin = DateField('Fecha Fin', validators=[Optional()])
    submit = SubmitField('Evaluar Resultados')

# Rutas
@ml_bp.route('/')
@login_required
@admin_required
def index():
    # Obtener estado del modelo
    modelo_path = os.path.join('instance', 'ml_models', 'extra_trees_model.joblib')
    modelo_entrenado = os.path.exists(modelo_path)
    
    # Obtener fecha de última actualización del modelo
    ultima_actualizacion = None
    if modelo_entrenado:
        ultima_actualizacion = datetime.fromtimestamp(os.path.getmtime(modelo_path))
    
    # Obtener métricas del modelo si existen
    metricas = None
    resultado = ResultadoComparativo.obtener_ultimo_resultado()
    if resultado:
        metricas = {
            'mae': float(resultado.mae) if resultado.mae else None,
            'reduccion_inventario': float(resultado.reduccion_inventario_excedente) if resultado.reduccion_inventario_excedente else None,
            'incremento_ventas': float(resultado.incremento_ventas) if resultado.incremento_ventas else None
        }
    
    # Obtener últimas predicciones
    ultimas_predicciones = Prediccion.query.order_by(Prediccion.fecha_prediccion.desc()).limit(5).all()
    
    return render_template(
        'ml/index.html',
        modelo_entrenado=modelo_entrenado,
        ultima_actualizacion=ultima_actualizacion,
        metricas=metricas,
        predicciones=ultimas_predicciones,
        title='Machine Learning Dashboard'
    )

@ml_bp.route('/entrenamiento', methods=['GET', 'POST'])
@login_required
@admin_required
def entrenamiento():
    form = EntrenamientoForm()
    
    # Establecer fechas predeterminadas
    if not form.fecha_inicio.data:
        form.fecha_inicio.data = datetime.today() - timedelta(days=180)  # 6 meses atrás
    if not form.fecha_fin.data:
        form.fecha_fin.data = datetime.today()
    
    if form.validate_on_submit():
        fecha_inicio = form.fecha_inicio.data
        fecha_fin = form.fecha_fin.data
        
        try:
            # Obtener datos históricos
            ventas_query = db.session.query(
                Venta.producto_id, 
                Venta.cantidad,
                Venta.precio_unitario,
                Venta.fecha_venta,
                Producto.categoria,
                Producto.modelo_carro
            ).join(
                Producto, Venta.producto_id == Producto.id
            ).filter(
                Venta.fecha_venta >= fecha_inicio,
                Venta.fecha_venta <= fecha_fin
            ).all()
            
            if not ventas_query:
                flash('No hay suficientes datos de ventas en el período seleccionado', 'warning')
                return redirect(url_for('ml.entrenamiento'))
            
            # Convertir a DataFrame
            ventas_df = pd.DataFrame([
                {
                    'producto_id': v.producto_id,
                    'cantidad': v.cantidad,
                    'precio_unitario': float(v.precio_unitario),
                    'fecha_venta': v.fecha_venta,
                    'categoria': v.categoria,
                    'modelo_carro': v.modelo_carro
                } for v in ventas_query
            ])
            
            # Obtener datos de inventario
            inventario_query = db.session.query(
                Inventario.producto_id,
                Inventario.stock_actual,
                Inventario.stock_minimo,
                Inventario.stock_optimo
            ).all()
            
            inventario_df = pd.DataFrame([
                {
                    'producto_id': i.producto_id,
                    'stock_actual': i.stock_actual,
                    'stock_minimo': i.stock_minimo or 0,
                    'stock_optimo': i.stock_optimo or i.stock_actual
                } for i in inventario_query
            ])
            
            # Preprocesamiento de datos
            data_procesada = preparar_datos(ventas_df, inventario_df)
            
            # Ingeniería de características
            features_df = crear_features(data_procesada)
            
            # Entrenamiento del modelo
            model, importancias_features, metricas = entrenar_modelo(features_df)
            
            # Guardar modelo
            os.makedirs(os.path.join('instance', 'ml_models'), exist_ok=True)
            joblib.dump(model, os.path.join('instance', 'ml_models', 'extra_trees_model.joblib'))
            
            # Guardar metadatos del modelo
            metadata = {
                'fecha_entrenamiento': datetime.now().isoformat(),
                'periodo_inicio': fecha_inicio.isoformat(),
                'periodo_fin': fecha_fin.isoformat(),
                'num_muestras': len(features_df),
                'metricas': metricas,
                'importancias': importancias_features
            }
            import json
            with open(os.path.join('instance', 'ml_models', 'model_metadata.json'), 'w') as f:
                json.dump(metadata, f)
            
            flash(f'Modelo entrenado correctamente con MAE: {metricas["mae"]:.2f}', 'success')
            return redirect(url_for('ml.index'))
            
        except Exception as e:
            flash(f'Error al entrenar el modelo: {str(e)}', 'danger')
            return redirect(url_for('ml.entrenamiento'))
    
    return render_template('ml/entrenamiento.html', form=form, title='Entrenamiento de Modelo')

@ml_bp.route('/prediccion', methods=['GET', 'POST'])
@login_required
@admin_required
def prediccion():
    form = PrediccionForm()
    
    # Cargar categorías para el formulario
    categorias = db.session.query(Producto.categoria).distinct().all()
    opciones_categoria = [('', 'Todas las categorías')] + [(cat[0], cat[0]) for cat in categorias]
    form.categoria.choices = opciones_categoria
    
    if form.validate_on_submit():
        categoria = form.categoria.data
        dias_prediccion = int(form.periodo_prediccion.data)
        
        try:
            # Verificar si existe el modelo
            modelo_path = os.path.join('instance', 'ml_models', 'extra_trees_model.joblib')
            if not os.path.exists(modelo_path):
                flash('No hay modelo entrenado. Por favor, entrene el modelo primero.', 'warning')
                return redirect(url_for('ml.entrenamiento'))
            
            # Cargar modelo
            model = joblib.load(modelo_path)
            
            # Obtener datos para generar predicciones
            # Ventas recientes (últimos 90 días) para calcular tendencias
            fecha_inicio = datetime.today() - timedelta(days=90)
            
            ventas_query = db.session.query(
                Venta.producto_id, 
                Venta.cantidad,
                Venta.precio_unitario,
                Venta.fecha_venta,
                Producto.categoria,
                Producto.modelo_carro
            ).join(
                Producto, Venta.producto_id == Producto.id
            ).filter(
                Venta.fecha_venta >= fecha_inicio
            )
            
            # Filtrar por categoría si se seleccionó
            if categoria:
                ventas_query = ventas_query.filter(Producto.categoria == categoria)
                
            ventas_recientes = ventas_query.all()
            
            if not ventas_recientes:
                flash('No hay datos de ventas recientes para generar predicciones', 'warning')
                return redirect(url_for('ml.prediccion'))
            
            # Convertir a DataFrame
            ventas_df = pd.DataFrame([
                {
                    'producto_id': v.producto_id,
                    'cantidad': v.cantidad,
                    'precio_unitario': float(v.precio_unitario),
                    'fecha_venta': v.fecha_venta,
                    'categoria': v.categoria,
                    'modelo_carro': v.modelo_carro
                } for v in ventas_recientes
            ])
            
            # Obtener inventario actual
            inventario_query = db.session.query(
                Inventario.producto_id,
                Inventario.stock_actual,
                Inventario.stock_minimo,
                Inventario.stock_optimo,
                Producto.categoria
            ).join(
                Producto, Inventario.producto_id == Producto.id
            )
            
            # Filtrar por categoría si se seleccionó
            if categoria:
                inventario_query = inventario_query.filter(Producto.categoria == categoria)
                
            inventario_actual = inventario_query.all()
            
            inventario_df = pd.DataFrame([
                {
                    'producto_id': i.producto_id,
                    'stock_actual': i.stock_actual,
                    'stock_minimo': i.stock_minimo or 0,
                    'stock_optimo': i.stock_optimo or i.stock_actual,
                    'categoria': i.categoria
                } for i in inventario_actual
            ])
            
            # Generar predicciones
            predicciones = generar_predicciones(
                model, 
                ventas_df, 
                inventario_df, 
                dias_prediccion=dias_prediccion
            )
            
            # Guardar predicciones en la base de datos
            fecha_inicio_pred = datetime.today()
            fecha_fin_pred = fecha_inicio_pred + timedelta(days=dias_prediccion)
            
            # Eliminar predicciones anteriores para no duplicar
            Prediccion.query.filter(
                Prediccion.fecha_inicio >= fecha_inicio_pred
            ).delete()
            
            # Insertar nuevas predicciones
            for _, row in predicciones.iterrows():
                prediccion = Prediccion(
                    producto_id=row['producto_id'],
                    cantidad_predicha=int(max(0, row['cantidad_predicha'])),
                    fecha_inicio=fecha_inicio_pred,
                    fecha_fin=fecha_fin_pred,
                    confianza=row.get('confianza', 0.8),
                    modelo_version='ExtraTreesRegressor'
                )
                db.session.add(prediccion)
            
            db.session.commit()
            
            flash(f'Predicciones generadas para los próximos {dias_prediccion} días', 'success')
            return redirect(url_for('ml.resultados_prediccion'))
            
        except Exception as e:
            flash(f'Error al generar predicciones: {str(e)}', 'danger')
            return redirect(url_for('ml.prediccion'))
    
    return render_template('ml/prediccion.html', form=form, title='Generación de Predicciones')

@ml_bp.route('/resultados')
@login_required
@admin_required
def resultados_prediccion():
    # Obtener predicciones más recientes
    predicciones = db.session.query(
        Prediccion, 
        Producto.codigo,
        Producto.categoria,
        Producto.modelo_carro,
        Inventario.stock_actual
    ).join(
        Producto, Prediccion.producto_id == Producto.id
    ).outerjoin(
        Inventario, Producto.id == Inventario.producto_id
    ).order_by(
        Producto.categoria,
        Producto.modelo_carro,
        Prediccion.fecha_prediccion.desc()
    ).all()
    
    # Agrupar por productos y tomar la predicción más reciente
    predicciones_unicas = {}
    for pred, codigo, categoria, modelo, stock in predicciones:
        key = pred.producto_id
        if key not in predicciones_unicas:
            predicciones_unicas[key] = {
                'prediccion': pred,
                'codigo': codigo,
                'categoria': categoria,
                'modelo_carro': modelo,
                'stock_actual': stock or 0
            }
    
    # Convertir a lista para la plantilla
    resultados = list(predicciones_unicas.values())
    
    # Agrupar por categoría para estadísticas
    categorias = {}
    for res in resultados:
        cat = res['categoria']
        if cat not in categorias:
            categorias[cat] = {
                'total_predicho': 0,
                'productos': 0
            }
        categorias[cat]['total_predicho'] += res['prediccion'].cantidad_predicha
        categorias[cat]['productos'] += 1
    
    return render_template(
        'ml/resultados_prediccion.html',
        predicciones=resultados,
        categorias=categorias,
        title='Resultados de Predicciones'
    )

class EvaluacionForm(FlaskForm):
    fecha_inicio = DateField('Fecha Inicio', validators=[DataRequired()])
    fecha_fin = DateField('Fecha Fin', validators=[DataRequired()])
    metrica = SelectField('Métrica de Evaluación', 
                         choices=[
                             ('mae', 'Error Absoluto Medio (MAE)'),
                             ('rmse', 'Error Cuadrático Medio (RMSE)'),
                             ('r2', 'Coeficiente de Determinación (R²)')
                         ],
                         default='mae',
                         validators=[Optional()])
    submit = SubmitField('Evaluar Resultados')


@ml_bp.route('/evaluacion', methods=['GET', 'POST'])
@login_required
@admin_required
def evaluacion():
    form = EvaluacionForm()
    
    # Establecer fechas predeterminadas
    if not form.fecha_inicio.data:
        form.fecha_inicio.data = datetime.today() - timedelta(days=30)  # 30 días atrás
    if not form.fecha_fin.data:
        form.fecha_fin.data = datetime.today()
    
    if form.validate_on_submit():
        fecha_inicio = form.fecha_inicio.data
        fecha_fin = form.fecha_fin.data
        metrica_seleccionada = form.metrica.data
        
        try:
            # Obtener predicciones en el período seleccionado
            predicciones = db.session.query(
                Prediccion.producto_id,
                Prediccion.cantidad_predicha,
                Prediccion.fecha_inicio,
                Prediccion.fecha_fin
            ).filter(
                Prediccion.fecha_inicio >= fecha_inicio,
                Prediccion.fecha_fin <= fecha_fin
            ).all()
            
            if not predicciones:
                flash('No hay predicciones en el período seleccionado', 'warning')
                return redirect(url_for('ml.evaluacion'))
            
            # Obtener ventas reales en el mismo período
            ventas_reales = db.session.query(
                Venta.producto_id,
                db.func.sum(Venta.cantidad).label('cantidad_real')
            ).filter(
                Venta.fecha_venta >= fecha_inicio,
                Venta.fecha_venta <= fecha_fin
            ).group_by(Venta.producto_id).all()
            
            # Convertir a diccionarios para fácil acceso
            predicciones_dict = {p.producto_id: p.cantidad_predicha for p in predicciones}
            ventas_dict = {v.producto_id: v.cantidad_real for v in ventas_reales}
            
            # Calcular métricas
            errores = []
            errores_cuadrados = []
            reales = []
            predichos = []
            
            for producto_id, cantidad_predicha in predicciones_dict.items():
                cantidad_real = ventas_dict.get(producto_id, 0)
                error = abs(cantidad_predicha - cantidad_real)
                error_cuadrado = (cantidad_predicha - cantidad_real) ** 2
                
                errores.append(error)
                errores_cuadrados.append(error_cuadrado)
                reales.append(cantidad_real)
                predichos.append(cantidad_predicha)
            
            # Calcular diferentes métricas según selección
            mae = sum(errores) / len(errores) if errores else 0
            rmse = (sum(errores_cuadrados) / len(errores_cuadrados)) ** 0.5 if errores_cuadrados else 0
            
            # Cálculo de R² (necesita un poco más de lógica)
            media_reales = sum(reales) / len(reales) if reales else 0
            ss_total = sum((y - media_reales) ** 2 for y in reales) if reales else 0
            ss_residual = sum(errores_cuadrados)
            r2 = 1 - (ss_residual / ss_total) if ss_total != 0 else 0
            
            # Asignar la métrica correcta basada en la selección
            metrica_valor = mae
            if metrica_seleccionada == 'rmse':
                metrica_valor = rmse
            elif metrica_seleccionada == 'r2':
                metrica_valor = r2
            
            # Calcular reducción de inventario excedente
            # Comparar inventario excedente antes y después del ML
            inventario_antes = db.session.query(
                db.func.sum(Inventario.stock_actual - Inventario.stock_optimo).label('excedente')
            ).filter(
                Inventario.stock_actual > Inventario.stock_optimo
            ).scalar()
            
            inventario_antes = float(inventario_antes) if inventario_antes else 0
            
            # Calcular el incremento en ventas
            ventas_antes = db.session.query(
                db.func.sum(Venta.cantidad)
            ).filter(
                Venta.fecha_venta < fecha_inicio
            ).scalar()
            
            ventas_durante = db.session.query(
                db.func.sum(Venta.cantidad)
            ).filter(
                Venta.fecha_venta >= fecha_inicio,
                Venta.fecha_venta <= fecha_fin
            ).scalar()
            
            ventas_antes = float(ventas_antes) if ventas_antes else 0
            ventas_durante = float(ventas_durante) if ventas_durante else 0
            
            incremento_ventas = ((ventas_durante - ventas_antes) / ventas_antes * 100) if ventas_antes > 0 else 0
            
            # Guardar resultados
            resultado = ResultadoComparativo(
                periodo_inicio=fecha_inicio,
                periodo_fin=fecha_fin,
                mae=mae,
                rmse=rmse,  # Añadir RMSE
                r2=r2,      # Añadir R²
                reduccion_inventario_excedente=10.5,  # Valor ejemplo, se debería calcular con datos reales
                incremento_ventas=incremento_ventas,
                notas=f'Evaluación realizada el {datetime.now()}'
            )
            
            db.session.add(resultado)
            db.session.commit()
            
            flash(f'Evaluación completada con {metrica_seleccionada.upper()}: {metrica_valor:.2f}', 'success')
            return redirect(url_for('ml.resultados_evaluacion'))
            
        except Exception as e:
            flash(f'Error al evaluar resultados: {str(e)}', 'danger')
            return redirect(url_for('ml.evaluacion'))
    
    return render_template('ml/evaluacion.html', form=form, title='Evaluación de Resultados')

@ml_bp.route('/resultados/evaluacion')
@login_required
@admin_required
def resultados_evaluacion():
    # Obtener historial de evaluaciones
    evaluaciones = ResultadoComparativo.query.order_by(ResultadoComparativo.fecha_evaluacion.desc()).all()
    
    # Obtener última evaluación para gráficos
    ultima_evaluacion = evaluaciones[0] if evaluaciones else None
    
    # Obtener datos para gráficos comparativos si hay una evaluación
    datos_graficos = None
    if ultima_evaluacion:
        # Ventas antes vs después
        ventas_antes = db.session.query(
            db.func.date_trunc('day', Venta.fecha_venta).label('fecha'),
            db.func.sum(Venta.cantidad).label('cantidad')
        ).filter(
            Venta.fecha_venta < ultima_evaluacion.periodo_inicio
        ).group_by(db.func.date_trunc('day', Venta.fecha_venta)).all()
        
        ventas_despues = db.session.query(
            db.func.date_trunc('day', Venta.fecha_venta).label('fecha'),
            db.func.sum(Venta.cantidad).label('cantidad')
        ).filter(
            Venta.fecha_venta >= ultima_evaluacion.periodo_inicio,
            Venta.fecha_venta <= ultima_evaluacion.periodo_fin
        ).group_by(db.func.date_trunc('day', Venta.fecha_venta)).all()
        
        datos_graficos = {
            'fechas_antes': [v.fecha.strftime('%Y-%m-%d') for v in ventas_antes],
            'cantidades_antes': [float(v.cantidad) for v in ventas_antes],
            'fechas_despues': [v.fecha.strftime('%Y-%m-%d') for v in ventas_despues],
            'cantidades_despues': [float(v.cantidad) for v in ventas_despues]
        }
    
    return render_template(
        'ml/resultados_evaluacion.html',
        evaluaciones=evaluaciones,
        ultima_evaluacion=ultima_evaluacion,
        datos_graficos=datos_graficos,
        title='Evaluación de Impacto del ML'
    )
