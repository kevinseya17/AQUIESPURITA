# -*- coding: utf-8 -*-
"""
Reconstruye el Word insertando:
  - 9.1.1  Pruebas de Aislamiento (sub-seccion de 9.1 Autenticacion)
  - 9.8    Pipeline CI/CD con GitHub Actions
  - 9.9    Importancia del Pipeline
en los lugares correctos del documento original.
"""
from docx import Document
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from lxml import etree
import copy, os

# ── Archivo fuente ────────────────────────────────────────────────────────────
SRC = 'EJEMPLO/Informe_Lacteos_Purita (2).docx'
DST = 'EJEMPLO/Informe_Lacteos_Purita_FINAL.docx'

doc = Document(SRC)

# ── Mapa de estilos por style_id (evita duplicados de nombre) ────────────────
_sid = {}
for s in doc.styles:
    if s.style_id not in _sid:
        _sid[s.style_id] = s

# ── Helper: crear parrafo con estilo dado por style_id ───────────────────────
def new_para(doc, style_id='Normal'):
    p = OxmlElement('w:p')
    pPr = OxmlElement('w:pPr')
    pStyle = OxmlElement('w:pStyle')
    pStyle.set(qn('w:val'), style_id)
    pPr.append(pStyle)
    p.append(pPr)
    return p

def make_run(text, bold=False):
    r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    if bold:
        b = OxmlElement('w:b')
        rPr.append(b)
    r.append(rPr)
    t = OxmlElement('w:t')
    t.set(qn('xml:space'), 'preserve')
    t.text = text
    r.append(t)
    return r

def build_para(style_id, segments):
    """
    segments: lista de (texto, bold)
    """
    p = new_para(doc, style_id)
    for text, bold in segments:
        p.append(make_run(text, bold))
    return p

# ════════════════════════════════════════════════════════════════════════════
# BLOQUE 9.1.1 – Pruebas de Aislamiento (va despues del ultimo bullet de 9.1)
# ════════════════════════════════════════════════════════════════════════════
def bloque_911():
    paras = []
    paras.append(build_para('Heading3', [('9.1.1 Pruebas de Aislamiento del Microservicio', False)]))
    paras.append(build_para('Normal', [(
        'Como parte del rigor tecnico aplicado, se disenaron procesos especificos para evaluar '
        'el desacoplamiento real entre las capas del sistema y el comportamiento del microservicio '
        'de autenticacion de forma completamente independiente al framework Django:', False)]))

    bullets_911 = [
        ('Aislamiento Funcional (test_run.py): ',
         'Para validar que la Capa de Dominio no esta acoplada al framework web ni a un motor de '
         'base de datos especifico, se construyo el script test_run.py. Este simula exactamente '
         'lo que haria un API Gateway real: construye un evento JSON (username + password) y lo '
         'lanza directamente contra lambda_handler() del microservicio. Se ejecutan dos escenarios: '
         'credenciales correctas (HTTP 200 OK) y contrasena incorrecta (HTTP 401 Unauthorized), '
         'verificando la logica de negocio sin levantar Django ni conectar ninguna base de datos.'),
        ('Repositorio en Memoria Volatil (in_memory_repository.py): ',
         'Durante las pruebas, el sistema es alimentado por InMemoryUserRepository, un adaptador '
         'simulado en memoria RAM. Carga usuarios de prueba en un diccionario Python, reemplazando '
         'al adaptador real sin cambiar una sola linea del nucleo de negocio. Esto cumple la '
         'promesa de la Arquitectura Hexagonal: el dominio es completamente agnostico a la '
         'infraestructura de persistencia.'),
        ('Gestion Multi-Entorno Segura (os.environ): ',
         'Se diseno una configuracion dinamica mediante variables de entorno '
         '(os.environ["AUTH_MICROSERVICE_URL"]) que indica si operar hacia localhost:8001 '
         'en desarrollo o hacia el proveedor PaaS en produccion, evitando que algun desarrollador '
         'conecte codigo local a la base de datos real por error.'),
    ]
    for bold_txt, normal_txt in bullets_911:
        p = new_para(doc, 'ListParagraph')
        p.append(make_run(bold_txt, bold=True))
        p.append(make_run(normal_txt, bold=False))
        paras.append(p)
    return paras

