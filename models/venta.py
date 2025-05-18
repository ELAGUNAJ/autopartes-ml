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
    
    def __repr__(self):
        return f'<Venta {self.id} - Producto: {self.producto_id}, Cantidad: {self.cantidad}>'
    
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
    
    @classmethod
    def ventas_por_periodo(cls, fecha_inicio, fecha_fin):
        """Obtener ventas dentro de un período específico."""
        return cls.query.filter(
            cls.fecha_venta >= fecha_inicio,
            cls.fecha_venta <= fecha_fin
        ).all()
    
    @classmethod
    def ventas_por_producto(cls, producto_id, fecha_inicio=None, fecha_fin=None):
        """Obtener ventas de un producto específico con filtro opcional de fechas."""
        query = cls.query.filter_by(producto_id=producto_id)
        
        if fecha_inicio:
            query = query.filter(cls.fecha_venta >= fecha_inicio)
        if fecha_fin:
            query = query.filter(cls.fecha_venta <= fecha_fin)
        
        return query.all()
    
    @classmethod
    def total_ventas_por_categoria(cls, categoria, fecha_inicio=None, fecha_fin=None):
        """Calcular el total de ventas por categoría de productos."""
        from app.models.producto import Producto
        
        query = db.session.query(
            db.func.sum(cls.precio_total).label('total_ventas')
        ).join(Producto).filter(Producto.categoria == categoria)
        
        if fecha_inicio:
            query = query.filter(cls.fecha_venta >= fecha_inicio)
        if fecha_fin:
            query = query.filter(cls.fecha_venta <= fecha_fin)
        
        result = query.first()
        return float(result.total_ventas) if result.total_ventas else 0.0