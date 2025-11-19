# Relleno v0.0.1. (En desarrollo. No funciona correctamente)

Este addon genera una malla interior perfecta para simulaciones de tela a partir del contorno de un patrón de residuo cero. Implementa un método para rellenar un patrón de manera uniforme, con un grid regular y sin huecos.

> [!CAUTION]
> No funciona correctamente, falta continuar desarrollándolo.

> [!NOTE]
> Hasta que esté funcional sustituir con el addon [Modeling Cloth]([https://pages.github.com/](https://github.com/the3dadvantage)) para blender 3.6, utilizar la función MC Grid Tools. (size: 0.01, Sin triángulos). 

---

## Características principales

- Detecta automáticamente el contorno del patrón.
- Proyección inteligente al plano adecuado.
- Genera:
  - Inner ring uniforme (V/H consistentes).
  - Grid0 alrededor del inner.
  - Quad caps en esquinas cóncavas.
  - Relleno homogéneo sin huecos.
- 100% quads, sin triángulos.
- Malla totalmente cerrada y lista para Cloth.
- Mantiene la forma del patrón con fidelidad métrica.
- Apto para patrones complejos y diseño de residuo cero.

---

## Requisitos

- Blender 3.6
- Un patrón generado previamente (por ejemplo con el addon Patronaje)

---

## Instalación

1. Abrir Blender  
2. Edit → Preferences → Add-ons  
3. Install…  
4. Seleccionar el archivo `.py` del addon  
5. Activarlo  
6. Ir al N-Panel → Relleno

---

## Uso

1. Seleccionar el objeto patrón (mesh).  
2. Ejecutar “rellenar”.  
3. El addon:
   - Identifica el contorno  
   - Calcula el inner  
   - Construye Grid0  
   - Rellena el interior con quads  
   - Reconstruye el modelo 3D  
4. Guardar o continuar con:
   - Coser  
   - Doblar  
   - Cloth  
   - Exportar SVG

---

## Flujo de trabajo recomendado

Patronaje → **Relleno** → Coser → Doblar → Exportar SVG → Simulación Cloth.

---

## Changelog

Ver archivo CHANGELOG.md.

---

## Licencia

GPL-3.0 license
Open Source – se permite estudiar, modificar y utilizar el addon para investigación o producción.
