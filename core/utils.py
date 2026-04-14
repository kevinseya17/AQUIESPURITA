from .models import Auditoria

def registrar_accion(request, accion, modelo_afectado=None, objeto_id=None):
    usuario = request.user if request.user.is_authenticated else None

    # ✅ Detectar el tipo de usuario
    if usuario:
        if usuario.is_superuser or usuario.is_staff:
            tipo = "Administrador"
        else:
            tipo = "Cliente"
    else:
        tipo = "Anónimo"

    # ✅ Registrar en base de datos
    Auditoria.objects.create(
        usuario=usuario,
        tipo_usuario=tipo,
        accion=accion,
        modelo_afectado=modelo_afectado,
        objeto_id=objeto_id
    )
