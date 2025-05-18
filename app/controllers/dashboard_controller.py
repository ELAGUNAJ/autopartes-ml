from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app import db
from app.models.venta import Venta
from app.models.producto import Producto
from app.models.inventario import Inventario
from app.models.prediccion import Prediccion
from app.models.resultado import ResultadoComparativo
from app.utils.auth_utils import vendedor_required
from app.utils.db_utils import (
    obtener_estadisticas_ventas,
    obtener_ventas_por_categoria,
    obtener_inventario_excedente,
    obtener_productos_baja_rotacion
)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    # Obtener datos para estadísticas generales
    estadisticas = obtener_estadisticas_ventas()
    
    # Ventas por categoría
    ventas_categoria = obtener_ventas_por_categoria()
    
    # Inventario excedente
    inventario_excedente = obtener_inventario_excedente()
    
    # Productos con baja rotación
    productos_baja_rotacion = obtener_productos_baja_rotacion()
    
    # Últimas ventas
    ultimas_ventas = Venta.query.order_by(Venta.fecha_venta.desc()).limit(5).all()
    
    # Verificar si hay un modelo ML entrenado
    from os.path import exists
    modelo_entrenado = exists('instance/ml_models/extra_trees_model.joblib')
    
    # Obtener último resultado comparativo para mostrar impacto del ML
    ultimo_resultado = ResultadoComparativo.obtener_ultimo_resultado()
    impacto_ml = None
    if ultimo_resultado:
        impacto_ml = {
            'reduccion_inventario': float(ultimo_resultado.reduccion_inventario_excedente) if ultimo_resultado.reduccion_inventario_excedente else 0,
            'incremento_ventas': float(ultimo_resultado.incremento_ventas) if ultimo_resultado.incremento_ventas else 0,
            'fecha_evaluacion': ultimo_resultado.fecha_evaluacion
        }
    
    # Obtener datos para gráficos
    # Ventas por día (últimos 30 días)
    fecha_inicio = datetime.now() - timedelta(days=30)
    
    ventas_por_dia = db.session.query(
        db.func.date(Venta.fecha_venta).label('fecha'),
        db.func.sum(Venta.precio_total).label('total')
    ).filter(
        Venta.fecha_venta >= fecha_inicio
    ).group_by(
        db.func.date(Venta.fecha_venta)
    ).order_by(
        db.func.date(Venta.fecha_venta)
    ).all()
    
    # Preparar datos para gráficos
    datos_grafico_ventas = {
        'fechas': [v.fecha.strftime('%d-%m-%Y') for v in ventas_por_dia],
        'totales': [float(v.total) for v in ventas_por_dia]
    }
    
    # Predicciones vs ventas reales si hay modelo entrenado
    datos_grafico_predicciones = None
    if modelo_entrenado:
        # Obtener últimas predicciones
        ultimas_predicciones = Prediccion.query.order_by(Prediccion.fecha_prediccion.desc()).limit(10).all()
        
        # Obtener ventas reales para los mismos productos y período
        if ultimas_predicciones:
            # Ejemplo para un producto específico 
            # (esto debería adaptarse para mostrar múltiples productos)
            if ultimas_predicciones:
                pred = ultimas_predicciones[0]
                producto_id = pred.producto_id
                
                # Obtener ventas históricas de este producto
                ventas_historicas = db.session.query(
                    db.func.date(Venta.fecha_venta).label('fecha'),
                    db.func.sum(Venta.cantidad).label('cantidad')
                ).filter(
                    Venta.producto_id == producto_id,
                    Venta.fecha_venta >= fecha_inicio
                ).group_by(
                    db.func.date(Venta.fecha_venta)
                ).order_by(
                    db.func.date(Venta.fecha_venta)
                ).all()
                
                # Preparar datos para el gráfico
                datos_grafico_predicciones = {
                    'producto_id': producto_id,
                    'fechas': [v.fecha.strftime('%d-%m-%Y') for v in ventas_historicas],
                    'cantidades': [int(v.cantidad) for v in ventas_historicas],
                    'prediccion': pred.cantidad_predicha
                }
    
    return render_template(
        'dashboard/index.html',
        estadisticas=estadisticas,
        ventas_categoria=ventas_categoria,
        inventario_excedente=inventario_excedente,
        productos_baja_rotacion=productos_baja_rotacion,
        ultimas_ventas=ultimas_ventas,
        modelo_entrenado=modelo_entrenado,
        impacto_ml=impacto_ml,
        datos_grafico_ventas=datos_grafico_ventas,
        datos_grafico_predicciones=datos_grafico_predicciones,
        title='Dashboard'
    )

