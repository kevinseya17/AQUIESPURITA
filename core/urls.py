"""login URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""login URL Configuration"""

"""login URL Configuration"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import (
    home, products, register, perfil, editar_perfil,
    login_custom, admin_dashboard, admin_usuarios, admin_productos,
    actualizar_usuario, actualizar_producto, agregar_producto,
    eliminar_producto, agregar_usuario, eliminar_usuario,
    cart_detail, add_to_cart, remove_from_cart,
    decrease_from_cart, clear_cart, product_detail,
    checkout, procesar_pago, factura,
    reporte_diario, reporte_diario_pdf, reporte_diario_excel,  # ✅ Reportes
    log_auditoria, exportar_log_excel  # ✅ Auditoría (nuevo)
)

urlpatterns = [
    # === PRINCIPAL Y AUTENTICACIÓN ===
    path('', home, name='home'),
    path('products/', products, name='products'),
    path('register/', register, name='register'),
    path('perfil/', perfil, name='perfil'),
    path('perfil/editar/', editar_perfil, name='editar_perfil'),
    path('actualizar-perfil/', editar_perfil, name='actualizar_perfil'),
    path('login/', login_custom, name='login'),

    # === ADMINISTRADOR ===
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/usuarios/', admin_usuarios, name='admin_usuarios'),
    path('admin/productos/', admin_productos, name='admin_productos'),

    # === USUARIOS ===
    path('admin/usuarios/actualizar/<int:usuario_id>/', actualizar_usuario, name='actualizar_usuario'),
    path('admin/usuarios/eliminar/<int:usuario_id>/', eliminar_usuario, name='eliminar_usuario'),
    path('admin/usuarios/agregar/', agregar_usuario, name='agregar_usuario'),

    # === PRODUCTOS ===
    path('admin/productos/actualizar/<int:producto_id>/', actualizar_producto, name='actualizar_producto'),
    path('admin/productos/eliminar/<int:producto_id>/', eliminar_producto, name='eliminar_producto'),
    path('admin/productos/agregar/', agregar_producto, name='agregar_producto'),

    # === CARRITO ===
    path("core/cart/", cart_detail, name="cart_detail"),
    path("core/cart/add/<int:producto_id>/", add_to_cart, name="add_to_cart"),
    path("core/cart/remove/<int:producto_id>/", remove_from_cart, name="remove_from_cart"),
    path("core/cart/decrease/<int:producto_id>/", decrease_from_cart, name="decrease_from_cart"),
    path("core/cart/clear/", clear_cart, name="clear_cart"),

    # === PRODUCTO DETALLE ===
    path("producto/<int:producto_id>/", product_detail, name="product_detail"),

    # === CHECKOUT Y PAGO ===
    path("checkout/", checkout, name="checkout"),
    path("procesar-pago/", procesar_pago, name="procesar_pago"),

    # === FACTURA ===
    path("factura/<int:pedido_id>/", factura, name="factura"),

    # === REPORTES ===
    path('admin/reporte-diario/', reporte_diario, name='reporte_diario'),
    path('admin/reporte-diario/pdf/', reporte_diario_pdf, name='reporte_diario_pdf'),
    path('admin/reporte-diario/excel/', reporte_diario_excel, name='reporte_diario_excel'),

    # === AUDITORÍA / LOG DE USABILIDAD ===
    path('admin/auditoria/', log_auditoria, name='log_auditoria'), 
    path('admin/auditoria/excel/', exportar_log_excel, name='exportar_log_excel'),  
]

# Archivos multimedia (solo en modo DEBUG)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
