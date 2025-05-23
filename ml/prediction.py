import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.ml.preprocessing import preparar_datos
from app.ml.feature_engineering import crear_features

def generar_predicciones(model, ventas_df, inventario_df, dias_prediccion=30):
    """
    Genera predicciones de ventas futuras usando el modelo entrenado.
    
    Args:
        model: Modelo entrenado (ExtraTreesRegressor)
        ventas_df (pd.DataFrame): DataFrame con datos históricos de ventas
        inventario_df (pd.DataFrame): DataFrame con datos actuales de inventario
        dias_prediccion (int): Número de días para los que se generarán predicciones
    
    Returns:
        pd.DataFrame: DataFrame con predicciones por producto
    """
    # Preparar datos
    datos_procesados = preparar_datos(ventas_df, inventario_df)
    
    # Crear características
    features_df = crear_features(datos_procesados)
    
    # Obtener lista única de productos
    productos = features_df['producto_id'].unique()
    
    # Obtener la fecha más reciente de los datos
    fecha_ultima = ventas_df['fecha_venta'].max()
    
    # Resultados de predicciones
    resultados = []
    
    for producto_id in productos:
        # Filtrar features para este producto
        producto_features = features_df[features_df['producto_id'] == producto_id].copy()
        
        # Si no hay suficientes datos para este producto, omitir
        if len(producto_features) < 7:  # Mínimo una semana de datos
            continue
        
        # Obtener las últimas métricas para este producto
        ultimas_metricas = producto_features.sort_values('producto_id').iloc[-1].copy()
        
        # Predecir ventas futuras
        # Para simplificar, usamos las métricas más recientes para todos los días futuros
        # En un sistema más avanzado, se harían predicciones día a día actualizando las métricas
        X_pred = pd.DataFrame([ultimas_metricas])
        
        # Eliminar la columna 'cantidad' que es nuestra variable objetivo
        if 'cantidad' in X_pred.columns:
            X_pred = X_pred.drop(columns=['cantidad'])
        
        # Eliminar producto_id para la predicción
        if 'producto_id' in X_pred.columns:
            X_pred = X_pred.drop(columns=['producto_id'])
        
        # Realizar predicción
        cantidad_predicha = model.predict(X_pred)[0]
        
        # No permitir predicciones negativas
        cantidad_predicha = max(0, cantidad_predicha)
        
        # Multiplicar por el número de días para obtener la predicción total del período
        cantidad_predicha_total = cantidad_predicha * dias_prediccion
        
        # Añadir a resultados
        producto_info = ventas_df[ventas_df['producto_id'] == producto_id].iloc[0]
        resultados.append({
            'producto_id': producto_id,
            'categoria': producto_info['categoria'] if 'categoria' in producto_info else 'desconocida',
            'modelo_carro': producto_info['modelo_carro'] if 'modelo_carro' in producto_info else 'desconocido',
            'cantidad_predicha': cantidad_predicha_total,
            'cantidad_predicha_diaria': cantidad_predicha,
            'dias_prediccion': dias_prediccion,
            'confianza': 0.8,  # Nivel de confianza predeterminado
            'fecha_inicio': fecha_ultima + timedelta(days=1),
            'fecha_fin': fecha_ultima + timedelta(days=dias_prediccion)
        })
    
    return pd.DataFrame(resultados)

def generar_recomendaciones_inventario(predicciones_df, inventario_df):
    """
    Genera recomendaciones de inventario basadas en las predicciones de ventas.
    
    Args:
        predicciones_df (pd.DataFrame): DataFrame con predicciones de ventas
        inventario_df (pd.DataFrame): DataFrame con datos actuales de inventario
    
    Returns:
        pd.DataFrame: DataFrame con recomendaciones de inventario
    """
    # Unir predicciones con inventario actual
    df = pd.merge(
        predicciones_df,
        inventario_df,
        on='producto_id',
        how='inner'
    )
    
    # Calcular recomendaciones
    df['inventario_recomendado'] = df.apply(
        lambda row: max(
            row['stock_minimo'],
            row['cantidad_predicha'] * 1.2  # Factor de seguridad del 20%
        ),
        axis=1
    )
    
    # Calcular ajuste necesario
    df['ajuste_inventario'] = df['inventario_recomendado'] - df['stock_actual']
    
    # Recomendación de acción
    df['accion_recomendada'] = df.apply(
        lambda row: 'Comprar' if row['ajuste_inventario'] > 0 else 'Reducir',
        axis=1
    )
    
    # Calcular impacto económico
    df['valor_ajuste'] = df['ajuste_inventario'] * df['precio_unitario']
    
    # Ordenar por prioridad (valor absoluto del ajuste)
    df['prioridad'] = df['valor_ajuste'].abs()
    df = df.sort_values('prioridad', ascending=False)
    
    return df[['producto_id', 'categoria', 'modelo_carro', 
               'stock_actual', 'inventario_recomendado', 
               'ajuste_inventario', 'accion_recomendada', 
               'valor_ajuste', 'prioridad']]