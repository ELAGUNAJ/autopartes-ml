import pandas as pd
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def entrenar_modelo(features_df):
    """
    Entrena un modelo ExtraTreesRegressor para predecir ventas futuras.
    
    Args:
        features_df (pd.DataFrame): DataFrame con características procesadas
    
    Returns:
        tuple: (modelo entrenado, importancia de features, métricas de evaluación)
    """
    # Preparar X e y
    # La variable objetivo es la cantidad vendida
    X = features_df.drop(columns=['cantidad'], errors='ignore')
    y = features_df['cantidad']
    
    # Guardar nombres de columnas para referencia de importancia de features
    feature_names = X.columns.tolist()
    
    # Dividir en conjuntos de entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Entrenar modelo ExtraTreesRegressor
    model = ExtraTreesRegressor(
        n_estimators=100,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=42,
        n_jobs=-1  # Usar todos los núcleos disponibles
    )
    
    model.fit(X_train, y_train)
    
    # Evaluar modelo
    y_pred = model.predict(X_test)
    
    # Calcular métricas
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    # Obtener importancia de features
    importancias = model.feature_importances_
    importancias_features = dict(zip(feature_names, importancias))
    
    # Ordenar por importancia
    importancias_features = {k: v for k, v in sorted(
        importancias_features.items(), 
        key=lambda item: item[1], 
        reverse=True
    )}
    
    # Métricas para devolver
    metricas = {
        'mae': mae,
        'rmse': rmse,
        'r2': r2
    }
    
    return model, importancias_features, metricas