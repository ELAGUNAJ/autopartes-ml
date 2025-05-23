from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
import pandas as pd
from datetime import datetime, timedelta

from app import db
from app.models.venta import Venta
from app.models.producto import Producto
from app.models.inventario import Inventario
from app.utils.auth_utils import vendedor_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    # Obtener estadísticas generales
    try:
        # Estadísticas de ventas
        ventas_query = db.session.query(
            db.func.count(Venta.id).label('total_ventas'),
            db.func.sum(Venta.precio_total).label('ventas_totales'),
            db.func.avg(Venta.precio_total).label('venta_promedio')
        ).first()
        
        estadisticas = {
            'total_ventas': ventas_query.total_ventas if ventas_query.total_ventas else 0,
            'ventas_totales': float(ventas_query.ventas_totales) if ventas_query.ventas_totales else 0,
            'venta_promedio': float(ventas_query.venta_promedio) if ventas_query.venta_promedio else 0
        }
        
        # Ventas por categoría
        ventas_categoria_query = db.session.query(
            Producto.categoria,
            db.func.count(Venta.id).label('total_ventas'),
            db.func.sum(Venta.precio_total).label('monto_total')
        ).join(Producto, Venta.producto_id == Producto.id
        ).group_by(Producto.categoria
        ).order_by(db.func.sum(Venta.precio_total).desc()
        ).all()
        
        ventas_categoria = [
            {
                'categoria': row[0],
                'total_ventas': row[1],
                'monto_total': float(row[2]) if row[2] else 0
            }
            for row in ventas_categoria_query
        ]
        
        # Inventario excedente
        inventario_excedente_query = db.session.query(
            Producto.id,
            Producto.codigo,
            Producto.categoria,
            Producto.modelo_carro,
            Inventario.stock_actual,
            Inventario.stock_optimo,
            (Inventario.stock_actual - Inventario.stock_optimo).label('excedente')
        ).join(
            Inventario, Producto.id == Inventario.producto_id
        ).filter(
            Inventario.stock_actual > Inventario.stock_optimo
        ).order_by(
            (Inventario.stock_actual - Inventario.stock_optimo).desc()
        ).all()
        
        inventario_excedente = [
            {
                'id': row[0],
                'codigo': row[1],
                'categoria': row[2],
                'modelo_carro': row[3],
                'stock_actual': row[4],
                'stock_optimo': row[5],
                'excedente': row[6]
            }
            for row in inventario_excedente_query
        ]
        
        # Productos con baja rotación (corregido)
        fecha_90_dias = datetime.utcnow() - timedelta(days=90)
        
        productos_baja_rotacion_query = db.session.query(
            Producto.id,
            Producto.codigo,
            Producto.categoria,
            Producto.modelo_carro,
            db.func.count(Venta.id).label('total_ventas'),
            Inventario.stock_actual
        ).outerjoin(
            Venta, db.and_(
                Producto.id == Venta.producto_id,
                Venta.fecha_venta >= fecha_90_dias
            )
        ).join(
            Inventario, Producto.id == Inventario.producto_id
        ).group_by(
            Producto.id, Producto.codigo, Producto.categoria, 
            Producto.modelo_carro, Inventario.stock_actual
        ).having(
            db.func.count(Venta.id) < 5,
            Inventario.stock_actual > 10
        ).order_by(
            db.func.count(Venta.id), Inventario.stock_actual.desc()
        ).all()
        
        productos_baja_rotacion = [
            {
                'id': row[0],
                'codigo': row[1],
                'categoria': row[2],
                'modelo_carro': row[3],
                'total_ventas': row[4],
                'stock_actual': row[5]
            }
            for row in productos_baja_rotacion_query
        ]
        
        # Últimas ventas
        ultimas_ventas = Venta.query.order_by(Venta.fecha_venta.desc()).limit(5).all()
        
        # Obtener datos para gráficos
        # Ventas por día (últimos 30 días)
        fecha_inicio = datetime.utcnow() - timedelta(days=30)
        
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
            'fechas': [(v.fecha.strftime('%d-%m-%Y') if hasattr(v.fecha, 'strftime') else v.fecha) for v in ventas_por_dia],
            'totales': [float(v.total) for v in ventas_por_dia]
        }
        
        return render_template(
            'dashboard/index.html',
            estadisticas=estadisticas,
            ventas_categoria=ventas_categoria,
            inventario_excedente=inventario_excedente,
            productos_baja_rotacion=productos_baja_rotacion,
            ultimas_ventas=ultimas_ventas,
            modelo_entrenado=False,
            impacto_ml=None,
            datos_grafico_ventas=datos_grafico_ventas,
            datos_grafico_predicciones=None,
            title='Dashboard'
        )
        
    except Exception as e:
        print(f"Error en el dashboard: {e}")
        return render_template(
            'dashboard/index.html',
            estadisticas={'total_ventas': 0, 'ventas_totales': 0, 'venta_promedio': 0},
            ventas_categoria=[],
            inventario_excedente=[],
            productos_baja_rotacion=[],
            ultimas_ventas=[],
            modelo_entrenado=False,
            impacto_ml=None,
            datos_grafico_ventas={'fechas': [], 'totales': []},
            datos_grafico_predicciones=None,
            error=str(e),
            title='Dashboard'
        )

@dashboard_bp.route('/comparativo')
@login_required
@vendedor_required
def comparativo():
    # Versión simplificada hasta que el ML esté implementado
    return render_template(
        'dashboard/comparativo.html',
        resultados=[],
        ultimo_resultado=None,
        datos_inventario={
            'antes': 0,
            'despues': 0,
            'reduccion_porcentaje': 0
        },
        datos_ventas={
            'antes': 0,
            'despues': 0,
            'incremento_porcentaje': 0
        },
        title='Análisis Comparativo Pre/Post ML'
    )