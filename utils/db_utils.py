from app import db
from sqlalchemy import text

def init_db():
    """Inicializar la base de datos con datos de prueba."""
    db.create_all()

def obtener_estadisticas_ventas():
    """Obtener estadísticas generales de ventas."""
    sql = text("""
    SELECT 
        COUNT(*) as total_ventas,
        SUM(precio_total) as ventas_totales,
        AVG(precio_total) as venta_promedio
    FROM ventas
    """)
    
    result = db.session.execute(sql).fetchone()
    return {
        'total_ventas': result[0] if result[0] else 0,
        'ventas_totales': float(result[1]) if result[1] else 0,
        'venta_promedio': float(result[2]) if result[2] else 0
    }

def obtener_ventas_por_categoria():
    """Obtener total de ventas agrupadas por categoría de producto."""
    sql = text("""
    SELECT 
        p.categoria,
        COUNT(v.id) as total_ventas,
        SUM(v.precio_total) as monto_total
    FROM ventas v
    JOIN productos p ON v.producto_id = p.id
    GROUP BY p.categoria
    ORDER BY monto_total DESC
    """)
    
    results = db.session.execute(sql).fetchall()
    return [
        {
            'categoria': row[0],
            'total_ventas': row[1],
            'monto_total': float(row[2]) if row[2] else 0
        }
        for row in results
    ]

def obtener_inventario_excedente():
    """Obtener productos con exceso de inventario."""
    sql = text("""
    SELECT 
        p.id,
        p.codigo,
        p.categoria,
        p.modelo_carro,
        i.stock_actual,
        i.stock_optimo,
        (i.stock_actual - i.stock_optimo) as excedente
    FROM inventario i
    JOIN productos p ON i.producto_id = p.id
    WHERE i.stock_actual > i.stock_optimo
    ORDER BY excedente DESC
    """)
    
    results = db.session.execute(sql).fetchall()
    return [
        {
            'id': row[0],
            'codigo': row[1],
            'categoria': row[2],
            'modelo_carro': row[3],
            'stock_actual': row[4],
            'stock_optimo': row[5],
            'excedente': row[6]
        }
        for row in results
    ]

def obtener_productos_baja_rotacion():
    """Obtener productos con baja rotación (pocas ventas)."""
    sql = text("""
    SELECT 
        p.id,
        p.codigo,
        p.categoria,
        p.modelo_carro,
        COALESCE(COUNT(v.id), 0) as total_ventas,
        i.stock_actual
    FROM productos p
    LEFT JOIN ventas v ON p.id = v.producto_id AND v.fecha_venta >= NOW() - INTERVAL '90 days'
    LEFT JOIN inventario i ON p.id = i.producto_id
    GROUP BY p.id, p.codigo, p.categoria, p.modelo_carro, i.stock_actual
    HAVING COALESCE(COUNT(v.id), 0) < 5 AND i.stock_actual > 10
    ORDER BY total_ventas, i.stock_actual DESC
    """)
    
    results = db.session.execute(sql).fetchall()
    return [
        {
            'id': row[0],
            'codigo': row[1],
            'categoria': row[2],
            'modelo_carro': row[3],
            'total_ventas': row[4],
            'stock_actual': row[5]
        }
        for row in results
    ]

def reporte_impacto_ml(fecha_inicio, fecha_fin):
    """Generar reporte de impacto del modelo ML en un período específico."""
    # Obtener métricas antes del ML
    pre_ml_sql = text("""
    SELECT 
        SUM(v.precio_total) as ventas_total,
        COUNT(v.id) as num_ventas,
        (SELECT SUM(i.stock_actual - i.stock_optimo) 
         FROM inventario i
         JOIN productos p ON i.producto_id = p.id
         WHERE i.stock_actual > i.stock_optimo) as exceso_inventario
    FROM ventas v
    WHERE v.fecha_venta < :fecha_inicio
    """)
    
    # Obtener métricas después del ML
    post_ml_sql = text("""
    SELECT 
        SUM(v.precio_total) as ventas_total,
        COUNT(v.id) as num_ventas,
        (SELECT SUM(i.stock_actual - i.stock_optimo) 
         FROM inventario i
         JOIN productos p ON i.producto_id = p.id
         WHERE i.stock_actual > i.stock_optimo) as exceso_inventario
    FROM ventas v
    WHERE v.fecha_venta >= :fecha_inicio AND v.fecha_venta <= :fecha_fin
    """)
    
    pre_result = db.session.execute(pre_ml_sql, {'fecha_inicio': fecha_inicio}).fetchone()
    post_result = db.session.execute(post_ml_sql, {'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin}).fetchone()
    
    # Calcular cambios porcentuales
    pre_ventas = float(pre_result[0]) if pre_result[0] else 0
    post_ventas = float(post_result[0]) if post_result[0] else 0
    
    pre_num_ventas = pre_result[1] if pre_result[1] else 0
    post_num_ventas = post_result[1] if post_result[1] else 0
    
    pre_exceso = float(pre_result[2]) if pre_result[2] else 0
    post_exceso = float(post_result[2]) if post_result[2] else 0
    
    # Evitar división por cero
    cambio_ventas = ((post_ventas - pre_ventas) / pre_ventas * 100) if pre_ventas > 0 else 0
    cambio_num_ventas = ((post_num_ventas - pre_num_ventas) / pre_num_ventas * 100) if pre_num_ventas > 0 else 0
    reduccion_exceso = ((pre_exceso - post_exceso) / pre_exceso * 100) if pre_exceso > 0 else 0
    
    return {
        'pre_ml': {
            'ventas_total': pre_ventas,
            'num_ventas': pre_num_ventas,
            'exceso_inventario': pre_exceso
        },
        'post_ml': {
            'ventas_total': post_ventas,
            'num_ventas': post_num_ventas,
            'exceso_inventario': post_exceso
        },
        'cambios': {
            'cambio_ventas': cambio_ventas,
            'cambio_num_ventas': cambio_num_ventas,
            'reduccion_exceso': reduccion_exceso
        }
    }