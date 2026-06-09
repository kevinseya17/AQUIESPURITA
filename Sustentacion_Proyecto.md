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

## 6. Arquitectura, Herramientas Utilizadas y DevOps
*(Basado en su tecnología actual)*

- **Arquitectura:** Monolítica / MVC (Modelo-Vista-Controlador) con base en el framework Django (Python).
- **Backend:** Python con Django.
- **Frontend:** HTML5, CSS3, JavaScript (Motor de plantillas de Django).
- **Base de Datos:** SQL (Ej. PostgreSQL en producción / SQLite en desarrollo).
- **Despliegue y Nube:** Vercel (PaaS - Plataforma como Servicio).
- **DevOps (Pipeline CI/CD con GitHub Actions):** Teniendo en cuenta la Guía del curso, aplicaremos un "Pipeline de Desarrollo de Software" con los siguientes pasos automatizados (Ejemplo Práctico 1):
  - **Paso 1 (Descargar el código):** GitHub Actions clona el repositorio cada vez que se hace un `push`.
  - **Paso 2 (Compilar el proyecto):** Se prepara la máquina virtual, se instala Python y se descargan las librerías necesarias del `requirements.txt`.
  - **Paso 3 (Ejecutar pruebas):** Se realizan chequeos de integridad de Django (`manage.py check`) y pruebas automáticas.
  - **Paso 4 (Generar versión lista):** Se recolectan los archivos estáticos (`collectstatic`) para preparar la versión de producción.
  - **Paso 5 (Despliegue en el servidor):** Una vez validado, la aplicación se despliega automáticamente en **Vercel**.

## 7. Integrantes
- **Frontend:** Kevin Camilo Molina Salazar - `molina.kevin@correounivalle.edu.co`
- **Backend:** Santiago Bedon Gomez - `santiago.bedon@correounivalle.edu.co`
- **Admin BD y Documentadora:** Daniela Martínez Fontal - `daniela.fontal@correounivalle.edu.co`
