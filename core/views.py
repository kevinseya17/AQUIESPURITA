from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Avg
from .models import Perfil, Producto, Categoria
from .cart import Carrito
from .forms import CustomUserCreationForm, EditarPerfilForm
from django.db.models import Sum, F
from django.db import transaction
import uuid
import pytz
import qrcode
import io
import base64
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from openpyxl import Workbook
from .models import Auditoria  # 👈 importante para acceder al modelo
# utils.py
from .models import Auditoria
from .utils import registrar_accion
from .models import Pedido, PedidoItem, Producto, Factura, FacturaItem
from datetime import datetime






# -------------------- Vistas generales --------------------

@login_required
def home(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')
    return render(request, 'core/home.html')

from django.shortcuts import render
from .models import Producto

def products(request):
    categoria_nombre = request.GET.get('categoria')
    categoria_obj = None
    
    if categoria_nombre:
        try:
            categoria_obj = Categoria.objects.get(nombre__iexact=categoria_nombre)
            productos = Producto.objects.filter(
                categoria=categoria_obj,
                disponible=True,
                cantidad__gt=0
            )
        except Categoria.DoesNotExist:
            productos = Producto.objects.filter(disponible=True, cantidad__gt=0)
    else:
        productos = Producto.objects.filter(disponible=True, cantidad__gt=0)

    return render(request, 'core/products.html', {
        'productos': productos,
        'categoria': categoria_obj,  # Enviamos el objeto completo, no solo el nombre
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Perfil, Pedido

@login_required
def perfil(request):
    user = request.user

    # Intentar obtener el perfil asociado
    try:
        perfil = user.perfil
    except Perfil.DoesNotExist:
        perfil = None

    # Traer los pedidos del usuario
    pedidos = Pedido.objects.filter(usuario=user).order_by('-fecha')

    context = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'cedula': perfil.cedula if perfil else 'No disponible',
        'numero_contacto': perfil.numero_contacto if perfil else 'No disponible',
        'pedidos': pedidos,  # ✅ se usa en el HTML
    }

    return render(request, 'core/perfil.html', context)


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import EditarPerfilForm
from .models import Perfil

@login_required
def editar_perfil(request):
    user = request.user
    perfil, created = Perfil.objects.get_or_create(user=user)

    if request.method == 'POST':
        data = request.POST.copy()
        data['email'] = user.email  
        form = EditarPerfilForm(data, request.FILES, instance=user)

        if form.is_valid():
            # Guarda valores actuales para comparar cambios
            old_first_name = user.first_name
            old_last_name = user.last_name
            old_cedula = perfil.cedula
            old_numero_contacto = perfil.numero_contacto
            old_foto = perfil.foto_perfil.name if perfil.foto_perfil else None

            # --- Guardar cambios ---
            user = form.save(commit=False)

            perfil.cedula = form.cleaned_data.get('cedula')
            perfil.numero_contacto = form.cleaned_data.get('numero_contacto')

            nueva_foto = form.cleaned_data.get('foto_perfil')
            if nueva_foto:
                perfil.foto_perfil = nueva_foto

            user.save()
            perfil.save()

            # ===================================================================
            # ======================== REGISTRO DE AUDITORÍA ====================
            # ===================================================================

            # Nombre del usuario
            if request.user and request.user.is_authenticated:
                nombre_usuario = f"{request.user.first_name} {request.user.last_name}".strip()
                if not nombre_usuario:
                    nombre_usuario = request.user.username
            else:
                nombre_usuario = "Usuario anónimo"

            # Fecha y hora
            fecha_actual = timezone.localtime(timezone.now()).strftime("%Y-%m-%d")
            hora_actual = timezone.localtime(timezone.now()).strftime("%H:%M:%S")

            # Detectar qué campos cambiaron
            cambios = []

            if old_first_name != form.cleaned_data.get('first_name'):
                cambios.append("nombre")

            if old_last_name != form.cleaned_data.get('last_name'):
                cambios.append("apellido")

            if old_cedula != form.cleaned_data.get('cedula'):
                cambios.append("cédula")

            if old_numero_contacto != form.cleaned_data.get('numero_contacto'):
                cambios.append("número de contacto")

            new_foto_name = nueva_foto.name if nueva_foto else None
            if new_foto_name and new_foto_name != old_foto:
                cambios.append("foto de perfil")

            cambios_texto = ", ".join(cambios) if cambios else "sin cambios detectados"

            detalle = (
                f"El {fecha_actual} a las {hora_actual}, {nombre_usuario} actualizó su perfil "
                f"(ID del perfil: {perfil.id}). "
                f"Campos modificados: {cambios_texto}."
            )

            registrar_accion(
                request,
                accion="Actualizó su perfil",
                modelo_afectado="Perfil",
                objeto_id=perfil.id,
                detalle=detalle
            )

            # ===================================================================

            messages.success(request, "✅ Tu perfil se ha actualizado correctamente.")
            return redirect('perfil')

        else:
            messages.error(request, "⚠️ Por favor, corrige los errores del formulario.")

    else:
        form = EditarPerfilForm(instance=user)

    return render(request, 'core/editar_perfil.html', {
        'form': form,
        'perfil': perfil,
    })



def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            perfil = Perfil.objects.create(
                user=user,
                cedula=form.cleaned_data['cedula'],
                numero_contacto=form.cleaned_data['numero_contacto']
            )

            # ============================
            #     REGISTRO DE AUDITORÍA
            # ============================
            fecha_actual = timezone.localtime(timezone.now()).strftime("%Y-%m-%d")
            hora_actual = timezone.localtime(timezone.now()).strftime("%H:%M:%S")

            detalle = (
                f"El {fecha_actual} a las {hora_actual}, el usuario {user.username} "
                f"creó su cuenta. "
                f"Cédula: {perfil.cedula}, "
                f"Contacto: {perfil.numero_contacto}."
            )

            registrar_accion(
                request,
                accion=f"Registro de nuevo usuario",
                modelo_afectado="User",
                objeto_id=user.id,
                detalle=detalle
            )
            # ============================

            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            login(request, user)
            messages.success(request, "🎉 Registro exitoso. Bienvenido.")
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


def login_custom(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # ===============================================
            # REGISTRO DE AUDITORÍA - INICIO DE SESIÓN
            # ===============================================

            tipo = "Administrador" if (user.is_staff or user.is_superuser) else "Cliente"

            # Nombre visible del usuario
            nombre_usuario = f"{user.first_name} {user.last_name}".strip()
            if not nombre_usuario:
                nombre_usuario = user.username

            # Fecha y hora local
            fecha_actual = timezone.localtime(timezone.now()).strftime("%Y-%m-%d")
            hora_actual = timezone.localtime(timezone.now()).strftime("%H:%M:%S")

            detalle = (
                f"El {fecha_actual} a las {hora_actual}, el usuario {nombre_usuario} "
                f"inició sesión como {tipo} (ID: {user.id})."
            )

            registrar_accion(
                request,
                accion="Inicio de sesión",
                modelo_afectado="User",
                objeto_id=user.id,
                detalle=detalle
            )
            # ===============================================

            # Redirigir según rol
            if user.is_superuser or user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('home')

        else:
            return render(
                request,
                'registration/login.html',
                {'error': 'Usuario o contraseña incorrectos'}
            )

    return render(request, 'registration/login.html')

# -------------------- Panel de administrador --------------------

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_dashboard(request):
    total_usuarios = User.objects.count()
    total_productos = Producto.objects.count()
    total_categorias = Categoria.objects.count()
    valor_total_inventario = Producto.objects.aggregate(
        total=Sum(F('precio') * F('cantidad'))
    )['total'] or 0

    ultimos_usuarios = User.objects.order_by('-date_joined')[:5]
    ultimos_productos = Producto.objects.order_by('-id')[:5]

    # 🔍 Registrar acceso al panel de administración
    registrar_accion(request, "Accedió al panel de administración", modelo_afectado="Dashboard")

    context = {
        'total_usuarios': total_usuarios,
        'total_productos': total_productos,
        'total_categorias': total_categorias,
        'valor_total_inventario': valor_total_inventario,
        'ultimos_usuarios': ultimos_usuarios,
        'ultimos_productos': ultimos_productos,
    }
    return render(request, 'core/admin_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_usuarios(request):
    usuarios = User.objects.all()

    # 🔍 Registrar visualización de usuarios
    registrar_accion(request, "Consultó la lista de usuarios", modelo_afectado="User")

    return render(request, 'core/admin_usuarios.html', {'usuarios': usuarios})


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_productos(request):
    if request.method == 'POST':

        # ==========================================================
        # ============== ACTUALIZAR PRODUCTO ========================
        # ==========================================================

        if 'guardar' in request.POST:
            producto_id = request.POST['guardar']
            producto = get_object_or_404(Producto, id=producto_id)

            # Guardar valores anteriores para detectar cambios
            old_nombre = producto.nombre
            old_codigo = producto.codigo
            old_descripcion = producto.descripcion
            old_precio = producto.precio
            old_categoria = producto.categoria.nombre if producto.categoria else None
            old_cantidad = producto.cantidad
            old_disponible = producto.disponible
            old_imagen = producto.imagen.name if producto.imagen else None

            # === Actualizar campos ===
            producto.nombre = request.POST.get(f'nombre_{producto_id}')
            producto.codigo = request.POST.get(f'codigo_{producto_id}')
            producto.descripcion = request.POST.get(f'descripcion_{producto_id}')
            precio_raw = request.POST.get(f'precio_{producto_id}', '').strip()
            producto.precio = float(precio_raw) if precio_raw else None

            producto.categoria_id = request.POST.get(f'categoria_{producto_id}')
            producto.cantidad = request.POST.get(f'cantidad_{producto_id}')
            producto.disponible = f'disponible_{producto_id}' in request.POST

            if request.FILES.get(f'imagen_{producto_id}'):
                producto.imagen = request.FILES[f'imagen_{producto_id}']

            producto.save()

            # ==========================================================
            # ============ REGISTRO DE AUDITORÍA (UPDATE) ==============
            # ==========================================================

            # Nombre usuario
            nombre_usuario = (
                f"{request.user.first_name} {request.user.last_name}".strip()
                or request.user.username
            )

            fecha_actual = timezone.localtime(timezone.now()).strftime("%Y-%m-%d")
            hora_actual = timezone.localtime(timezone.now()).strftime("%H:%M:%S")

            # Detectar cambios con valores exactos
            cambios = []

            if old_nombre != producto.nombre:
                cambios.append(f"nombre: '{old_nombre}' → '{producto.nombre}'")

            if old_codigo != producto.codigo:
                cambios.append(f"código: '{old_codigo}' → '{producto.codigo}'")

            if old_descripcion != producto.descripcion:
                cambios.append(f"descripción: '{old_descripcion}' → '{producto.descripcion}'")

            if old_precio != producto.precio:
                cambios.append(f"precio: {old_precio} → {producto.precio}")

            new_categoria = producto.categoria.nombre if producto.categoria else None
            if old_categoria != new_categoria:
                cambios.append(f"categoría: '{old_categoria}' → '{new_categoria}'")

            if old_cantidad != producto.cantidad:
                cambios.append(f"cantidad: {old_cantidad} → {producto.cantidad}")

            if old_disponible != producto.disponible:
                cambios.append(f"disponible: {old_disponible} → {producto.disponible}")

            new_imagen = producto.imagen.name if producto.imagen else None
            if old_imagen != new_imagen:
                cambios.append(f"imagen: '{old_imagen}' → '{new_imagen}'")

            cambios_texto = ", ".join(cambios) if cambios else "sin cambios"

            detalle = (
                f"El {fecha_actual} a las {hora_actual}, {nombre_usuario} actualizó el producto "
                f"'{producto.nombre}' (ID: {producto.id}). Cambios realizados: {cambios_texto}."
            )

            registrar_accion(
                request,
                accion="Actualizó un producto",
                modelo_afectado="Producto",
                objeto_id=producto.id,
                detalle=detalle
            )

            messages.success(request, f"Producto '{producto.nombre}' actualizado correctamente.")


        # ==========================================================
        # ============== ELIMINAR PRODUCTO ==========================
        # ==========================================================

        elif 'eliminar' in request.POST:
            producto_id = request.POST['eliminar']
            producto = get_object_or_404(Producto, id=producto_id)
            nombre_producto = producto.nombre
            producto.delete()

            # === Auditoría de eliminación ===
            nombre_usuario = (
                f"{request.user.first_name} {request.user.last_name}".strip()
                or request.user.username
            )

            fecha_actual = timezone.localtime(timezone.now()).strftime("%Y-%m-%d")
            hora_actual = timezone.localtime(timezone.now()).strftime("%H:%M:%S")

            detalle = (
                f"El {fecha_actual} a las {hora_actual}, {nombre_usuario} eliminó el producto "
                f"'{nombre_producto}' (ID: {producto_id})."
            )

            registrar_accion(
                request,
                accion="Eliminó un producto",
                modelo_afectado="Producto",
                objeto_id=producto_id,
                detalle=detalle
            )

            messages.success(request, f"Producto '{nombre_producto}' eliminado.")

        return redirect('admin_productos')

    # ==========================================================
    # ============== CONSULTA DE LISTA DE PRODUCTOS ============
    # ==========================================================

    productos = Producto.objects.all()
    categorias = Categoria.objects.all()

    # Auditoría (solo vista)
    nombre_usuario = (
        f"{request.user.first_name} {request.user.last_name}".strip()
        or request.user.username
    )
    fecha_actual = timezone.localtime(timezone.now()).strftime("%Y-%m-%d")
    hora_actual = timezone.localtime(timezone.now()).strftime("%H:%M:%S")

    detalle = (
        f"El {fecha_actual} a las {hora_actual}, {nombre_usuario} consultó la lista completa "
        f"de productos. Total mostrados: {productos.count()}."
    )

    registrar_accion(
        request,
        accion="Consultó productos",
        modelo_afectado="Producto",
        objeto_id=None,
        detalle=detalle
    )

    return render(request, 'core/admin_productos.html', {
        'productos': productos,
        'categorias': categorias,
    })

# -------------------- Gestión de usuarios --------------------

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .utils import registrar_accion  # 👈 Importa la función

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def agregar_usuario(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')

        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(username=username)
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.set_password('usuario123')
            user.save()

            # =============================
            # 🔍 AUDITORÍA DETALLADA
            # =============================
            nombre_usuario = (
                f"{request.user.first_name} {request.user.last_name}".strip()
                or request.user.username
            )
            fecha = timezone.localtime(timezone.now()).strftime("%Y-%m-%d")
            hora = timezone.localtime(timezone.now()).strftime("%H:%M:%S")

            detalle = (
                f"El {fecha} a las {hora}, {nombre_usuario} creó un nuevo usuario.\n"
                f"Valores ingresados:\n"
                f"- Username: {username}\n"
                f"- Nombre: {first_name}\n"
                f"- Apellido: {last_name}\n"
                f"- Email: {email}\n"
                f"- Contraseña establecida por defecto: usuario123"
            )

            registrar_accion(
                request,
                accion="Creó un nuevo usuario",
                modelo_afectado="User",
                objeto_id=user.id,
                detalle=detalle
            )

            messages.success(request, f"Usuario {username} agregado correctamente.")
        else:
            messages.warning(request, f"El nombre de usuario '{username}' ya existe.")

    return redirect('admin_usuarios')

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def actualizar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)

    if request.method == 'POST':

        # =============================
        # 🔍 Guardar valores antiguos
        # =============================
        old_first_name = usuario.first_name
        old_last_name = usuario.last_name
        old_email = usuario.email

        # =============================
        # 🔄 Actualizar datos
        # =============================
        usuario.first_name = request.POST.get('first_name')
        usuario.last_name = request.POST.get('last_name')
        usuario.email = request.POST.get('email')
        usuario.save()

        # =============================
        # 📌 Detectar cambios
        # =============================
        cambios = []

        if old_first_name != usuario.first_name:
            cambios.append(f"Nombre: '{old_first_name}' → '{usuario.first_name}'")

        if old_last_name != usuario.last_name:
            cambios.append(f"Apellido: '{old_last_name}' → '{usuario.last_name}'")

        if old_email != usuario.email:
            cambios.append(f"Email: '{old_email}' → '{usuario.email}'")

        cambios_texto = "\n".join(f"- {c}" for c in cambios) if cambios else "Sin cambios."

        # =============================
        # 🕒 Fecha, hora y usuario
        # =============================
        nombre_admin = (
            f"{request.user.first_name} {request.user.last_name}".strip()
            or request.user.username
        )
        fecha = timezone.localtime(timezone.now()).strftime("%Y-%m-%d")
        hora = timezone.localtime(timezone.now()).strftime("%H:%M:%S")

        # =============================
        # 📝 Detalle completo auditoría
        # =============================
        detalle = (
            f"El {fecha} a las {hora}, {nombre_admin} actualizó el usuario "
            f"'{usuario.username}' (ID: {usuario.id}).\n\n"
            f"Cambios realizados:\n"
            f"{cambios_texto}"
        )

        # =============================
        # 🧾 Registrar acción
        # =============================
        registrar_accion(
            request,
            accion="Actualizó un usuario",
            modelo_afectado="User",
            objeto_id=usuario.id,
            detalle=detalle
        )

        messages.success(request, f"Usuario {usuario.username} actualizado correctamente.")

    return redirect('admin_usuarios')


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def eliminar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)

    # Evitar que alguien elimine su propia cuenta o un superusuario
    if usuario != request.user and not usuario.is_superuser:

        # ============================
        # 🔍 Guardar datos antes de borrar
        # ============================
        datos_usuario = {
            "username": usuario.username,
            "first_name": usuario.first_name,
            "last_name": usuario.last_name,
            "email": usuario.email,
        }

        nombre = usuario.username
        usuario.delete()

        # ============================
        # 🕒 Datos del administrador
        # ============================
        admin_nombre = (
            f"{request.user.first_name} {request.user.last_name}".strip()
            or request.user.username
        )
        fecha = timezone.localtime(timezone.now()).strftime("%Y-%m-%d")
        hora = timezone.localtime(timezone.now()).strftime("%H:%M:%S")

        # ============================
        # 📝 Detalle completo auditoría
        # ============================
        detalle = (
            f"El {fecha} a las {hora}, {admin_nombre} eliminó el usuario "
            f"'{datos_usuario['username']}' (ID: {usuario_id}).\n\n"
            f"Datos del usuario eliminado:\n"
            f"- Nombre: {datos_usuario['first_name']}\n"
            f"- Apellido: {datos_usuario['last_name']}\n"
            f"- Email: {datos_usuario['email']}\n"
        )

        # ============================
        # 🧾 Registrar acción
        # ============================
        registrar_accion(
            request,
            accion="Eliminó un usuario",
            modelo_afectado="User",
            objeto_id=usuario_id,
            detalle=detalle
        )

        messages.success(request, f"Usuario {nombre} eliminado correctamente.")

    else:
        messages.warning(request, "No puedes eliminar tu propia cuenta o la de un superusuario.")

    return redirect('admin_usuarios')



# -------------------- Gestión de productos --------------------

from .utils import registrar_accion  # ✅ importar la función

from django.utils import timezone

from django.utils import timezone

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def agregar_producto(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        precio = request.POST.get('precio', '0').strip()
        categoria_id = request.POST.get('categoria')
        codigo = request.POST.get('codigo', '').strip()
        cantidad = request.POST.get('cantidad', '0').strip()
        disponible = request.POST.get('disponible') == 'on'
        imagen = request.FILES.get('imagen')

        if Producto.objects.filter(codigo=codigo).exists():
            messages.error(request, 'El código del producto ya existe. Debe ser único.')
            return redirect('admin_productos')

        try:
            categoria = Categoria.objects.get(id=categoria_id)
        except Categoria.DoesNotExist:
            messages.error(request, 'Categoría no válida.')
            return redirect('admin_productos')

        try:
            precio = float(precio)
            cantidad = int(cantidad)
        except ValueError:
            messages.error(request, 'Precio o cantidad inválidos.')
            return redirect('admin_productos')

        producto = Producto.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            categoria=categoria,
            codigo=codigo,
            cantidad=cantidad,
            disponible=disponible,
            imagen=imagen,
        )

        # 🔹 Nombre del usuario
        if request.user and request.user.is_authenticated:
            nombre_usuario = f"{request.user.first_name} {request.user.last_name}".strip()
            if not nombre_usuario:
                nombre_usuario = request.user.username
        else:
            nombre_usuario = "Usuario anónimo"

        # 🔹 Fecha y hora actual en zona horaria configurada (America/Bogota)
        ahora = timezone.localtime()
        fecha_actual = ahora.strftime("%Y-%m-%d")
        hora_actual = ahora.strftime("%H:%M:%S")

        # 🔥 Auditoría detallada
        registrar_accion(
            request,
            accion="Creó un nuevo producto",
            modelo_afectado="Producto",
            objeto_id=producto.id,
            producto=producto.nombre,
            cantidad=producto.cantidad,
            detalle=(
                f"El {fecha_actual} a las {hora_actual}, "
                f"{nombre_usuario} creó un producto con código {producto.codigo}, "
                f"cantidad inicial {producto.cantidad} y precio {producto.precio:.2f}."
            )
        )

        messages.success(request, 'Producto agregado correctamente.')
        return redirect('admin_productos')

    return redirect('admin_productos')



from django.shortcuts import redirect, get_object_or_404
from core.models import Producto, Categoria
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.shortcuts import redirect, get_object_or_404
from .models import Producto, Categoria
from django.contrib.auth.decorators import login_required

from django.shortcuts import redirect, get_object_or_404
from core.models import Producto, Categoria
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.shortcuts import redirect, get_object_or_404
from .models import Producto, Categoria
from django.contrib.auth.decorators import login_required

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def actualizar_producto(request, producto_id):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)

        # Actualizar campos básicos
        producto.nombre = request.POST.get(f'nombre_{producto_id}')
        producto.codigo = request.POST.get(f'codigo_{producto_id}')
        producto.descripcion = request.POST.get(f'descripcion_{producto_id}')
        producto.precio = float(request.POST.get(f'precio_{producto_id}', producto.precio))
        producto.categoria_id = request.POST.get(f'categoria_{producto_id}')
        producto.cantidad = int(request.POST.get(f'cantidad_{producto_id}', producto.cantidad))
        producto.disponible = request.POST.get(f'disponible_{producto_id}') == 'on'

        # Actualizar imagen
        if request.FILES.get(f'imagen_{producto_id}'):
            producto.imagen = request.FILES[f'imagen_{producto_id}']

        producto.save()
        messages.success(request, f"Producto '{producto.nombre}' actualizado correctamente.")
    return redirect('admin_productos')

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    nombre = producto.nombre
    producto.delete()

    # 🔍 Registrar acción
    registrar_accion(
        request,
        f"Eliminó el producto: {nombre}",
        modelo_afectado="Producto",
        objeto_id=producto_id
    )

    messages.success(request, f"Producto '{nombre}' eliminado.")
    return redirect('admin_productos')


# -----------------------------
# CLIENTE - CARRITO
# -----------------------------

@login_required
def cart_detail(request):
    cart = Carrito(request)
    return render(request, "core/cart_detail.html", {
        "cart": cart,
        "total": cart.get_total()
    })


@login_required
def add_to_cart(request, producto_id):
    cart = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    cart.add(producto)

    # 🔹 Nombre del usuario
    if request.user and request.user.is_authenticated:
        nombre_usuario = f"{request.user.first_name} {request.user.last_name}".strip()
        if not nombre_usuario:
            nombre_usuario = request.user.username
    else:
        nombre_usuario = "Usuario anónimo"

    # 🔹 Fecha y hora actual en zona horaria configurada (America/Bogota)
    fecha_hora = timezone.localtime(timezone.now())
    fecha_actual = fecha_hora.strftime("%Y-%m-%d")
    hora_actual = fecha_hora.strftime("%H:%M:%S")

    # 🔥 Auditoría detallada
    registrar_accion(
        request,
        accion="Agregó producto al carrito",
        modelo_afectado="Producto",
        objeto_id=producto.id,
        producto=producto.nombre,
        cantidad=1,  # siempre agrega 1 al carrito
        detalle=(
            f"El usuario {nombre_usuario} agregó el producto '{producto.nombre}' "
            f"(ID {producto.id}) al carrito el día {fecha_actual} a las {hora_actual}."
        )
    )

    return redirect("cart_detail")




@login_required
def remove_from_cart(request, producto_id):
    cart = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    cart.remove(producto)

    # Nombre del usuario
    if request.user and request.user.is_authenticated:
        nombre_usuario = f"{request.user.first_name} {request.user.last_name}".strip()
        if not nombre_usuario:
            nombre_usuario = request.user.username
    else:
        nombre_usuario = "Usuario anónimo"

    # Fecha y hora Colombia
    fecha_hora = timezone.localtime(timezone.now())
    fecha_actual = fecha_hora.strftime("%Y-%m-%d")
    hora_actual = fecha_hora.strftime("%H:%M:%S")

    # Stock disponible
    stock_disponible = producto.cantidad

    # 🔥 Auditoría detallada (SIN parámetros no permitidos)
    detalle = (
        f"El {fecha_actual} a las {hora_actual}, {nombre_usuario} eliminó del carrito "
        f"el producto '{producto.nombre}' (ID {producto.id}), "
        f"precio: ${producto.precio}, stock disponible: {stock_disponible} unidades."
    )

    registrar_accion(
        request,
        accion="Eliminó producto del carrito",
        modelo_afectado="Producto",
        objeto_id=producto.id,
        detalle=detalle
    )

    return redirect("cart_detail")



@login_required
def decrease_from_cart(request, producto_id):
    cart = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    cart.decrease(producto)

    # 🔹 Nombre del usuario
    if request.user and request.user.is_authenticated:
        nombre_usuario = f"{request.user.first_name} {request.user.last_name}".strip()
        if not nombre_usuario:
            nombre_usuario = request.user.username
    else:
        nombre_usuario = "Usuario anónimo"

    # 🔹 Fecha y hora local (Colombia)
    fecha_actual = timezone.localtime(timezone.now()).strftime("%Y-%m-%d")
    hora_actual = timezone.localtime(timezone.now()).strftime("%H:%M:%S")

    # 🔥 Auditoría detallada
    registrar_accion(
        request,
        accion="Disminuyó cantidad del producto en carrito",
        modelo_afectado="Producto",
        objeto_id=producto.id,
        producto=producto.nombre,
        cantidad=1,
        detalle=(
            f"El {fecha_actual} a las {hora_actual}, "
            f"{nombre_usuario} disminuyó la cantidad del producto '{producto.nombre}' "
            f"(ID {producto.id}) en el carrito."
        )
    )

    return redirect("cart_detail")



@login_required
def clear_cart(request):
    cart = Carrito(request)
    cart.clear()

    # 🔹 Nombre del usuario
    if request.user and request.user.is_authenticated:
        nombre_usuario = f"{request.user.first_name} {request.user.last_name}".strip()
        if not nombre_usuario:
            nombre_usuario = request.user.username
    else:
        nombre_usuario = "Usuario anónimo"

    # 🔹 Fecha y hora local (Colombia)
    fecha_actual = timezone.localtime(timezone.now()).strftime("%Y-%m-%d")
    hora_actual = timezone.localtime(timezone.now()).strftime("%H:%M:%S")

    # 🔥 Auditoría detallada
    registrar_accion(
        request,
        accion="Vació su carrito",
        modelo_afectado="Carrito",
        objeto_id=None,
        producto=None,
        cantidad=None,
        detalle=(
            f"El {fecha_actual} a las {hora_actual}, "
            f"{nombre_usuario} vació completamente su carrito de compras."
        )
    )

    return redirect("cart_detail")


@login_required
def cart_total_api(request):
    cart = request.session.get('cart', {})
    total_items = sum(item.get('quantity', 0) for item in cart.values())
    return JsonResponse({'total_items': total_items})

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Producto

def product_detail(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    # Si es petición AJAX (fetch), devolvemos el fragmento
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, "core/product_detail_fragment.html", {"producto": producto})

    # Si es navegación normal, devolvemos la página completa
    return render(request, "core/product_detail.html", {"producto": producto})

from django.shortcuts import render, redirect
from django.contrib import messages
from .cart import Carrito

@login_required
def checkout(request):
    cart = Carrito(request)

    # 🔹 Nombre del usuario
    if request.user and request.user.is_authenticated:
        nombre_usuario = f"{request.user.first_name} {request.user.last_name}".strip()
        if not nombre_usuario:
            nombre_usuario = request.user.username
    else:
        nombre_usuario = "Usuario anónimo"

    # 🔹 Fecha y hora local (Colombia)
    fecha_actual = timezone.localtime(timezone.now()).strftime("%Y-%m-%d")
    hora_actual = timezone.localtime(timezone.now()).strftime("%H:%M:%S")

    # 🔥 Registrar acción detallada
    registrar_accion(
        request,
        accion="Ingresó al proceso de pago (checkout)",
        modelo_afectado="Carrito",
        objeto_id=None,
        producto=None,
        cantidad=None,
        detalle=(
            f"El {fecha_actual} a las {hora_actual}, "
            f"{nombre_usuario} ingresó al proceso de pago (checkout)."
        )
    )

    return render(request, "core/checkout.html", {
        "cart_items": cart,
        "total": cart.get_total()
    })


from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from .models import Pedido, PedidoItem
from .cart import Carrito  # asegúrate de importar bien



# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Pedido, PedidoItem, Producto
from .cart import Carrito



from .models import Pedido, PedidoItem, Factura, FacturaItem
from .cart import Carrito
from .utils import registrar_accion  # Asegúrate de tener esta función en utils.py


from .cart import Carrito  

# 🔹 importa tus modelos
from .models import Pedido, PedidoItem, Factura, FacturaItem
from .utils import registrar_accion  # si usas esta función

# === Vista para procesar pago ===
@login_required
@transaction.atomic
def procesar_pago(request):
    if request.method == "POST":
        try:
            metodo_pago = request.POST.get("metodo_pago")
            nombre = request.POST.get("nombre")
            email = request.POST.get("email")
            telefono = request.POST.get("telefono")
            direccion = request.POST.get("direccion")

            cart = Carrito(request)
            subtotal = cart.get_subtotal()
            iva = cart.get_iva()
            total = cart.get_total()

            # === Determinar estado según método de pago ===
            estado = "pendiente" if metodo_pago.lower() == "efectivo" else "pagado"

            # === Crear pedido ===
            pedido = Pedido.objects.create(
                usuario=request.user,
                nombre=nombre,
                email=email,
                telefono=telefono,
                direccion=direccion,
                metodo_pago=metodo_pago,
                total=total,
                estado=estado,
            )

            # === Crear items del pedido ===
            for item in cart:
                PedidoItem.objects.create(
                    pedido=pedido,
                    producto=item["producto"],
                    cantidad=item["cantidad"],
                    precio=item["producto"].precio
                )

            # === Crear factura ===
            cufe = str(uuid.uuid4())
            timezone_co = pytz.timezone("America/Bogota")
            fecha_local = datetime.now(timezone_co)

            factura = Factura.objects.create(
                pedido=pedido,
                cliente=request.user,
                direccion=direccion,
                subtotal=subtotal,
                iva=iva,
                total=total,
                fecha=fecha_local,
                cufe=cufe,
                forma_pago="Contado",
                medio_pago=metodo_pago,
            )

            # === Crear items de factura ===
            for item in pedido.items.all():
                FacturaItem.objects.create(
                    factura=factura,
                    producto=item.producto.nombre,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio,
                    subtotal=item.subtotal()
                )

            # === Actualizar inventario ===
            for item in pedido.items.all():
                producto = item.producto
                if producto.cantidad >= item.cantidad:
                    producto.cantidad -= item.cantidad
                    producto.save()
                else:
                    messages.error(
                        request,
                        f"No hay suficiente stock de {producto.nombre}. Disponible: {producto.cantidad}"
                    )
                    raise ValueError("Stock insuficiente")

            # === Generar código QR ===
            qr_data = f"""
DIAN - Factura Electrónica de Venta
Empresa: {factura.nombre_empresa}
NIT: {factura.nit_empresa}
Cliente: {nombre}
Factura No: {factura.numero_factura}
CUFE: {cufe}
Fecha emisión: {fecha_local.strftime("%d/%m/%Y %H:%M:%S")}
Total: ${total}
Medio de pago: {metodo_pago}
"""
            qr = qrcode.make(qr_data)
            buffer = io.BytesIO()
            qr.save(buffer, format="PNG")
            factura.qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            factura.save()

            # === Limpiar carrito ===
            cart.clear()

            # === Registro en auditoría ===

            # Nombre del usuario
            if request.user and request.user.is_authenticated:
                nombre_usuario = f"{request.user.first_name} {request.user.last_name}".strip()
                if not nombre_usuario:
                    nombre_usuario = request.user.username
            else:
                nombre_usuario = "Usuario anónimo"

            # Fecha y hora local (Colombia)
            fecha_actual = timezone.localtime(timezone.now()).strftime("%Y-%m-%d")
            hora_actual = timezone.localtime(timezone.now()).strftime("%H:%M:%S")

            # 🔥 Construir detalle de productos
            productos_detalle = []
            for item in pedido.items.all():
                productos_detalle.append(
                    f"{item.producto.nombre} x{item.cantidad} (${item.precio})"
                )

            productos_texto = ", ".join(productos_detalle)

            # === 🔥 AGREGAR TIPO DE PAGO AL DETALLE ===
            detalle = (
                f"El {fecha_actual} a las {hora_actual}, {nombre_usuario} realizó un pedido "
                f"(ID: {pedido.id}) por un total de ${total}. "
                f"Tipo de pago: {pedido.metodo_pago}. "
                f"Productos comprados: {productos_texto}. "
                f"Se generó la factura No. {factura.numero_factura}."
            )

            registrar_accion(
                request,
                accion="Generó pedido y factura",
                modelo_afectado="Factura",
                objeto_id=factura.id,
                detalle=detalle
            )

            messages.success(request, f"¡Gracias {nombre}! Tu pedido y factura fueron generados correctamente.")
            return redirect("factura", pedido_id=pedido.id)

        except Exception as e:
            messages.error(request, f"Ocurrió un error al procesar el pago: {str(e)}")
            return redirect("checkout")

    return redirect("checkout")


@login_required
def factura(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    factura = get_object_or_404(Factura, pedido=pedido)
    items = factura.items.all()

    # === Generar QR ===
    qr_data = f"""
DIAN - Factura Electrónica de Venta
Empresa: {factura.nombre_empresa}
NIT: {factura.nit_empresa}
Cliente: {factura.cliente.username}
Factura No: {factura.numero_factura}
CUFE: {factura.cufe}
Fecha emisión: {factura.fecha.strftime("%d/%m/%Y %H:%M:%S")}
Total: ${factura.total}
Medio de pago: {factura.medio_pago}
"""
    qr = qrcode.make(qr_data)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    # === Registrar acción ===
    registrar_accion(
        request,
        f"Consultó la factura {factura.numero_factura}",
        modelo_afectado="Factura",
        objeto_id=factura.id
    )

    return render(request, "core/factura.html", {
        "pedido": pedido,
        "factura": factura,
        "items": items,
        "qr_base64": qr_base64,
    })



from django.shortcuts import render, get_object_or_404
from .models import Pedido

from decimal import Decimal

@login_required
def factura(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    factura = get_object_or_404(Factura, pedido=pedido)
    items = factura.items.all()

    # === Generar nuevamente el código QR ===
    qr_data = f"""
DIAN - Factura Electrónica de Venta
Empresa: {factura.nombre_empresa}
NIT: {factura.nit_empresa}
Cliente: {factura.cliente.username}
Factura No: {factura.numero_factura}
CUFE: {factura.cufe}
Fecha emisión: {factura.fecha.strftime("%d/%m/%Y %H:%M:%S")}
Total: ${factura.total}
Medio de pago: {factura.medio_pago}
"""
    qr = qrcode.make(qr_data)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    # ===========================
    # 📝 AUDITORÍA DETALLADA
    # ===========================
    usuario_nombre = (
        f"{request.user.first_name} {request.user.last_name}".strip()
        or request.user.username
    )

    fecha_actual = timezone.localtime(timezone.now()).strftime("%Y-%m-%d")
    hora_actual = timezone.localtime(timezone.now()).strftime("%H:%M:%S")

    detalle = (
        f"El {fecha_actual} a las {hora_actual}, el usuario {usuario_nombre} consultó "
        f"la factura No. {factura.numero_factura} (ID: {factura.id}).\n\n"
        f"Detalles de la factura:\n"
        f"- Cliente: {factura.cliente.username}\n"
        f"- Total: ${factura.total}\n"
        f"- Medio de pago: {factura.medio_pago}\n"
        f"- Ítems: {items.count()}\n"
        f"- CUFE: {factura.cufe}\n"
    )

    registrar_accion(
        request,
        accion="Consultó una factura",
        modelo_afectado="Factura",
        objeto_id=factura.id,
        detalle=detalle
    )

    return render(request, "core/factura.html", {
        "pedido": pedido,
        "factura": factura,
        "items": items,
        "qr_base64": qr_base64,
    })

# -------------------- Reporte diario / Informe de operación --------------------
from django.shortcuts import render
from django.utils import timezone
from datetime import datetime
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.http import HttpResponse
from io import BytesIO

from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .models import Pedido


from django.db.models import Sum, Count
from django.db.models.functions import TruncDate

@staff_member_required
def reporte_diario(request):
    fecha_inicio = request.GET.get('inicio')
    fecha_fin = request.GET.get('fin')

    if fecha_inicio and fecha_fin:
        try:
            inicio = timezone.make_aware(datetime.strptime(fecha_inicio, '%Y-%m-%d'))
            fin = timezone.make_aware(datetime.strptime(fecha_fin, '%Y-%m-%d'))
            ventas = Pedido.objects.filter(fecha__date__range=[inicio.date(), fin.date()])
        except Exception:
            ventas = Pedido.objects.none()
    else:
        hoy = timezone.now().date()
        inicio_dia = timezone.make_aware(datetime.combine(hoy, datetime.min.time()))
        fin_dia = timezone.make_aware(datetime.combine(hoy, datetime.max.time()))
        ventas = Pedido.objects.filter(fecha__range=(inicio_dia, fin_dia))

    total_pedidos = ventas.count()
    total_vendido = ventas.aggregate(total=Sum('total'))['total'] or 0

    metodos_pago = list(ventas.values('metodo_pago').annotate(total=Sum('total')).order_by())
    estados = list(ventas.values('estado').annotate(total=Count('id')).order_by())
    ventas_por_dia = list(
        ventas.annotate(fecha_simple=TruncDate('fecha'))
        .values('fecha_simple')
        .annotate(total=Sum('total'))
        .order_by('fecha_simple')
    )

    # ============================
    # 🔍 REGISTRO EN AUDITORÍA — SIMPLE
    # ============================

    # Usuario
    if request.user and request.user.is_authenticated:
        nombre_usuario = f"{request.user.first_name} {request.user.last_name}".strip()
        if not nombre_usuario:
            nombre_usuario = request.user.username
    else:
        nombre_usuario = "Usuario anónimo"

    # Fecha y hora
    fecha_actual = timezone.localtime(timezone.now()).strftime("%Y-%m-%d")
    hora_actual = timezone.localtime(timezone.now()).strftime("%H:%M:%S")

    # Rango consultado
    if fecha_inicio and fecha_fin:
        rango_texto = f"del {fecha_inicio} al {fecha_fin}"
    else:
        rango_texto = "del día actual"

    detalle = (
        f"El {fecha_actual} a las {hora_actual}, {nombre_usuario} consultó el reporte diario "
        f"{rango_texto}."
    )

    registrar_accion(
        request,
        accion="Consultó reporte diario",
        modelo_afectado="Reporte",
        objeto_id=0,
        detalle=detalle
    )

    # ============================

    context = {
        'ventas': ventas,
        'total_pedidos': total_pedidos,
        'total_vendido': total_vendido,
        'metodos_pago': metodos_pago,
        'estados': estados,
        'ventas_por_dia': ventas_por_dia,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }

    return render(request, 'core/reporte_diario.html', context)

#  === EXPORTAR A PDF ===
from django.utils import timezone
from datetime import datetime, timezone as dt_timezone
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import Pedido


def reporte_diario_pdf(request):
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    # Crear la respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_diario.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    p.setTitle("Reporte de Ventas")

    # Cabecera
    p.setFont("Helvetica-Bold", 14)
    p.drawString(200, 750, "Reporte de ventas")
    p.setFont("Helvetica", 10)

    if fecha_inicio and fecha_fin:
        try:
            inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            fin = datetime.strptime(fecha_fin, "%Y-%m-%d")

            # ✅ Usamos datetime.timezone.utc (no django.utils.timezone.utc)
            inicio_utc = datetime.combine(inicio, datetime.min.time(), tzinfo=dt_timezone.utc)
            fin_utc = datetime.combine(fin, datetime.max.time(), tzinfo=dt_timezone.utc)

            ventas = Pedido.objects.filter(fecha__range=(inicio_utc, fin_utc))
            titulo = f"Reporte de ventas del {fecha_inicio} al {fecha_fin} (UTC)"
        except ValueError:
            ventas = []
            titulo = "Reporte de ventas (rango inválido)"
    else:
        # ✅ Reporte automático del día actual en UTC
        hoy_utc = timezone.now().astimezone(dt_timezone.utc).date()
        inicio_dia_utc = datetime.combine(hoy_utc, datetime.min.time(), tzinfo=dt_timezone.utc)
        fin_dia_utc = datetime.combine(hoy_utc, datetime.max.time(), tzinfo=dt_timezone.utc)

        ventas = Pedido.objects.filter(fecha__range=(inicio_dia_utc, fin_dia_utc))
        titulo = f"Reporte diario de ventas (UTC {hoy_utc.strftime('%d/%m/%Y')})"

    # Escribir encabezado
    p.drawString(50, 730, titulo)

    # Info del sistema
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(50, 715, "Zona horaria: UTC")
    p.drawString(50, 705, f"Fecha del sistema: {datetime.now(dt_timezone.utc).strftime('%d/%m/%Y %H:%M:%S')}")

    # Cabecera de tabla
    y = 680
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "ID")
    p.drawString(100, y, "Cliente")
    p.drawString(200, y, "Método")
    p.drawString(300, y, "Estado")
    p.drawString(400, y, "Fecha")
    p.drawString(480, y, "Total")
    p.line(45, y - 5, 550, y - 5)
    y -= 20

    # Datos
    total_vendido = 0
    total_pedidos = ventas.count()

    p.setFont("Helvetica", 10)
    for pedido in ventas:
        p.drawString(50, y, str(pedido.id))
        p.drawString(100, y, str(pedido.usuario.username if pedido.usuario else "N/A"))
        p.drawString(200, y, str(pedido.metodo_pago))
        p.drawString(300, y, str(pedido.estado))
        p.drawString(400, y, pedido.fecha.strftime("%Y-%m-%d %H:%M"))
        p.drawString(480, y, f"${pedido.total:.2f}")
        total_vendido += pedido.total
        y -= 20
        if y < 50:
            p.showPage()
            y = 750

    # Totales
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y - 20, f"Total de pedidos: {total_pedidos}")
    p.drawString(300, y - 20, f"Total vendido: ${total_vendido:.2f}")

    p.showPage()
    p.save()
    return response



#from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.http import HttpResponse
from django.db import transaction

from openpyxl import Workbook
from datetime import datetime
from django.db.models import Sum
from .models import Producto, Pedido, PedidoItem, Factura, FacturaItem

from datetime import timezone as dt_timezone
from django.db import transaction

@staff_member_required
def reporte_diario_excel(request):
    """Genera un archivo Excel con el informe diario o rango filtrado (en UTC)."""
    
    fecha_inicio = request.GET.get('inicio')
    fecha_fin = request.GET.get('fin')

    ventas = Pedido.objects.none()  # valor por defecto

    # ✅ Validar que existan y no sean 'None'
    if fecha_inicio and fecha_fin and fecha_inicio.lower() != "none" and fecha_fin.lower() != "none":
        try:
            # Convertir a fechas UTC
            inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fin = datetime.strptime(fecha_fin, '%Y-%m-%d')

            inicio_utc = datetime.combine(inicio, datetime.min.time(), tzinfo=dt_timezone.utc)
            fin_utc = datetime.combine(fin, datetime.max.time(), tzinfo=dt_timezone.utc)

            ventas = Pedido.objects.filter(fecha__range=(inicio_utc, fin_utc))
        except Exception:
            ventas = Pedido.objects.none()
    else:
        # 🕒 Reporte diario UTC (día actual)
        hoy_utc = timezone.now().astimezone(dt_timezone.utc).date()
        inicio_dia_utc = datetime.combine(hoy_utc, datetime.min.time(), tzinfo=dt_timezone.utc)
        fin_dia_utc = datetime.combine(hoy_utc, datetime.max.time(), tzinfo=dt_timezone.utc)
        ventas = Pedido.objects.filter(fecha__range=(inicio_dia_utc, fin_dia_utc))

    # === Crear el archivo Excel ===
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte de Ventas"

    # === Cabecera ===
    ws.append(["ID", "Cliente", "Método de Pago", "Estado", "Fecha", "Total"])

    total_vendido = 0
    for pedido in ventas:
        ws.append([
            pedido.id,
            pedido.usuario.username if pedido.usuario else "N/A",
            pedido.metodo_pago,
            pedido.estado,
            pedido.fecha.strftime("%Y-%m-%d %H:%M"),
            float(pedido.total),
        ])
        total_vendido += float(pedido.total or 0)

    # === Totales ===
    ws.append([])
    ws.append(["", "", "", "TOTAL PEDIDOS", ventas.count()])
    ws.append(["", "", "", "TOTAL VENDIDO", float(total_vendido)])

    # === Respuesta HTTP ===
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="reporte_diario.xlsx"'
    wb.save(response)
    return response


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def log_auditoria(request):
    """Muestra los registros de auditoría con filtro por fechas."""
    fecha_inicio = request.GET.get('inicio')
    fecha_fin = request.GET.get('fin')
    logs = Auditoria.objects.all().order_by('-fecha')

    if fecha_inicio and fecha_fin:
        logs = logs.filter(fecha__date__range=[fecha_inicio, fecha_fin])

    context = {
        'logs': logs,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    }
    return render(request, 'core/log_auditoria.html', context)

@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def exportar_log_excel(request):
    """Exporta los registros de auditoría filtrados a un archivo Excel."""
    
    fecha_inicio = request.GET.get('inicio')
    fecha_fin = request.GET.get('fin')

    logs = Auditoria.objects.all().order_by('-fecha')

    # Validar rango de fechas
    if fecha_inicio and fecha_fin and fecha_inicio.lower() != "none" and fecha_fin.lower() != "none":
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            logs = logs.filter(fecha__date__range=[fecha_inicio_dt, fecha_fin_dt])
        except ValueError:
            pass  # Si no son válidas no se filtra nada

    # Crear archivo Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Auditoría"

    # Encabezados completos
    ws.append([
        "Fecha",
        "Usuario",
        "Tipo Usuario",
        "Acción",
        "Modelo Afectado",
        "ID Objeto",
        "Producto",
        "Cantidad",
        "Detalle"
    ])

    # Inserción de datos
    for log in logs:
        ws.append([
            log.fecha.strftime("%Y-%m-%d %H:%M:%S"),
            log.usuario.username if log.usuario else "Anónimo",
            log.tipo_usuario or "",
            log.accion or "",
            log.modelo_afectado or "",
            log.objeto_id or "",
            str(log.producto) if log.producto else "",
            log.cantidad if log.cantidad else "",
            log.detalle if log.detalle else "",
        ])

    # Respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="log_auditoria.xlsx"'

    wb.save(response)
    return response


# ======================================================================
# FUNCIÓN registrar_accion — FINAL Y COMPLETA
# ======================================================================
def registrar_accion(
    request,
    accion,
    modelo_afectado=None,
    objeto_id=None,
    producto=None,
    cantidad=None,
    detalle=None
):
    usuario = request.user if request.user.is_authenticated else None

    tipo = None
    if usuario:
        tipo = "Admin" if usuario.is_staff else "Cliente"

    Auditoria.objects.create(
        usuario=usuario,
        tipo_usuario=tipo,
        accion=accion,
        modelo_afectado=modelo_afectado,
        objeto_id=objeto_id,
        producto=producto,
        cantidad=cantidad,
        detalle=detalle
    )