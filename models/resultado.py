from app import db
from datetime import datetime

class ResultadoComparativo(db.Model):
    """Modelo para almacenar los resultados comparativos pre/post ML."""
    __tablename__ = 'resultados_comparativos'
    
    id = db.Column(db.Integer, primary_key=True)
    fecha_evaluacion = db.Column(db.DateTime, default=datetime.utcnow)
    periodo_inicio = db.Column(db.Date, nullable=False)
    periodo_fin = db.Column(db.Date, nullable=False)
    mae = db.Column(db.Numeric(10, 2))
    rmse = db.Column(db.Numeric(10, 2))
    reduccion_inventario_excedente = db.Column(db.Numeric(5, 2))
    incremento_ventas = db.Column(db.Numeric(5, 2))
    notas = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Resultado Comparativo {self.id} - Período: {self.periodo_inicio} a {self.periodo_fin}>'
    
    def to_dict(self):
        """Convertir objeto a diccionario para API/JSON."""
        return {
            'id': self.id,
            'fecha_evaluacion': self.fecha_evaluacion.isoformat(),
            'periodo_inicio': self.periodo_inicio.isoformat(),
            'periodo_fin': self.periodo_fin.isoformat(),
            'mae': float(self.mae) if self.mae else None,
            'rmse': float(self.rmse) if self.rmse else None,
            'reduccion_inventario_excedente': float(self.reduccion_inventario_excedente) if self.reduccion_inventario_excedente else None,
            'incremento_ventas': float(self.incremento_ventas) if self.incremento_ventas else None,
            'notas': self.notas
        }
    
    @classmethod
    def obtener_ultimo_resultado(cls):
        """Obtener el último resultado comparativo registrado."""
        return cls.query.order_by(cls.fecha_evaluacion.desc()).first()
    
    @classmethod
    def resultados_por_periodo(cls, fecha_inicio, fecha_fin):
        """Obtener resultados comparativos para un período específico."""
        return cls.query.filter(
            cls.periodo_inicio >= fecha_inicio,
            cls.periodo_fin <= fecha_fin
        ).all()