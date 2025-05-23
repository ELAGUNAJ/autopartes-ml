import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def evaluar_modelo(model, datos_df, predicciones_df):
    """
    Evalúa el modelo comparando predicciones con ventas reales.
    
    Args:
        model: Modelo entrenado
        datos_df (pd.DataFrame): DataFrame con datos reales
        predicciones_df (pd.DataFrame): DataFrame con predicciones
    
    Returns:
        dict: Métricas de evaluación
    """
    # Asegurar que los DataFrames tengan las mismas columnas
    if 'cantidad' not in datos_df.columns or 'cantidad_predicha' not in predicciones_df.columns:
        raise ValueError("Los DataFrames deben contener las columnas 'cantidad' y 'cantidad_predicha'")
    
    # Unir datos reales y predicciones por producto_id y fecha
    if 'fecha_venta' in datos_df.columns and 'fecha' in predicciones_df.columns:
        # Renombrar 'fecha' a 'fecha_venta' para hacer el merge
        predicciones_df = predicciones_df.rename(columns={'fecha': 'fecha_venta'})
    
    # Merge de datos
    df_comparacion = pd.merge(
        datos_df[['producto_id', 'fecha_venta', 'cantidad']],
        predicciones_df[['producto_id', 'fecha_venta', 'cantidad_predicha']],
        on=['producto_id', 'fecha_venta'],
        how='inner'
    )
    
    # Si no hay datos para comparar, devolver métricas vacías
    if len(df_comparacion) == 0:
        return {
            'mae': None,
            'rmse': None,
            'r2': None,
            'error_porcentual_medio': None
        }
    
    # Calcular métricas
    y_real = df_comparacion['cantidad'].values
    y_pred = df_comparacion['cantidad_predicha'].values
    
    mae = mean_absolute_error(y_real, y_pred)
    rmse = np.sqrt(mean_squared_error(y_real, y_pred))
    r2 = r2_score(y_real, y_pred)
    
    # Error porcentual medio (evitar división por cero)
    mape_array = np.zeros(len(y_real))
    for i in range(len(y_real)):
        if y_real[i] > 0:
            mape_array[i] = np.abs((y_real[i] - y_pred[i]) / y_real[i])
    
    # Filtrar solo valores donde y_real > 0
    mape_values = mape_array[y_real > 0]
    mape = np.mean(mape_values) * 100 if len(mape_values) > 0 else None
    
    # Calcular reducción de inventario excedente
    # Esto requeriría datos de inventario antes y después de aplicar ML
    
    # Calcular incremento en ventas
    # Esto requeriría datos de ventas antes y después de aplicar ML
    
    metricas = {
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'error_porcentual_medio': mape
    }
    
    return metricas

def evaluar_impacto_inventario(inventario_antes_df, inventario_despues_df):
    """
    Evalúa el impacto del modelo en la reducción de inventario excedente.
    
    Args:
        inventario_antes_df (pd.DataFrame): DataFrame con inventario antes del ML
        inventario_despues_df (pd.DataFrame): DataFrame con inventario después del ML
    
    Returns:
        dict: Métricas de impacto en inventario
    """
    # Calcular inventario excedente antes y después
    inventario_antes_df['excedente'] = inventario_antes_df.apply(
        lambda row: max(0, row['stock_actual'] - row['stock_optimo']),
        axis=1
    )
    
    inventario_despues_df['excedente'] = inventario_despues_df.apply(
        lambda row: max(0, row['stock_actual'] - row['stock_optimo']),
        axis=1
    )
    
    # Calcular totales
    excedente_antes = inventario_antes_df['excedente'].sum()
    excedente_despues = inventario_despues_df['excedente'].sum()
    
    # Calcular reducción porcentual
    if excedente_antes > 0:
        reduccion_porcentual = (excedente_antes - excedente_despues) / excedente_antes * 100
    else:
        reduccion_porcentual = 0
    
    # Valor en dinero del excedente
    valor_excedente_antes = (
        inventario_antes_df['excedente'] * inventario_antes_df['precio_unitario']
    ).sum()
    
    valor_excedente_despues = (
        inventario_despues_df['excedente'] * inventario_despues_df['precio_unitario']
    ).sum()
    
    ahorro = valor_excedente_antes - valor_excedente_despues
    
    return {
        'excedente_antes': excedente_antes,
        'excedente_despues': excedente_despues,
        'reduccion_porcentual': reduccion_porcentual,
        'valor_excedente_antes': valor_excedente_antes,
        'valor_excedente_despues': valor_excedente_despues,
        'ahorro': ahorro
    }

def evaluar_impacto_ventas(ventas_antes_df, ventas_despues_df):
    """
    Evalúa el impacto del modelo en el incremento de ventas.
    
    Args:
        ventas_antes_df (pd.DataFrame): DataFrame con ventas antes del ML
        ventas_despues_df (pd.DataFrame): DataFrame con ventas después del ML
    
    Returns:
        dict: Métricas de impacto en ventas
    """
    # Calcular totales de ventas
    total_ventas_antes = ventas_antes_df['cantidad'].sum()
    total_ventas_despues = ventas_despues_df['cantidad'].sum()
    
    # Calcular incremento porcentual
    if total_ventas_antes > 0:
        incremento_porcentual = (total_ventas_despues - total_ventas_antes) / total_ventas_antes * 100
    else:
        incremento_porcentual = 0
    
    # Valor en dinero de las ventas
    valor_ventas_antes = (
        ventas_antes_df['cantidad'] * ventas_antes_df['precio_unitario']
    ).sum()
    
    valor_ventas_despues = (
        ventas_despues_df['cantidad'] * ventas_despues_df['precio_unitario']
    ).sum()
    
    incremento_valor = valor_ventas_despues - valor_ventas_antes
    
    return {
        'total_ventas_antes': total_ventas_antes,
        'total_ventas_despues': total_ventas_despues,
        'incremento_porcentual': incremento_porcentual,
        'valor_ventas_antes': valor_ventas_antes,
        'valor_ventas_despues': valor_ventas_despues,
        'incremento_valor': incremento_valor
    }