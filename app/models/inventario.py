from app import db
from datetime import datetime

class Inventario(db.Model):
    """Modelo para la tabla de gestión de inventario."""
    __tablename__ = 'inventario'
    
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    stock_actual = db.Column(db.Integer, nullable=False)
    stock_minimo = db.Column(db.Integer, default=0)
    stock_optimo = db.Column(db.Integer)
    ubicacion = db.Column(db.String(100))
    ultima_actualizacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Inventario de Producto {self.producto_id} - Stock: {self.stock_actual}>'
    
    def to_dict(self):
        """Convertir objeto a diccionario para API/JSON."""
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'stock_actual': self.stock_actual,
            'stock_minimo': self.stock_minimo,
            'stock_optimo': self.stock_optimo,
            'ubicacion': self.ubicacion,
            'ultima_actualizacion': self.ultima_actualizacion.isoformat()
        }