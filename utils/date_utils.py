from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta

def fecha_a_str(fecha, formato='%Y-%m-%d'):
    """Convertir fecha a string en formato específico."""
    if isinstance(fecha, str):
        return fecha
    return fecha.strftime(formato)

def str_a_fecha(fecha_str, formato='%Y-%m-%d'):
    """Convertir string a fecha."""
    if isinstance(fecha_str, datetime):
        return fecha_str
    return datetime.strptime(fecha_str, formato)

def obtener_rango_fechas(fecha_inicio, fecha_fin, formato_salida='%Y-%m-%d'):
    """Obtener lista de fechas entre fecha_inicio y fecha_fin."""
    if isinstance(fecha_inicio, str):
        fecha_inicio = str_a_fecha(fecha_inicio)
    if isinstance(fecha_fin, str):
        fecha_fin = str_a_fecha(fecha_fin)
    
    delta = (fecha_fin - fecha_inicio).days + 1
    fechas = [fecha_inicio + timedelta(days=i) for i in range(delta)]
    
    if formato_salida:
        return [fecha_a_str(fecha, formato_salida) for fecha in fechas]
    return fechas

def obtener_periodo_anterior(fecha_inicio, fecha_fin):
    """Obtener el mismo periodo de tiempo pero anterior al rango dado."""
    if isinstance(fecha_inicio, str):
        fecha_inicio = str_a_fecha(fecha_inicio)
    if isinstance(fecha_fin, str):
        fecha_fin = str_a_fecha(fecha_fin)
    
    delta_dias = (fecha_fin - fecha_inicio).days + 1
    
    fecha_fin_anterior = fecha_inicio - timedelta(days=1)
    fecha_inicio_anterior = fecha_fin_anterior - timedelta(days=delta_dias - 1)
    
    return fecha_inicio_anterior, fecha_fin_anterior

def obtener_dia_semana(fecha):
    """Obtener el día de la semana (0 = lunes, 6 = domingo)."""
    if isinstance(fecha, str):
        fecha = str_a_fecha(fecha)
    return fecha.weekday()

def es_feriado(fecha, lista_feriados):
    """Verificar si una fecha es feriado."""
    fecha_str = fecha_a_str(fecha)
    return fecha_str in lista_feriados

def obtener_semana_del_año(fecha):
    """Obtener el número de semana del año."""
    if isinstance(fecha, str):
        fecha = str_a_fecha(fecha)
    return fecha.isocalendar()[1]

def obtener_mes(fecha):
    """Obtener el mes (1-12)."""
    if isinstance(fecha, str):
        fecha = str_a_fecha(fecha)
    return fecha.month

def calcular_diferencia_meses(fecha_inicio, fecha_fin):
    """Calcular la diferencia en meses entre dos fechas."""
    if isinstance(fecha_inicio, str):
        fecha_inicio = str_a_fecha(fecha_inicio)
    if isinstance(fecha_fin, str):
        fecha_fin = str_a_fecha(fecha_fin)
    
    return (fecha_fin.year - fecha_inicio.year) * 12 + (fecha_fin.month - fecha_inicio.month)

def agregar_meses(fecha, meses):
    """Agregar un número específico de meses a una fecha."""
    if isinstance(fecha, str):
        fecha = str_a_fecha(fecha)
    
    return fecha + relativedelta(months=meses)

def preparar_fechas_para_df(ventas_df):
    """Prepara las fechas para el DataFrame y agrega características temporales."""
    if 'fecha_venta' in ventas_df.columns:
        # Asegurarse de que fecha_venta sea datetime
        ventas_df['fecha_venta'] = pd.to_datetime(ventas_df['fecha_venta'])
        
        # Extraer características temporales
        ventas_df['dia_semana'] = ventas_df['fecha_venta'].dt.dayofweek
        ventas_df['semana_año'] = ventas_df['fecha_venta'].dt.isocalendar().week
        ventas_df['mes'] = ventas_df['fecha_venta'].dt.month
        ventas_df['año'] = ventas_df['fecha_venta'].dt.year
        
    return ventas_df