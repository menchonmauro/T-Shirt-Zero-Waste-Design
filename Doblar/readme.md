# Doblar – Addon para Blender

Doblar es un complemento para Blender 3.6 que permite generar pliegues no destructivos en patrones de residuo cero utilizando aristas tipo *seam* o edges seleccionadas. Es útil para prendas Zero Waste donde la tela se pliega sobre sí misma antes del cosido virtual.

> [!WARNING]
> Si bien funciona, la interfaz de usuario y la usabilidad debe o puede mejorarse.

> [!CAUTION]
> Pronto se mejorará su funcionalidad.

---

## Características principales

- Detecta automáticamente cada seam como un pliegue.
- Genera:
  - Pivotes vacíos (Empty) orientados según la dirección del seam.
  - Grupos de vértices sólidos.
  - Modificadores Bend con ángulo configurable.
- Funcionamiento no destructivo.
- Control de lado: ambos, positivo o negativo.
- Modos de cobertura:
  - ALL (todo sólido)
  - RANGE (área rectangular local)
  - SEAM_STRIP (tirilla rígida alrededor del seam)
- Limitación opcional por topología (bordes reales de la malla).
- Herramientas para recalcular un pliegue por índice sin regenerarlos.
- Vista directa del grupo de pesos para un pliegue.
- Sistema de combinación (AND / OR) para un solo pliegue maestro.

---

## Requisitos

- Blender 3.6
- Un objeto Mesh con seams marcados donde se quiera doblar.

---

## Instalación

1. Abrir Blender.  
2. Edit → Preferences → Add-ons  
3. Install…  
4. Elegir el archivo `.py` del addon Doblar  
5. Activarlo  
6. Abrir N-Panel: pestaña **Doblar**

---

## Uso

1. En modo Edición, marcar como seam las aristas donde se quiere el pliegue.  
2. En el panel Doblar → presionar “Crear pliegues”.  
3. Ajustar ángulos, cobertura, lado o barreras.  
4. Si es necesario modificar un pliegue sin generar todo nuevamente:  
   - Seleccionar un índice  
   - Ajustar parámetros  
   - Presionar “Recalcular (índice)”  
5. Para ver el grupo afectado: “Ver grupo (índice)”.

---

## Flujo de trabajo recomendado

Patronaje → Tela (relleno) → Coser → **Doblar** → Exportar SVG → Simulación Cloth.

---

## Changelog

Ver archivo CHANGELOG.

---

## Licencia

GPL-3.0 license
Open Source. Se permite modificar, estudiar y adaptar a cualquier proyecto de diseño de indumentaria o investigación.
