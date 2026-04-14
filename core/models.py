from django.db import models
from django.contrib.auth.models import User
from PIL import Image
import os
from django.utils.crypto import get_random_string  # ✅ necesario para generar el CUFE

# ---------------- Perfil ----------------
class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cedula = models.CharField(max_length=20)
    numero_contacto = models.CharField(max_length=15)
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True, verbose_name="Foto de perfil")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.foto_perfil:
            img = Image.open(self.foto_perfil.path)
            img.thumbnail((300, 300))
            img.save(self.foto_perfil.path)

    def delete(self, *args, **kwargs):
        if self.foto_perfil and os.path.isfile(self.foto_perfil.path):
            os.remove(self.foto_perfil.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Perfil de {self.user.username}"


# ---------------- Categoría ----------------
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la categoría")

    def __str__(self):
        return self.nombre


# ---------------- Producto ----------------
class Producto(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del producto")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código del producto")
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio",
        null=True,
        blank=True
    )
    descripcion = models.TextField(max_length=500, verbose_name="Descripción breve")
    descripcion = models.TextField(max_length=500, verbose_name="Descripción breve")
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, verbose_name="Categoría", related_name="productos")
    cantidad = models.PositiveIntegerField(default=0, verbose_name="Cantidad en inventario")
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    disponible = models.BooleanField(default=True, verbose_name="¿Está disponible?")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.imagen:
            img_path = self.imagen.path
            img = Image.open(img_path)
            img = img.resize((686, 386), Image.LANCZOS)
            img.save(img_path)

    def delete(self, *args, **kwargs):
        if self.imagen and os.path.isfile(self.imagen.path):
            os.remove(self.imagen.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.nombre


# ---------------- Pedido ----------------
class Pedido(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('cancelado', 'Cancelado'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=150)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255)
    metodo_pago = models.CharField(max_length=50)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.username}"


# ---------------- PedidoItem ----------------
class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, related_name="items", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"


# ---------------- Generar CUFE ----------------
def generar_cufe():
    """Genera un código único de factura (CUFE) de 64 caracteres."""
    return get_random_string(length=64)


# ---------------- Factura ----------------
class Factura(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='factura')
    cliente = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    direccion = models.CharField(max_length=255)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    iva = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Datos empresa
    nit_empresa = models.CharField(max_length=20, default='900123456-1')
    nombre_empresa = models.CharField(max_length=100, default='Lacteos Aqui Es Purita')
    direccion_empresa = models.CharField(max_length=150, default='cra 12 #34-56, La Cumbre Valle Del Cauca')
    correo_empresa = models.EmailField(default='lacteospurita@gmail.com')
    telefono_empresa = models.CharField(max_length=20, default='+57 3000000000')
    resolucion_dian = models.CharField(max_length=50, default='18760000000000')
    prefijo_factura = models.CharField(max_length=10, default='LP')

    # Datos DIAN
    forma_pago = models.CharField(max_length=50, default='Contado')  # contado / crédito
    medio_pago = models.CharField(max_length=50, default='Efectivo')  # efectivo / transferencia / tarjeta
    cufe = models.CharField(max_length=64, unique=True, default=generar_cufe)

    @property
    def numero_factura(self):
        return f"{self.prefijo_factura}{self.id:04d}"

    def __str__(self):
        return f"Factura {self.numero_factura} - {self.cliente.username}"


# ---------------- FacturaItem ----------------
class FacturaItem(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='items')
    producto = models.CharField(max_length=100)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"


# ---------------- Notificación ----------------
class Notificacion(models.Model):
    mensaje = models.CharField(max_length=255)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="notificaciones")
    fecha = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.producto.nombre} - {self.mensaje}"


# ---------------- Auditoría ----------------
class Auditoria(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tipo_usuario = models.CharField(max_length=20, blank=True, null=True)  # Admin / Cliente

    accion = models.CharField(max_length=255)
    modelo_afectado = models.CharField(max_length=100, null=True, blank=True)
    objeto_id = models.IntegerField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    # --- Nuevos campos ---
    producto = models.CharField(max_length=255, null=True, blank=True)
    cantidad = models.IntegerField(null=True, blank=True)
    detalle = models.TextField(null=True, blank=True)

    def __str__(self):
        nombre = self.usuario.username if self.usuario else "Anónimo"
        return f"{nombre} ({self.tipo_usuario}) - {self.accion} - {self.fecha.strftime('%Y-%m-%d %H:%M:%S')}"