# ════════════════════════════════════════════════════════════════════════════
# BLOQUE 9.8 – Pipeline CI/CD
# ════════════════════════════════════════════════════════════════════════════
def bloque_98():
    paras = []
    paras.append(build_para('Heading2', [('9.8 Pipeline CI/CD Automatizado con GitHub Actions', False)]))
    paras.append(build_para('Normal', [(
        'Ningun cambio es promovido a la plataforma principal de manera manual ni arbitraria. '
        'El entorno automatizado, orquestado en .github/workflows/pipeline-ci-cd.yml bajo el '
        'nombre "Pipeline E-Commerce Purita", actua como filtro estricto de calidad. '
        'Se compone de 5 fases tecnicas secuenciales que se disparan automaticamente con cada '
        'evento push en la rama main de GitHub:', False)]))

    steps = [
        ('Paso 1 - Descargar y Aislar (Checkout): ',
         'Se instancia una maquina virtual ubuntu-latest en la infraestructura de GitHub. '
         'A traves de actions/checkout@v3 se efectua una clonacion limpia del repositorio, '
         'garantizando que el runner trabaje con el codigo mas reciente sin archivos residuales '
         'de ejecuciones anteriores.'),
        ('Paso 2 - Compilar Entorno (Instalar Python y Dependencias): ',
         'Mediante actions/setup-python@v4 se instala Python 3.11. Luego pip instala de forma '
         'determinista todas las librerias del requirements.txt: Django 5.1.7, Pillow, '
         'psycopg2-binary, ReportLab, openpyxl, cloudinary, whitenoise y qrcode, asegurando '
         'un entorno de pruebas identico al de produccion.'),
        ('Paso 3 - Pruebas e Integridad del Sistema (Django Checks): ',
         'Es el paso mas critico. GitHub Actions ejecuta "python manage.py check" para analizar '
         'modelos ORM y relaciones entre tablas, y "python manage.py makemigrations --dry-run" '
         'para detectar modelos sin migracion generada. Si cualquier comando falla, el pipeline '
         'se detiene y el despliegue es abortado, protegiendo la base de datos PostgreSQL.'),
        ('Paso 4 - Generar Version de Produccion (Collectstatic): ',
         '"python manage.py collectstatic --noinput" recolecta y centraliza todos los archivos '
         'estaticos (CSS, JavaScript, imagenes) en staticfiles/. Permite que WhiteNoise los '
         'sirva de forma ultrarapida sin servidor web adicional como Nginx.'),
        ('Paso 5 - Despliegue Multi-Cloud Zero-Downtime (Publish): ',
         'Solo si los cuatro pasos anteriores tienen exito al 100%, el codigo pasa a la nube. '
         'Configuracion dual: render.yaml define el servicio en Render.com (dependencias, '
         'collectstatic, migrate, gunicorn), mientras vercel.json ofrece la alternativa '
         'serverless. Esta arquitectura garantiza Zero-Downtime: los usuarios que esten '
         'comprando no experimentan ninguna interrupcion durante el despliegue.'),
    ]
    for bold_txt, normal_txt in steps:
        p = new_para(doc, 'ListParagraph')
        p.append(make_run(bold_txt, bold=True))
        p.append(make_run(normal_txt, bold=False))
        paras.append(p)
    return paras

