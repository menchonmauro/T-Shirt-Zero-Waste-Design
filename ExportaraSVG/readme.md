# Exportar a SVG 

Este addon exporta patrones en formato SVG 1:1 con calidad profesional. Es parte del flujo de herramientas para diseño de prendas de residuo cero dentro de Blender.

> [!WARNING]
> Este addon está en desarrollo, si bien funciona, no es el funcionamiento esperado.
---

## Características principales

- Exporta el patrón como paths cerrados continuos.
- Escala 1:1 real, lista para impresión.
- Multiples unidades: cm, mm, in, px, pt.
- Capas de información:
  - Trazos del patrón
  - IDs de vértices
  - Líneas auxiliares
  - Cotas internas
  - Cotas externas (ordinadas)
  - Marco exterior
  - Capa simple (promedio de curvas cercanas)
- Tipografías configurables (tamaño, unidad, porcentaje relativo).
- Proyección a cualquier plano del patrón.
- Cálculo inteligente de posición, marco y altura del documento.
- Compatibilidad con:
  - Inkscape
  - Scribus
  - Plotters de corte
  - Máquinas CNC
  - Impresión tradicional

> [!CAUTION]
> Por ahora funciona solo la capa del patrón, actualmente en desarrollo

---

## Requisitos

- Blender 3.6 o superior.
- Un objeto Mesh que represente el patrón final.

---

## Instalación

1. Abrir Blender  
2. Edit → Preferences → Add-ons  
3. Install…  
4. Seleccionar el archivo `.py` correspondiente  
5. Activar el addon  
6. Ir al N-Panel → Exportar → Exportar SVG

---

## Uso

1. Seleccionar el objeto patrón.  
2. Ajustar propiedades:
   - Unidad del documento  
   - Tipografía  
   - Stroke  
   - Cotas internas y externas  
   - Capa simple  
3. Ejecutar “Exportar a SVG”.  
4. El archivo se genera automáticamente en la carpeta:
   **~/Desktop/exports/patrones/**  
   (o la especificada por el usuario).

---

## Flujo recomendado

Patronaje → Relleno → Coser → Doblar → **Exportar SVG** → Impresión / Corte / Archivo digital.

---

## Changelog

Ver archivo CHANGELOG.md.

---

## Licencia

GPL-3.0 license
Open Source – puede utilizarse, modificarse y adaptarse libremente.
