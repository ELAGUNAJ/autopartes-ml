# Importar todos los modelos para que Flask-Migrate los detecte
from app.models.usuario import Usuario
from app.models.producto import Producto
from app.models.inventario import Inventario
from app.models.venta import Venta
from app.models.prediccion import Prediccion
from app.models.resultado import ResultadoComparativo