import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.utils.date_utils import preparar_fechas_para_df

def preparar_datos(ventas_df, inventario_df):
    """
    Preprocesa los datos de ventas e inventario para el análisis de ML.
    
    Args:
        ventas_df (pd.DataFrame): DataFrame con datos históricos de ventas
        inventario_df (pd.DataFrame): DataFrame con datos actuales de inventario
    
    Returns:
        pd.DataFrame: DataFrame procesado listo para feature engineering
    """
    # Asegurarse de que las fechas estén en formato datetime
    ventas_df = preparar_fechas_para_df(ventas_df)
    
    # Agregación de ventas por producto y día
    ventas_diarias = ventas_df.groupby(['producto_id', pd.Grouper(key='fecha_venta', freq='D')]).agg({
        'cantidad': 'sum',
        'precio_unitario': 'mean',  # Precio promedio por día
        'categoria': 'first',
        'modelo_carro': 'first'
    }).reset_index()
    
    # Rellenar días sin ventas
    # Obtener rango completo de fechas
    fecha_min = ventas_df['fecha_venta'].min()
    fecha_max = ventas_df['fecha_venta'].max()
    
    # Crear un DataFrame de fechas completo
    todos_productos = ventas_df['producto_id'].unique()
    todas_fechas = pd.date_range(start=fecha_min, end=fecha_max, freq='D')
    
    # Crear un MultiIndex con todas las combinaciones producto-fecha
    idx = pd.MultiIndex.from_product([todos_productos, todas_fechas], 
                                     names=['producto_id', 'fecha_venta'])
    
    # Reindexar para incluir todas las fechas para todos los productos
    ventas_completas = ventas_diarias.set_index(['producto_id', 'fecha_venta']).reindex(idx)
    
    # Rellenar valores faltantes
    ventas_completas = ventas_completas.reset_index()
    
    # Para cantidad, rellenar con 0 (no hubo ventas)
    ventas_completas['cantidad'] = ventas_completas['cantidad'].fillna(0)
    
    # Para precio_unitario, usar el último precio disponible (forward fill por producto)
    ventas_completas = ventas_completas.sort_values(['producto_id', 'fecha_venta'])
    ventas_completas['precio_unitario'] = ventas_completas.groupby('producto_id')['precio_unitario'].ffill()
    
    # Si aún hay NaN en precio_unitario (para productos sin ventas previas),
    # usar el precio promedio de la categoría
    precios_por_categoria = ventas_df.groupby('categoria')['precio_unitario'].mean()
    
    # Primero completamos las columnas de categoría y modelo_carro
    for producto_id in todos_productos:
        mask = ventas_completas['producto_id'] == producto_id
        if mask.any():
            producto_info = ventas_df[ventas_df['producto_id'] == producto_id].iloc[0]
            ventas_completas.loc[mask, 'categoria'] = producto_info['categoria']
            ventas_completas.loc[mask, 'modelo_carro'] = producto_info['modelo_carro']
    
    # Ahora completamos los precios faltantes usando la categoría
    for cat in precios_por_categoria.index:
        mask = (ventas_completas['precio_unitario'].isna()) & (ventas_completas['categoria'] == cat)
        ventas_completas.loc[mask, 'precio_unitario'] = precios_por_categoria[cat]
    
    # Si aún hay NaN en precio_unitario, usar el precio promedio global
    precio_promedio_global = ventas_df['precio_unitario'].mean()
    ventas_completas['precio_unitario'] = ventas_completas['precio_unitario'].fillna(precio_promedio_global)
    
    # Limpiar posibles NaN restantes
    ventas_completas = ventas_completas.fillna({
        'categoria': 'otros',
        'modelo_carro': 'generico'
    })
    
    # Fusionar con datos de inventario
    datos_completos = pd.merge(
        ventas_completas, 
        inventario_df,
        on='producto_id',
        how='left'
    )
    
    # Rellenar valores de inventario faltantes
    datos_completos['stock_actual'] = datos_completos['stock_actual'].fillna(0)
    datos_completos['stock_minimo'] = datos_completos['stock_minimo'].fillna(0)
    datos_completos['stock_optimo'] = datos_completos['stock_optimo'].fillna(
        datos_completos['stock_actual']
    )
    
    return datos_completos