@dashboard_bp.route('/comparativo')
@login_required
@vendedor_required
def comparativo():
    # Obtener resultados comparativos para mostrar el antes y después
    resultados = ResultadoComparativo.query.order_by(ResultadoComparativo.fecha_evaluacion.desc()).all()
    
    # Si no hay resultados, redirigir al dashboard principal
    if not resultados:
        return redirect(url_for('dashboard.index'))
    
    # Obtener el último resultado para análisis detallado
    ultimo_resultado = resultados[0]
    
    # Obtener datos para gráficos comparativos
    # Inventario excedente antes vs después
    inventario_antes = sum(float(p['excedente']) for p in obtener_inventario_excedente())
    
    # Calcular la reducción porcentual
    reduccion = float(ultimo_resultado.reduccion_inventario_excedente) if ultimo_resultado.reduccion_inventario_excedente else 0
    inventario_despues = inventario_antes * (1 - reduccion / 100)
    
    datos_inventario = {
        'antes': inventario_antes,
        'despues': inventario_despues,
        'reduccion_porcentaje': reduccion
    }
    
    # Ventas antes vs después
    incremento = float(ultimo_resultado.incremento_ventas) if ultimo_resultado.incremento_ventas else 0
    
    # Obtener estadísticas de ventas actuales
    estadisticas_ventas = obtener_estadisticas_ventas()
    ventas_actuales = estadisticas_ventas['ventas_totales']
    
    # Calcular ventas anteriores basado en el incremento
    ventas_anteriores = ventas_actuales / (1 + incremento / 100) if incremento != -100 else 0
    
    datos_ventas = {
        'antes': ventas_anteriores,
        'despues': ventas_actuales,
        'incremento_porcentaje': incremento
    }
    
    return render_template(
        'dashboard/comparativo.html',
        resultados=resultados,
        ultimo_resultado=ultimo_resultado,
        datos_inventario=datos_inventario,
        datos_ventas=datos_ventas,
        title='Análisis Comparativo Pre/Post ML'
    )

@dashboard_bp.route('/productos')
@login_required
@vendedor_required
def productos():
    # Obtener todos los productos con su inventario
    productos = db.session.query(
        Producto,
        Inventario
    ).outerjoin(
        Inventario, Producto.id == Inventario.producto_id
    ).order_by(
        Producto.categoria,
        Producto.modelo_carro
    ).all()
    
    # Agrupar por categoría
    productos_por_categoria = {}
    for producto, inventario in productos:
        if producto.categoria not in productos_por_categoria:
            productos_por_categoria[producto.categoria] = []
        
        productos_por_categoria[producto.categoria].append({
            'id': producto.id,
            'codigo': producto.codigo,
            'modelo_carro': producto.modelo_carro,
            'descripcion': producto.descripcion,
            'precio_unitario': float(producto.precio_unitario),
            'stock_actual': inventario.stock_actual if inventario else 0,
            'stock_minimo': inventario.stock_minimo if inventario else 0,
            'stock_optimo': inventario.stock_optimo if inventario else 0
        })
    
    return render_template(
        'dashboard/productos.html',
        productos_por_categoria=productos_por_categoria,
        title='Catálogo de Productos'
    )

@dashboard_bp.route('/predicciones')
@login_required
@vendedor_required
def predicciones():
    # Verificar si hay un modelo ML entrenado
    from os.path import exists
    modelo_entrenado = exists('instance/ml_models/extra_trees_model.joblib')
    
    if not modelo_entrenado:
        return redirect(url_for('dashboard.index'))
    
    # Obtener las predicciones más recientes con datos de producto
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
        Prediccion.fecha_prediccion.desc()
    ).all()
    
    # Agrupar por fecha de predicción para mostrar las más recientes
    predicciones_por_fecha = {}
    for pred, codigo, categoria, modelo, stock in predicciones:
        fecha_key = pred.fecha_prediccion.strftime('%Y-%m-%d')
        
        if fecha_key not in predicciones_por_fecha:
            predicciones_por_fecha[fecha_key] = {
                'fecha': pred.fecha_prediccion,
                'predicciones': []
            }
        
        predicciones_por_fecha[fecha_key]['predicciones'].append({
            'id': pred.id,
            'producto_id': pred.producto_id,
            'codigo': codigo,
            'categoria': categoria,
            'modelo_carro': modelo,
            'cantidad_predicha': pred.cantidad_predicha,
            'stock_actual': stock if stock else 0,
            'diferencia': (stock if stock else 0) - pred.cantidad_predicha,
            'periodo': f"{pred.fecha_inicio.strftime('%d/%m/%Y')} - {pred.fecha_fin.strftime('%d/%m/%Y')}"
        })
    
    # Ordenar por fecha (más reciente primero)
    fechas_ordenadas = sorted(predicciones_por_fecha.keys(), reverse=True)
    predicciones_ordenadas = [predicciones_por_fecha[fecha] for fecha in fechas_ordenadas]
    
    return render_template(
        'dashboard/predicciones.html',
        predicciones=predicciones_ordenadas,
        title='Predicciones de Ventas'
    )