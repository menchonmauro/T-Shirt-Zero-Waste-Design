# Manual de Instrucciones en Español – Versión corta

#### 1. Pasos previos necesarios

- Instalar [Blender 3.6 LTS](https://www.blender.org/download/releases/3-6/)
- Descargar el conjunto de [complementos desde Github](https://github.com/menchonmauro/T-Shirt-Zero-Waste-Design/archive/refs/heads/main.zip)
  - Instalar los complementos:
    - [patronaje.py](https://github.com/menchonmauro/T-Shirt-Zero-Waste-Design/blob/main/Patronaje/patronaje-v310-alpha.py)
    - [coser.py](https://github.com/menchonmauro/T-Shirt-Zero-Waste-Design/blob/main/Coser/Coser-v100.py)
    - [doblar.py](https://github.com/menchonmauro/T-Shirt-Zero-Waste-Design/blob/main/Doblar/Doblar-v100.py)
    - [exportaraSVG.py](https://github.com/menchonmauro/T-Shirt-Zero-Waste-Design/blob/main/ExportaraSVG/ExportaraSVG-v100.py)
  - Ruta de instalación:
    - **Editar > Preferencias > Complementos > Instalar**
- Descargar e instalar el complemento [Modeling Clothes](https://github.com/the3dadvantage)

---

##### Limpiar la escena inicial de Blender y definir la vista frontal

- En la Vista 3D presionar la tecla **"A"** (Seleccionar todo) y luego **"X"** o **"Suprimir"** (Eliminar selección)
- Presionar **"5"** y luego **"1"**  
  (Configura la vista ortogonal y posiciona la vista frontal)

---

#### 2. Crear el patrón de la remera

##### Abrir el complemento y generar el patrón de la remera

- Presionar la tecla **"N"** y buscar en el panel lateral el complemento **"Patronaje"**, con el nombre **"Remera de diseño de residuo cero"**
- Hacer clic en **"Crear nuevo patrón"**
- Ingresar las medidas del tamaño de la tela, mangas y cuello, o ajustarlas visualmente en tiempo real
- Guardar las medidas o cargar medidas previamente guardadas  
  ([descargar patrones de ejemplo](https://github.com/menchonmauro/T-Shirt-Zero-Waste-Design/tree/main/examples/patrones))

---

#### 3. Rellenar el patrón (método alternativo)

- Utilizar el complemento **Modeling Clothes**
- Seleccionar el patrón y ajustar los valores en **MC Grid Tools**
- Configuración recomendada:
  - Límite angular: **20**
  - Tamaño: **0.010000**
  - Distancia de unión (Merge Distance): **1.100**
  - Iteraciones de suavizado (Smooth Iterations): **10**
  - Triángulos: **desactivado**

##### Aplicar simetría para obtener el tamaño completo de la tela

- Seleccionar el patrón relleno (objeto nuevo)
- Ir a **Modificadores > Agregar modificador > Simetrizar**
- Aplicar el modificador:
  - Desde el panel del modificador, desplegar la flecha y hacer clic en **Aplicar**
  - O con el cursor sobre el modificador, presionar **"Ctrl + A"**

---

#### 4. Coser el patrón

- Seleccionar el patrón relleno y entrar en **Modo Edición** presionando **"TAB"**
- Dentro del Modo Edición, seleccionar pares de bordes a coser

##### A) Coser mangas

- Seleccionar el borde inferior de la manga derecha y luego el borde superior correspondiente
- Aplicar el complemento **"Coser"**

  - Seleccionar el primer vértice del borde
  - Presionar **Ctrl + botón izquierdo del mouse** sobre el último vértice del mismo borde
  - Con un lado seleccionado, seleccionar la misma cantidad de vértices en el borde superior:
    - **Shift + clic** en el primer vértice
    - **Ctrl + clic** en el último vértice

  > [!NOTE]
  > Para conocer la cantidad de vértices seleccionados:
  > activar **Sobreimpresos (Overlays) > Estadísticas**.
  > La cantidad de vértices seleccionados en ambas series debe ser la misma.

- Con los bordes seleccionados, presionar **"N"** para abrir el panel lateral
- Buscar el complemento **"Coser"**, presionar **"Coser"** y luego **"Aceptar"**
- Se generan líneas entre los vértices, uniendo los bordes a coser

---

##### B) Coser parte trasera horizontal

- Seleccionar el borde ubicado debajo de la manga
- Seleccionar luego el borde desde el centro del patrón hacia la manga, respetando la cantidad de vértices

  > [!NOTE]
  > Este tipo de costura es invertida.
  > Con los bordes seleccionados:
  > - Presionar **"N"**
  > - Abrir el complemento **"Coser"**
  > - Presionar **"Coser"**
  > - Activar **"Invertir serie A"**
  > - Presionar **"Aceptar"**

---

##### C) Coser parte trasera vertical

- Seleccionar los bordes laterales que no forman parte de las mangas
- Coser de manera normal, sin invertir las series

> [!TIP]
> El cuello puede coserse o dejarse sin coser.
> Para evitar deformaciones incorrectas en la simulación,
> se puede coser un vértice de la tapa del cuello con un vértice de la espalda.

---

#### 5. Doblar el patrón

- Seleccionar el patrón ya cosido y entrar en **Modo Edición** (**"TAB"**)
- Seleccionar aristas o bucles de vértices donde se desee doblar la prenda
- Con una arista seleccionada, presionar **"Ctrl + E"** y elegir **"Marcar como costura"**
- Marcar tantas aristas como sea necesario para mejorar el doblado
- Presionar **"N"**, abrir el panel lateral y seleccionar el complemento **"Doblar"**
- Hacer clic en **"Crear pliegues"**

- Se crean ejes en el centro de cada costura marcada, generando zonas de doblado
- Al hacer clic en **"Ver grupo (Índice)"** se muestra el mapa de influencias
- Ajustar **"Lado (Índice)"** en **-X** o **+X** para definir la dirección del doblado
- Ajustar **"Ancho (Índice)"**, **"Largo (Índice)"** y **"Margen (Índice)"**
- Presionar **"Aplicar configuración de pliegue"** para visualizar los cambios

  > [!NOTE]
  > Cada índice representa una costura marcada.
  > Si existen 5 costuras, habrá 5 índices (0 a 4) asignados automáticamente.

- Luego de configurar todos los índices:
  - Ir a la pestaña **Modificadores**
  - Ajustar el **Ángulo** de cada zona de doblado
  - Valores negativos doblan hacia un lado, valores positivos hacia el contrario

---

#### 6. Armar y visualizar la prenda sobre un gemelo digital

##### Asignar propiedades de tela al patrón

- Con el objeto seleccionado, ir a **Propiedades de Física > Ropa (Cloth)**
  - Ejemplo de una tela batista de **1,11 m × 0,95 m**, con un peso de **67 g**
  - Blender utiliza kilogramos:
    - **67 / 1000 = 0,067 kg**
  - Área real:
    - **1,11 × 0,95 = 1,0545 m²**
  - Densidad areal (GSM):
    - **0,067 / 1,0545 = 0,06354 kg/m²**

  > [!NOTE]
  > Conociendo la densidad areal (GSM) se puede calcular o verificar
  > la masa total de la prenda:
  > **Área × GSM = masa total**

  - Consultar la cantidad de vértices en **Sobreimpresos > Estadísticas**
  - Masa de vértices:
    - **masa total / cantidad de vértices**
    - Ejemplo: **0,067 / 24443 = 2,7410710632901E-06 ≈ 0.000002741**

  > [!IMPORTANT]
  > Siempre calcular la masa de vértices.
  > Se pueden desarrollar complementos para automatizar estos cálculos.

  - Ingresar el valor en **Ropa > Masa de vértices**
  - Definir los siguientes parámetros:
    - Intervalos de calidad: **20**
    - Multiplicador de velocidad: **0.500**
    - Masa de vértices: **0.000003**

  - Activar **Forma > Costura**
    - Fuerza máxima de costura: **5**

  - Activar **Colisiones**
    - Distancia con objetos: **0.001 m**

  - Activar **Colisiones propias**
    - Fricción: **5**
    - Distancia: **0.0025**

---

##### Asignar propiedades de colisión al gemelo digital

- Seleccionar el gemelo digital
- Ir a **Propiedades de Física > Colisión**
  - Grosor exterior: **0.002**

---

#### 7. Exportar el patrón en formato vectorial SVG
- Presionar la tecla **"N"** y buscar en el panel lateral el complemento **"Exportar"**
  
  1. Seleccionar el objeto patrón  
   (el patrón original sin rellenar)
  2. Ajustar las propiedades:
      - Unidades del documento
      - Tipografía
      - Trazo (Stroke)
      - Cotas internas y externas
      - Capa simple
  3. Hacer clic en **"Exportar a SVG"**
  4. El archivo se genera automáticamente en la carpeta:
   **~/Desktop/exports/patrones/**
   (o en la ruta definida por el usuario)
  5. Abrir el archivo con [Inkscape](https://inkscape.org/release/inkscape-1.4.2/windows/)

