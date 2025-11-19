# Examples

Este directorio contiene ejemplos completos para demostrar el uso de los addons del ecosistema de Herramientas de Diseño de Residuo Cero en Blender. El objetivo es proporcionar archivos prácticos para aprender, probar y verificar el correcto funcionamiento del pipeline/proceso:

Patronaje → Relleno → Coser → Doblar → Exportar SVG → Simulación / Impresión

---

## 1. Patrones (carpeta `patrones`)

Contiene archivos .blend preparados para abrir directamente en Blender 3.6 o superior:


---

## 2. Render Demo (carpeta `render_demo`)

Contiene imágenes renderizadas que muestran:

- Doblado del patrón  
- Costura virtual del patrón  
- Simulación Cloth en diferentes etapas  
- Render final de ejemplo

Estas imágenes se utilizan para documentación y como referencia visual.

---

## 3. SVG Outputs (carpeta `svg_outputs`)

Contiene archivos SVG generados con el addon Exportar SVG. Estos SVG incluyen:

- Paths cerrados continuos  
- Capas organizadas  
- IDs por vértice  
- Líneas auxiliares  
- Cotas internas y externas  
- Capa simple  
- Marco exterior

Los SVG pueden abrirse en Inkscape o programas de corte láser (tentativamente).

---

## Cómo usar estos ejemplos

1. Abrir cualquier archivo .blend dentro de la carpeta `patrones`.
2. Activar los addons del repositorio: Patronaje, Relleno, Coser, Doblar y Exportar SVG.
3. Seguir el flujo recomendado:
   - Generar o actualizar el patrón  
   - Construir la malla de relleno  
   - Aplicar costuras  
   - Crear pliegues  
   - Asignar Cloth  
   - Exportar SVG  
4. Utilizar las carpetas `render_demo` y `svg_outputs` como referencia para validar los resultados.

---

## Objetivo de los ejemplos

- Mostrar el funcionamiento de cada addon en un entorno real.  
- Facilitar el aprendizaje para nuevos usuarios.  
- Proveer material de testing para desarrollo.  
- Servir como base visual para documentación y presentaciones.

---

## Licencia

GPL-3.0 license
Los archivos dentro de `examples/` pueden usarse libremente para estudio, pruebas, documentación y demostración del software.

