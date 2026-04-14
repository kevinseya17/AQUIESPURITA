from django.contrib import admin
from .models import Producto, Categoria, Pedido, PedidoItem
from django.contrib import admin
from .models import (
    Perfil, Categoria, Producto, Pedido, PedidoItem,
    Factura, FacturaItem, Notificacion
)
from .models import Auditoria
# === Categoría ===
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


# === Producto ===
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'precio', 'categoria', 'cantidad', 'disponible')
    search_fields = ('nombre', 'codigo', 'categoria__nombre')
    list_filter = ('categoria', 'disponible')


# === PedidoItem Inline (para ver los productos dentro del pedido) ===
class PedidoItemInline(admin.TabularInline):
    model = PedidoItem
    extra = 0
    readonly_fields = ('producto', 'cantidad', 'precio', 'subtotal_display')

    def subtotal_display(self, obj):
        return f"${obj.subtotal():.2f}"
    subtotal_display.short_description = 'Subtotal'


# === Pedido ===
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha', 'metodo_pago', 'total', 'estado')
    list_filter = ('estado', 'metodo_pago', 'fecha')
    search_fields = ('usuario__username', 'nombre', 'email')
    inlines = [PedidoItemInline]
    list_editable = ('estado',)  # 👈 permite cambiar el estado directamente desde la lista

# === PedidoItem ===
@admin.register(PedidoItem)
class PedidoItemAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'producto', 'cantidad', 'precio', 'subtotal_display')

    def subtotal_display(self, obj):
        return f"${obj.subtotal():.2f}"
    subtotal_display.short_description = 'Subtotal'

class FacturaItemInline(admin.TabularInline):
    model = FacturaItem
    extra = 0

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "total", "fecha")
    inlines = [FacturaItemInline]


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'accion', 'modelo_afectado', 'objeto_id', 'fecha')
    list_filter = ('modelo_afectado', 'fecha')
    search_fields = ('usuario__username', 'accion', 'modelo_afectado')
    readonly_fields = ('usuario', 'accion', 'modelo_afectado', 'objeto_id', 'fecha')

    def has_add_permission(self, request):
        # Evita que se creen auditorías manualmente desde el admin
        return False