# ════════════════════════════════════════════════════════════════════════════
# BLOQUE 9.9 – Importancia del Pipeline
# ════════════════════════════════════════════════════════════════════════════
def bloque_99():
    paras = []
    paras.append(build_para('Heading2', [('9.9 Importancia del Pipeline en el Contexto Academico y Empresarial', False)]))
    paras.append(build_para('Normal', [(
        'La implementacion de este flujo de CI/CD no es unicamente un requisito tecnico; '
        'representa la adopcion de una cultura de ingenieria de software moderna y profesional. '
        'En un entorno empresarial real, cada minuto de caida significa perdidas economicas '
        'directas. El pipeline implementado garantiza cuatro propiedades fundamentales:', False)]))

    props = [
        ('Calidad garantizada: ',
         'Ningun codigo defectuoso llega jamas a los usuarios finales; el Paso 3 actua como barrera impenetrable.'),
        ('Velocidad de entrega: ',
         'El equipo puede publicar mejoras multiples veces al dia con total confianza y sin procedimientos manuales.'),
        ('Trazabilidad completa: ',
         'Cada ejecucion queda registrada en GitHub con logs detallados, fechas y resultado de cada paso, habilitando auditoria completa.'),
        ('Automatizacion end-to-end: ',
         'GitHub Actions cierra el ciclo completo: desde el commit del desarrollador hasta el servidor en la nube, sin intervencion humana adicional.'),
    ]
    for bold_txt, normal_txt in props:
        p = new_para(doc, 'ListParagraph')
        p.append(make_run(bold_txt, bold=True))
        p.append(make_run(normal_txt, bold=False))
        paras.append(p)
    return paras

# ════════════════════════════════════════════════════════════════════════════
# INSERTAR EN EL CUERPO DEL DOCUMENTO
# ════════════════════════════════════════════════════════════════════════════
body = doc.element.body
paragraphs = body.findall(qn('w:p'))

def get_text(p_elem):
    return ''.join(t.text or '' for t in p_elem.iter(qn('w:t')))

# Detectar posicion del ultimo bullet de 9.1 (justo antes de 9.2 Catalogo)
# y posicion del encabezado de la seccion 10 (para insertar 9.8/9.9 antes)
idx_after_91 = None   # indice despues del cual insertar 9.1.1
idx_before_10 = None  # indice antes del cual insertar 9.8 y 9.9

all_children = list(body)

for i, child in enumerate(all_children):
    if child.tag == qn('w:p'):
        txt = get_text(child)
        # Encontrar "9.2 Módulo de Catálogo" → insertar 9.1.1 ANTES de este
        if '9.2' in txt and 'Cat' in txt and idx_after_91 is None:
            idx_after_91 = i
        # Encontrar "10." o "10. Modelos" → insertar 9.8/9.9 ANTES de este
        if txt.strip().startswith('10.') and idx_before_10 is None:
            idx_before_10 = i

print(f"Insertar 9.1.1 antes del indice: {idx_after_91}")
print(f"Insertar 9.8/9.9 antes del indice: {idx_before_10}")

# Insertar bloques (de atras hacia adelante para no desplazar indices)
if idx_before_10 is not None:
    ref_node = all_children[idx_before_10]
    for p in reversed(bloque_99()):
        body.insert(list(body).index(ref_node), p)
    for p in reversed(bloque_98()):
        ref_node = list(body)[idx_before_10]  # re-calcular tras insercion
        body.insert(list(body).index(ref_node), p)

if idx_after_91 is not None:
    ref_node = list(body)[idx_after_91]
    for p in reversed(bloque_911()):
        body.insert(list(body).index(ref_node), p)

doc.save(DST)
print(f"\n✅ Documento guardado como: {DST}")
print("   Estructura de Seccion 9:")
print("   9.1   Autenticacion y Perfiles")
print("   9.1.1 Pruebas de Aislamiento del Microservicio  ← NUEVO")
print("   9.2   Catalogo y Productos")
print("   9.3   Carrito de Compras")
print("   9.4   Pedidos y Checkout")
print("   9.5   Facturacion Electronica")
print("   9.6   Reportes")
print("   9.7   Auditoria")
print("   9.8   Pipeline CI/CD con GitHub Actions        ← NUEVO")
print("   9.9   Importancia del Pipeline                 ← NUEVO")
print("   10.  Modelos de Datos")
