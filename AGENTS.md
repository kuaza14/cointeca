# Instrucciones y Contexto del Proyecto para Agentes de IA (AGENTS.md)

Este documento define la arquitectura, convenciones y reglas de negocio de **Cointeca S.A.S.** para que cualquier agente de IA o chat nuevo tenga contexto inmediato del proyecto.

---

## 1. Stack Tecnológico

- **Backend:** Python + Django 5.2
- **Base de Datos:** PostgreSQL (`cointeca_db`). Localmente en puerto 5432 o vía Docker en puerto 5433 (`localhost:8001`).
- **Frontend:** Django Templates + Tailwind CSS v4 (compilado con `@theme` en `static/css/input.css`).
- **Comandos habituales:**
  - Servidor local: `python manage.py runserver`
  - Docker: `docker compose up -d`
  - Tailwind (desarrollo): `npm run dev`

---

## 2. Estructura de Directorios

- `core/models.py`: Modelos principales de datos (Macroproyectos, Proyectos, Materiales, Apoyos, Entradas, etc.).
- `core/views/`: Controladores organizados modularmente por departamento:
  - `logistica/`:
    - `proyectos_materiales.py`: Gestión central de macroproyectos, asignación de materiales, entradas y consumos por proyecto.
    - `materiales.py`: Catálogo general de materiales e inventarios.
    - `dotacion.py`: Gestión de dotación para personal.
  - `ingenieria/`: Definición de proyectos, cálculos técnicos y requerimientos de obra.
  - `rrhh/`: Personal, contratos y documentación laboral.
  - `contabilidad/`: Facturación, costos y presupuestos.
  - `gerencia/`: Reportes consolidados y métricas ejecutivas.
- `core/templates/`: Plantillas HTML organizadas por módulo.
- `static/`: Recursos estáticos (CSS procesado, JS, imágenes).

---

## 3. Reglas de Negocio Clave

### Flujo de Logística vs. Obra
1. **Entradas asociadas a Proyecto:**
   - La entrada de materiales se asigna directamente al **Proyecto** correspondiente en el momento en que ingresa a la empresa.
2. **Consumo reportado por supervisores:**
   - Los supervisores de obra entregan periódicamente el reporte de materiales efectivamente utilizados en terreno.
   - Logística registra este consumo real sobre el material ya asignado.
3. **Comparativa Ingeniería vs. Logística:**
   - **Ingeniería:** Define el material *requerido / calculado* técnicamente.
   - **Logística:** Registra el material *ingresado* y el material *consumido*.
   - El sistema compara `Requerido` vs. `Ingresado` vs. `Consumido` para obtener saldos y desviaciones.

---

## 4. Convenciones de Desarrollo

- **Diseño UI:**
  - Utilizar las clases semánticas de Tailwind definidas en el proyecto: `btn btn-primario`, `btn btn-secundario`, `tabla-caja`, `bg-primary`, `text-muted-foreground`.
  - Evitar colores arbitrarios o estilos en línea `style="..."` siempre que existan clases equivalentes.
- **Rendimiento y edición de código:**
  - `core/views/logistica/proyectos_materiales.py` es un archivo extenso. Al consultar o editar, buscar directamente la función específica sin reescribir bloques ajenos.
  - Mantener transacciones atómicas (`transaction.atomic`) en operaciones que involucren movimientos de stock o inventarios.
