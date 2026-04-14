from decimal import Decimal
from .models import Producto

class Carrito:
    def __init__(self, request):
        self.session = request.session
        carrito = self.session.get('carrito')
        if not carrito:
            carrito = self.session['carrito'] = {}
        self.carrito = carrito

    def add(self, producto):
        producto_id = str(producto.id)
        if producto_id not in self.carrito:
            self.carrito[producto_id] = {'cantidad': 1}
        else:
            self.carrito[producto_id]['cantidad'] += 1
        self.save()

    def remove(self, producto):
        producto_id = str(producto.id)
        if producto_id in self.carrito:
            del self.carrito[producto_id]
            self.save()

    def decrease(self, producto):
        producto_id = str(producto.id)
        if producto_id in self.carrito:
            self.carrito[producto_id]['cantidad'] -= 1
            if self.carrito[producto_id]['cantidad'] <= 0:
                self.remove(producto)
            self.save()

    def clear(self):
        self.session['carrito'] = {}
        self.session.modified = True

    def save(self):
        self.session['carrito'] = self.carrito
        self.session.modified = True

    def __iter__(self):
        for product_id, item in self.carrito.items():
            producto = Producto.objects.get(id=product_id)
            precio = Decimal(producto.precio or 0)
            yield {
                'producto': producto,
                'cantidad': item['cantidad'],
                'subtotal': precio * item['cantidad']
            }

    # === MÉTODOS PARA FACTURA ===
    def get_subtotal(self):
        """Subtotal sin IVA"""
        return sum(
            Decimal(producto.precio or 0) * item['cantidad']
            for product_id, item in self.carrito.items()
            for producto in [Producto.objects.get(id=product_id)]
        )

    def get_iva(self, porcentaje=0.19):
        """Calcula el IVA (19% por defecto)"""
        porcentaje = Decimal(str(porcentaje))
        return self.get_subtotal() * porcentaje

    def get_total(self, porcentaje=0.19):
        """Subtotal + IVA"""
        return self.get_subtotal() + self.get_iva(porcentaje)
