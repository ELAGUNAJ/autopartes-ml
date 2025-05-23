import os
import sys
from pathlib import Path
import datetime
import random

# Añadir el directorio raíz al Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from app import create_app, db
from app.models.usuario import Usuario
from app.models.producto import Producto
from app.models.inventario import Inventario
from app.models.venta import Venta

# Categorías de ejemplo
CATEGORIAS = [
    "Faros delanteros", 
    "Faros neblineros", 
    "Luces traseras", 
    "Parachoques delanteros", 
    "Parachoques traseros", 
    "Mandiles delanteros", 
    "Guardafangos"
]

# Modelos de carros
MODELOS_CARRO = [
    "Toyota Corolla", 
    "Honda Civic", 
    "Nissan Sentra", 
    "Hyundai Elantra", 
    "Kia Rio", 
    "Suzuki Swift", 
    "Chevrolet Spark"
]

def reset_database():
    """Reinicia la base de datos y crea todas las tablas."""
    app = create_app()
    
    with app.app_context():
        # Eliminar todas las tablas existentes
        print("Eliminando tablas existentes...")
        db.drop_all()
        
        # Crear todas las tablas nuevamente
        print("Creando tablas nuevas...")
        db.create_all()
        
        # Crear usuario administrador
        print("Creando usuario administrador...")
        admin = Usuario(
            username='admin',
            email='admin@example.com',
            nombre='Administrador',
            apellido='Sistema',
            rol='admin',
            activo=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Crear usuario vendedor
        vendedor = Usuario(
            username='vendedor',
            email='vendedor@example.com',
            nombre='Juan',
            apellido='Pérez',
            rol='vendedor',
            activo=True
        )
        vendedor.set_password('vendedor123')
        db.session.add(vendedor)
        
        # Crear productos de ejemplo
        print("Creando productos e inventario de ejemplo...")
        productos_creados = []
        
        # Crear 20 productos de ejemplo
        for i in range(1, 21):
            categoria = random.choice(CATEGORIAS)
            modelo_carro = random.choice(MODELOS_CARRO)
            
            producto = Producto(
                codigo=f"P{i:03d}",
                categoria=categoria,
                modelo_carro=modelo_carro,
                descripcion=f"Descripción del producto {i} - {categoria} para {modelo_carro}",
                precio_unitario=random.uniform(50, 500),
                es_producto_nuevo=random.choice([True, False])
            )
            db.session.add(producto)
            db.session.flush()  # Para obtener el ID
            productos_creados.append(producto)
            
            # Crear inventario para este producto
            inventario = Inventario(
                producto_id=producto.id,
                stock_actual=random.randint(0, 50),
                stock_minimo=5,
                stock_optimo=20,
                ubicacion=f"Estante {random.choice(['A', 'B', 'C'])}-{random.randint(1, 10)}"
            )
            db.session.add(inventario)
        
        # Crear ventas de ejemplo
        print("Creando ventas de ejemplo...")
        fecha_actual = datetime.datetime.now()
        
        # Crear 100 ventas en los últimos 90 días
        for i in range(100):
            producto = random.choice(productos_creados)
            cantidad = random.randint(1, 5)
            precio_unitario = float(producto.precio_unitario)
            
            # Fecha aleatoria en los últimos 90 días
            dias_atras = random.randint(0, 90)
            fecha_venta = fecha_actual - datetime.timedelta(days=dias_atras)
            
            venta = Venta(
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                precio_total=cantidad * precio_unitario,
                fecha_venta=fecha_venta,
                usuario_id=vendedor.id
            )
            db.session.add(venta)
        
        # Guardar todos los cambios
        db.session.commit()
        print("Base de datos reiniciada y poblada con datos de ejemplo.")

if __name__ == "__main__":
    reset_database()