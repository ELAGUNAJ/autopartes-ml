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
    
    def actualizar_stock(self, nueva_cantidad):
        """Actualizar el stock de un producto."""
        self.stock_actual = nueva_cantidad
        self.ultima_actualizacion = datetime.utcnow()
        db.session.commit()
    
    def calcular_exceso_stock(self):
        """Calcular si hay exceso de stock basado en stock óptimo."""
        if self.stock_optimo is None:
            return 0
        exceso = max(0, self.stock_actual - self.stock_optimo)
        return exceso
    
    def verificar_stock_bajo(self):
        """Verificar si el stock está por debajo del mínimo."""
        return self.stock_actual < self.stock_minimo
    
    @classmethod
    def productos_con_exceso_stock(cls):
        """Obtener lista de productos con exceso de stock."""
        inventarios = cls.query.filter(cls.stock_optimo != None).all()
        return [inv for inv in inventarios if inv.calcular_exceso_stock() > 0]
    
    @classmethod
    def productos_con_stock_bajo(cls):
        """Obtener lista de productos con stock bajo."""
        return cls.query.filter(cls.stock_actual < cls.stock_minimo).all()