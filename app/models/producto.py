from app import db
from datetime import datetime

class Producto(db.Model):
    """Modelo para la tabla de productos (autopartes)."""
    __tablename__ = 'productos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True)
    categoria = db.Column(db.String(100), nullable=False)
    modelo_carro = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    es_producto_nuevo = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    inventario = db.relationship('Inventario', backref='producto', uselist=False)
    ventas = db.relationship('Venta', backref='producto', lazy='dynamic')
    predicciones = db.relationship('Prediccion', backref='producto', lazy='dynamic')
    
    def __repr__(self):
        return f'<Producto {self.codigo} - {self.categoria} para {self.modelo_carro}>'
    
    def to_dict(self):
        """Convertir objeto a diccionario para API/JSON."""
        return {
            'id': self.id,
            'codigo': self.codigo,
            'categoria': self.categoria,
            'modelo_carro': self.modelo_carro,
            'descripcion': self.descripcion,
            'precio_unitario': float(self.precio_unitario),
            'es_producto_nuevo': self.es_producto_nuevo,
            'stock_actual': self.inventario.stock_actual if self.inventario else 0
        }
    
    @classmethod
    def buscar_por_categoria(cls, categoria):
        """Buscar productos por categoría."""
        return cls.query.filter_by(categoria=categoria).all()
    
    @classmethod
    def buscar_por_modelo(cls, modelo_carro):
        """Buscar productos por modelo de carro."""
        return cls.query.filter_by(modelo_carro=modelo_carro).all()