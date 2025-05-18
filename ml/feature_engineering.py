import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

def crear_features(datos_df):
    """
    Crea características (features) a partir de los datos procesados
    para el entrenamiento del modelo de ML.
    
    Args:
        datos_df (pd.DataFrame): DataFrame con datos preprocesados
    
    Returns:
        pd.DataFrame: DataFrame con features de ML
    """
    # Copiar para no modificar el original
    df = datos_df.copy()
    
    # Características temporales
    df['dia_semana'] = df['fecha_venta'].dt.dayofweek
    df['semana_año'] = df['fecha_venta'].dt.isocalendar().week
    df['mes'] = df['fecha_venta'].dt.month
    df['dia_mes'] = df['fecha_venta'].dt.day
    df['es_fin_semana'] = df['dia_semana'].apply(lambda x: 1 if x >= 5 else 0)
    
    # Características de ventas históricas (últimos 7, 14 y 30 días)
    # Necesitamos calcular medias móviles para cada producto
    df = df.sort_values(['producto_id', 'fecha_venta'])
    
    # Media móvil de ventas (7 días)
    df['media_movil_ventas_7d'] = df.groupby('producto_id')['cantidad'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )
    
    # Media móvil de ventas (14 días)
    df['media_movil_ventas_14d'] = df.groupby('producto_id')['cantidad'].transform(
        lambda x: x.rolling(window=14, min_periods=1).mean()
    )
    
    # Media móvil de ventas (30 días)
    df['media_movil_ventas_30d'] = df.groupby('producto_id')['cantidad'].transform(
        lambda x: x.rolling(window=30, min_periods=1).mean()
    )
    
    # Lag de ventas (7 días antes)
    df['lag_ventas_7d'] = df.groupby('producto_id')['cantidad'].shift(7).fillna(0)
    
    # Lag de ventas (14 días antes)
    df['lag_ventas_14d'] = df.groupby('producto_id')['cantidad'].shift(14).fillna(0)
    
    # Lag de ventas (30 días antes)
    df['lag_ventas_30d'] = df.groupby('producto_id')['cantidad'].shift(30).fillna(0)
    
    # Variación de ventas (cambio porcentual respecto a la semana anterior)
    # Evitar división por cero
    df['media_movil_ventas_7d_anterior'] = df.groupby('producto_id')['media_movil_ventas_7d'].shift(7).fillna(0)
    df['variacion_ventas'] = df.apply(
        lambda row: 0 if row['media_movil_ventas_7d_anterior'] == 0 
                      else (row['media_movil_ventas_7d'] - row['media_movil_ventas_7d_anterior']) / 
                           (row['media_movil_ventas_7d_anterior'] + 0.001),
        axis=1
    )
    
    # Ratio stock/demanda
    df['ratio_stock_demanda'] = df.apply(
        lambda row: float('inf') if row['media_movil_ventas_7d'] == 0 
                    else row['stock_actual'] / (row['media_movil_ventas_7d'] + 0.001),
        axis=1
    )
    
    # Indicador de exceso de stock
    df['exceso_stock'] = df.apply(
        lambda row: max(0, row['stock_actual'] - row['stock_optimo']),
        axis=1
    )
    
    # Indicador de stock bajo
    df['stock_bajo'] = df.apply(
        lambda row: 1 if row['stock_actual'] < row['stock_minimo'] else 0,
        axis=1
    )
    
    # Precio relativo (comparado con el precio promedio de la categoría)
    precio_promedio_categoria = df.groupby('categoria')['precio_unitario'].transform('mean')
    df['precio_relativo'] = df['precio_unitario'] / precio_promedio_categoria
    
    # Ciclicidad del mes y día de la semana (transformación cíclica)
    df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
    df['mes_cos'] = np.cos(2 * np.pi * df['mes'] / 12)
    df['dia_semana_sin'] = np.sin(2 * np.pi * df['dia_semana'] / 7)
    df['dia_semana_cos'] = np.cos(2 * np.pi * df['dia_semana'] / 7)
    
    # Eliminar columnas no necesarias para ML
    columnas_a_eliminar = ['fecha_venta', 'media_movil_ventas_7d_anterior']
    df = df.drop(columns=columnas_a_eliminar, errors='ignore')
    
    # Codificar variables categóricas
    label_encoders = {}
    for columna in ['categoria', 'modelo_carro']:
        if columna in df.columns:
            le = LabelEncoder()
            df[f'{columna}_encoded'] = le.fit_transform(df[columna])
            label_encoders[columna] = le
            
    # Eliminar las columnas originales categóricas después de codificarlas
    df = df.drop(columns=['categoria', 'modelo_carro'], errors='ignore')
    
    # Eliminar filas con valores NaN
    df = df.dropna()
    
    return df