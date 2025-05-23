from app import db
from datetime import datetime

class Prediccion(db.Model):
    """Modelo para la tabla de predicciones generadas por ML."""
    __tablename__ = 'predicciones'
    
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad_predicha = db.Column(db.Integer, nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    confianza = db.Column(db.Numeric(5, 2))
    fecha_prediccion = db.Column(db.DateTime, default=datetime.utcnow)
    modelo_version = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<Predicción para Producto {self.producto_id} - Cantidad: {self.cantidad_predicha}>'
    
    def to_dict(self):
        """Convertir objeto a diccionario para API/JSON."""
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'cantidad_predicha': self.cantidad_predicha,
            'fecha_inicio': self.fecha_inicio.isoformat(),
            'fecha_fin': self.fecha_fin.isoformat(),
            'confianza': float(self.confianza) if self.confianza else None,
            'fecha_prediccion': self.fecha_prediccion.isoformat(),
            'modelo_version': self.modelo_version
        }
    
    @classmethod
    def obtener_ultima_prediccion(cls, producto_id):
        """Obtener la última predicción para un producto específico."""
        return cls.query.filter_by(producto_id=producto_id).order_by(cls.fecha_prediccion.desc()).first()
    
    @classmethod
    def predicciones_por_periodo(cls, fecha_inicio, fecha_fin):
        """Obtener predicciones para un período específico."""
        return cls.query.filter(
            cls.fecha_inicio >= fecha_inicio,
            cls.fecha_fin <= fecha_fin
        ).all()