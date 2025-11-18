
# Patronaje: Remera de Diseño de Residuo Cero – Zero Waste T-Shirt (Complemento Blender - Blender Add-on)

Complemento para **Blender** que genera patrones paramétricos de remeras de diseño de **residuo cero**, permitiendo editar proporciones, aplicar medidas manuales y trabajar con restricciones inteligentes basadas en reglas reales de patronaje.

Incluye:

* Transformación completa de **manga** y **cuello**.
* Sistema de **guardado y carga de medidas** (`.json`) para continuar proyectos.
* Vista previa paramétrica en tiempo real.
* Controles avanzados para escalado, offsets y medidas manuales.

---

## Características principales

### Manga

* Ajuste paramétrico con reglas pre establecidas.
 
* Escalado en X controlable por:
  * Profundidad manual.
  * Profundidad automática (1/2 del ancho total).
  * Escala X opcional.
* Escalado Y limitado automáticamente para evitar deformaciones irreales.

### Cuello

* Puede seguir o no el escalado general del patrón.
* Medidas manuales disponibles:

    * Escala X.
    * Escala Y.

### Sistema de medidas manuales

* Para manga:

  * Distancias desde bordes inferior o lateral.
  * Distancia sisa-a-sisa.
  * Bloqueo de relaciones entre la costura de la espalda y la sisa.
* Para cuello:

  * Base del cuello (mitad).
  * Base total 
  * Distancia desde el borde inferior a la base del cuello.
  * Distancia desde el borde inferior al cuello.

### Guardar / Cargar Configuraciones

Podés guardar todas tus medidas, escalas y estados del patrón como **preset JSON**, y luego cargarlo para continuar el mismo proyecto.

Ideal para:

* Diferentes talles.
* Pruebas.
* Plantillas personalizadas.

---

## Instalación

1. Descargá el archivo `.zip` del release.
2. En Blender, ir a:

   ```
   Edit > Preferences > Add-ons > Install...
   ```
3. Seleccioná el `.zip`.
4. Activá:

   ```
   Patronaje: Remera de Diseño de Residuo Cero
   ```
5. Abrir el panel en
   **N-Panel → Remera de Diseño de Residuo Cero**

---

## Uso básico

### 1. Crear el patrón

Presioná:

```
Crear Nuevo Patrón
```

El patrón se genera anclado en la esquina inferior derecha  → origen 0,0).

### 2. Ajustar dimensiones de la tela

* Ancho.
* Alto.
* Mantener proporción (opcional).

### 3. Modificar forma de la manga

* Profundidad automática (½ ancho).
* Escala X e Y.
* Offset vertical.
* Medidas manuales de la sisa y la costura de la espalda.

### 4. Modificar el cuello

* Escalas independientes.
* Profundidad.
* Offsets verticales.
* Medidas manuales.
* Límites superiores estricos para no exceder la tela.

### 5. Actualizar patrón

Si desactivaste “Vista previa en tiempo real”, usá:

```
Actualizar Patrón
```

---

## Guardar y cargar presets de medidas

En el panel principal aparece una sección:

### **Guardar / Cargar medidas**

#### Guardar

```
💾 Guardar medidas…
```

Genera un archivo `.json` con TODAS las propiedades de `patron_props`.

#### Cargar

```
📁 Cargar medidas…
```

Carga un preset previamente guardado y actualiza el patrón.

Esto incluye:

* Dimensiones
* Escalas y offsets
* Medidas manuales
* Posición del objeto
* Configuración del cuello y la manga

---

## Flujo de trabajo recomendado

1. Crear un patrón base.
2. Ajustar todas las medidas necesarias.
3. Guardar medidas como:

   ```
   talle_S.json
   talle_L_variante_manga.json
   ```
4. Reabrir Blender y cargar el preset deseado.
5. Continuar el mismo diseño sin perder nada.

---

## Estructura interna

* Patrón original definido por `PATRON_DATA_ORIGINAL`.
* Transformaciones aplicadas mediante:

  * Escalado global.
  * Reescalado específico en manga y cuello.
  * Offsets independientes.
* Límites verticales rígidos:

  * 2 cm arriba y abajo para puntos críticos.
* Reglas para mantener la distancia.
* Cuello con escala independiente y reglas de límite.

---

## Compatibilidad

* Blender **3.6+**
* No requiere dependencias externas.
* 100% compatible con archivos `.blend` estándar.

---

## Licencia

GPL-3.0 license

---

## Créditos

Desarrollado por **Mauro Menchón**
Asistencia técnica y adaptación lógica mediante IA.

---
