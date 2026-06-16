# Documento de Sustentación: Proyecto "Lácteos Aquí Es Purita"
**Asignatura:** Desarrollo de Software III

---

## 1. Nombre del Proyecto
**Implementación E-commerce "Lácteos Aquí Es Purita"**

## 2. Descripción
El proyecto surge por la necesidad de digitalizar la venta de productos lácteos, mejorando la experiencia del cliente y la eficiencia interna.

- **Racional de negocio:** Ofrecer una plataforma de compra intuitiva con carrito, pagos seguros y seguimiento de pedidos.
- **Eficiencia operacional:** Optimizar el control de ventas, inventario y atención al cliente.
- **Fundamento técnico:** Implementar una arquitectura modular basada en API REST que garantice escalabilidad y fácil mantenimiento.

## 3. Planteamiento del Problema
La empresa “Lácteos Aquí es Purita” gestiona sus ventas y procesos de forma manual o con herramientas limitadas, lo que genera errores, demoras y poco control del inventario.

Además, no cuenta con un canal digital de ventas, lo que afecta la experiencia del cliente y la competitividad del negocio. Por ello, se requiere una solución tecnológica que permita digitalizar y optimizar los procesos mediante una arquitectura de software integrada y escalable.

## 4. Objetivo Principal y Objetivos Específicos
### Objetivo General
Diseñar una arquitectura de software integrada, escalable y basada en la nube que garantice buen rendimiento, disponibilidad y optimización de costos.

### Objetivos Específicos
- Integrar los módulos del sistema y servicios externos mediante API.
- Permitir la expansión con nuevas funcionalidades sin afectar la estabilidad.
- Implementar infraestructura en la nube con base de datos SQL para asegurar rendimiento y disponibilidad.
- Optimizar costos usando recursos bajo demanda.

## 5. Alcance
La plataforma proporciona a los usuarios una experiencia de compra intuitiva, con funciones como el carrito de compras, pagos en línea seguros y seguimiento de pedidos. Además, permitirá a la empresa tener un control más eficiente sobre las ventas, el inventario y la atención al cliente.

## 6. Arquitectura y Herramientas Utilizadas
El proyecto ha evolucionado de una arquitectura monolítica clásica a una arquitectura más distribuida (Microservicios) basándose en el patrón Hexagonal:
- **Base Principal:** Python 3.11 / 3.12 con el framework Django 5.1.7.
- **Frontend / UI:** HTML5, CSS3, JavaScript puro apoyado en Bootstrap 5 y Crispy Forms.
- **Microservicio de Autenticación (`auth_microservice`):** Módulo en Python puro, separado físicamente, basado en la Arquitectura Hexagonal (Capa de Dominio, Aplicación e Infraestructura). Interactúa mediante un API Gateway local (`ms_gateway.py`).
- **Base de Datos:**
  - Desarrollo: SQLite 3.
  - Producción: PostgreSQL administrado por Render (vía `dj-database-url` y `psycopg2`).
- **Archivos Estáticos y Medios:**
  - Reportes PDFs y Excel: Generación automática usando `ReportLab` y `openpyxl`.
  - Imágenes: `django-cloudinary-storage` que aloja recursos en la CDN de Cloudinary.
  - Estáticos: Servidos limpiamente mediante WhiteNoise autoadministrado.
- **Generación de Códigos Diarios:** Módulo `qrcode` y librerías de encriptación interna de Django para emitir el código CUFE y visuales.

## 7. Pruebas y Validación del Software
Como parte vital de nuestro enfoque técnico, integramos métodos estrictos de validación, garantizando que los componentes funcionen aislados de las fluctuaciones de la Base de Datos o el entorno local:
- **Testeo del Microservicio Individual (`test_run.py`):** Realizamos inyecciones manuales en nuestra capa de lógica de negocio pura (simulando casos HTTP) utilizando un repositorio en memoria (`in_memory_repository.py`) para confirmar respuestas 200 OK frente a 401 Unauthorized sin comprometer la base de datos real.
- **Dry-Run Migratorio y Chequeos Generales:** Como parte integral (y para evitar fallos catastróficos), probamos las migraciones forzando verificaciones (`makemigrations --dry-run` y `manage.py check`). Un error en un modelo o relación frena en seco el despliegue en vez de colapsar la aplicación principal.
- **Uso Dinámico de Variables:** Verificamos de forma controlada si la conexión fluye hacia `localhost` o hacia los proveedores SaaS para descartar cruce de entornos nocivos.

## 8. Estrategia DevOps y Pipeline CI/CD Automatizado
Teniendo en cuenta las guías y estándares avanzados, aplicamos una canalización de Desarrollo de Software y Entrega Continua estricta con **GitHub Actions**. El entorno nube y servidores PaaS solo reciben código con certificación de 100% éxito.

El flujo de trabajo automatizado (`.github/workflows/pipeline-ci-cd.yml`) consta de 5 pasos técnicos robustos que se ejecutan unicamente desde la rama `main` al confirmarse un _push_:
1. **Descargar y Aislar (Checkout):** Aprovisionamiento seguro del sistema y clonación en la máquina virtual linux (`actions/checkout@v3`).
2. **Compilar (Dependencies):** Instalación determinista de entorno virtual para `Python 3.11`, seguida de las descargas obligatorias de de dependencias vía `requirements.txt`.
3. **Pruebas (Test Checks):** Comprobación de modelos defectuosos utilizando chequeos de integridad de Django. Esta es la barrera más importante que garantiza que ningún modelo base romperá la BD en la nube.
4. **Construir Versiones de Rendimiento (Collectstatic):** Preparación de assets de frontend para su servida óptima a los clientes (`collectstatic --noinput`).
5. **Despliegue Multi-Cloud (Publish):** Engranaje estricto con los endpoints Render (con archivo propio de infraestructura _render.yaml_ y servidor _Gunicorn_) y alternativamente _Vercel_, automatizando su actualización pública sin tumbar el sistema (Zero Downtime).

## 7. Integrantes
- **Frontend:** Kevin Camilo Molina Salazar - `molina.kevin@correounivalle.edu.co`
- **Backend:** Santiago Bedon Gomez - `santiago.bedon@correounivalle.edu.co`
- **Admin BD y Documentadora:** Daniela Martínez Fontal - `daniela.fontal@correounivalle.edu.co`
