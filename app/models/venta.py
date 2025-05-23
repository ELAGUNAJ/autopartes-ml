from app import db
from datetime import datetime

class Venta(db.Model):
    """Modelo para la tabla de registro de ventas."""
    __tablename__ = 'ventas'
    
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    precio_total = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_venta = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    @property
    def fecha(self):
        """Alias para fecha_venta para mantener compatibilidad."""
        return self.fecha_venta
    
    def __repr__(self):
        return f'<Venta {self.id} - Producto: {self.producto_id}, Cantidad: {self.cantidad}>'
    
    # Resto del código...
    
    def to_dict(self):
        """Convertir objeto a diccionario para API/JSON."""
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'cantidad': self.cantidad,
            'precio_unitario': float(self.precio_unitario),
            'precio_total': float(self.precio_total),
            'fecha_venta': self.fecha_venta.isoformat(),
            'usuario_id': self.usuario_id
        }