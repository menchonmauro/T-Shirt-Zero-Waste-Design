Manual v11.25 (mes/año - month/year)

> [!IMPORTANT]
> Manual en proceso de confección.


# Introducción

Este manual explica el proceso utilizado para crear principalmente remeras y blusas, como así también vestidos utilizando un complemento de código abierto desarrollado en el marco de una investigación a través del diseño dentro de Blender.

El proceso puede realizarse de diferentes maneras, una consiste en  utilizar el complemento generado para esta investigación (saltar hasta Diseño Digital) y otra, es crear los patrones buscando soluciones a medida (leer desde el comienzo de este archivo). 


# Patrón de diseño de residuo cero.

Se puede utilizar como base para crear una síntesis de la forma del diseño un patrón existente que posea atribuciones de derechos que permitan su uso y realizar modificaciones de manera libre, o de un diseño de residuo cero creado por los diseñadores de indumentaria.  

# Diseño del patrón.

Se pueden utilizar diferentes aplicaciones de código abierto, como Seamly2D, Valentina, especializadas en diseño de patrones, Inkscape, potente editor vectorial, para obtener un patròn base, IA para generar la sìntesis de una figura, o se pueden ingresar datos manualmente haciendo uso del sistema de coordenadas (x,y) de manera secuencial, donde cada punto (x,y) representa un nodo que puede denominarse como un vértice conectado a otros vértices mediante una arista para conformar forma cerrada con un origen y un cierre en un mìsmo lugar dentro del entorno de Blender. 

Links Seamly2D, Valentina, Inkscape

# Gemelo digital.

Para la visualización y prueba de caída de la prenda se puede utilizar cualquier modelo tridimensional disponible que represente a una figura humana, o no, mientras se respeten las medidas para las cuales está pensado, o se ajusten a las medidas internas de Blender.

Una alternativa práctica y efectiva es utilizar un modelo humano tridimensional construido en Makehuman, aplicación de código abierto que posibilita la creación de modelos de personas ingresando mediciones según la contextura física, peso, edad y medidas más detalladas. 

Los modelos que se obtienen son compatibles con el flujo de trabajo de Blender, ya sea como base para vestir la prenda o para generar animaciones.

Los modelos se exportan en formato .dae conjuntamente con las texturas y esqueleto necesario para mover o animar sus partes en Blender.

link Makehuman

# Programación | Modificación | Mantenimiento.

El uso de la IA es fundamental para alguien sin conocimientos en programación, ya que la interacción con los distintos modelos de inteligencia artificial permite escribir, interpretar, ajustar y modificar código escrito en el lenguaje Python, utilizado por Blender para sus complementos, en el caso en que los diseñadores o el público en general quisiese elaborar o modificar sus propios complementos.
Un complemento básicamente es una aplicación que se agrega a otra aplicación base. El complemento se nutre de los recursos provistos por la aplicación base para poder llevar a cabo su funcionamiento. 

Mediante la IA se puede sintetizar una forma (patròn, o parte del mismo), partiendo de una imagen o conjunto de datos que luego se transforma en una serie ordenada de puntos de coordenadas compatibles con Python y Blender, que sirve como modelo base para realizar transformaciones paramètricas. El complemento Patronaje desarrollado a continuación se basó en este principio.

# Diseño digital 3D.

## Instalación de Blender.

Es necesario instalar la versión 3.6 de Blender ya que uno de los propósitos de este desarrollo es que sea accesible a la mayor cantidad de personas posible, y esta versión es una de las últimas versiones compatibles para equipos de hasta 10 años de antigüedad. Igualmente cabe destacar que, a través de la IA, se puede adaptar fácilmente el funcionamiento de los complementos a las nuevas versiones Blender.

En la configuración inicial del programa se debe establecer el uso del sistema métrico internacional, ya que todas las medidas están en cm, en próximas versiones se podrá utilizar para los distintos sistemas de medición. 

Los complementos se pueden ejecutar de maneras distintas, una de ellas, cuando el complemento se encuentra en una versión estable, y otra, a demanda, cuando el usuario lo necesita usar o el complemento se encuentra en pleno desarrollo.

La instalación estable se realiza desde las preferencias de Blender, se instala un archivo .zip (conjunto de archivos comprimidos cuando el complemento posee una estructura interna de carpetas o archivos) o .py (cuando es un archivo de Python individual).

La instalación a demanda se realiza dentro del entorno de Blender, en la pestaña "scripts", se crea un documento nuevo haciendo click en "+", se pega el código del complemento en el espacio para el texto y luego se hace click en el botón "play" o "ejecutar". Si el mensaje de la consola es verde, quiere decir que el complemento se instaló correctamente sin errores, por el contrario, si el mensaje es rojo, se emite un error, el cual sirve para ingresarlo dentro de una IA para que corrija el código y volver a probar si se pudo corregir.

En ambos casos luego de instalar o ejecutar el complemento, se debe apretar la tecla "n", para que aparezca un menú lateral, allí figura el complemento con el nombre asignado en el código. Al tocar sobre la pestaña se despliega el complemento listo para ser utilizado.

## Procesos necesarios para la creación de la remera.

A continuación se describe la secuencia propuesta para crear una remera de residuo cero dentro de Blender. Con estos complementos creados exclusivamente para este motivo se pueden crear patrones, dotarlos de un relleno apto para la simulación de tela, coser la tela digital, posicionar el patrón para la visualización y exportar el patrón en formato .svg.

Cada complemento es una herramienta digital que permite experimentar sobre un patrón tanto a diseñadores, estudiantes o particulares sin generar residuos. Estos se encuentran actualmente en desarrollo y por tal motivo se presentan de manera individual para agilizar su desarrollo y evolución. Pudiendo, en un futuro cercano conformar una sola aplicación que incluya todos los complementos integrados.

Los complementos son Patronaje, Tela, Coser, Doblar y Exportar Patrón. La elección de los nombres es intencional y refleja de manera evidente la función que cumplen. 

## Complemento Patronaje

Básicamente es una herramienta digital que permite diseñar patrones de una remera de diseño de residuo cero, en la que se pueden ingresar medidas específicas o se puede manipular los controles de la interfaz para ajustar en tiempo real las medidas de una prenda. Está diseñado para ser utilizado de manera simple, intuitiva y eficaz. En cada momento el usuario puede controlar y ver las medidas ingresadas ya que se calculan en tiempo real.
Las funciones se distribuyen de manera secuencial. Se crea un patrón inicial, se define si se trabaja en la vista frontal o en la superior, se define el tamaño de la tela y luego se ajustan los tamaños y posición tanto del cuello como la manga y se define la posición del patrón del espacio de trabajo de Blender.



### Parámetros.



## Complemento Tela/Relleno

Este complemento se encuentra actualmente en desarrollo, con el se busca crear una malla 3D apropiada para cubrir o rellenar el patrón de residuo cero y así poder asignar las propiedades de Cloth de Blender.

Momentáneamente este paso se realiza utilizando "Grid fill", una herramienta incluida en el complemento de código abierto Modeling Clothes. 

La configuración que se utiliza es la siguiente:


## Complemento Coser

Este tipo de patrón de residuo cero, al estilo bog coat, abrigo de pantano, basado e inspirado en el trabajo de Holly McQuillian y otros, ampliamente desarrollado en el trabajo Make/Use, posee una manera particular de ser cosido virtualmente, que requiere de un método específico, por tal motivo se desarrolló un complemento que cumpla la función de cosido para este caso particular.

Su función es la de unir mediante segmentos o aristas los vértices seleccionados para coser la prenda. Esta prenda posee dos maneras de coser los vértices, una donde los vértices que se cosen en serie ABCD-ABCD y otra donde los vértices se cosen en distinta dirección ABCD-DCBA.

El procedimiento es básico, se seleccionan las series de vértices a coser y se elige en qué dirección coserlo, de manera invertida o no.


## Complemento Doblar 

Al ser una prenda que se cose sobre sí misma, sin partes separadas, esto supone un reto para los programas de diseño, que no están propiamente diseñados para estos escenarios, se creó un complemento que crea doblados de manera no destructiva del modelo u objeto, para luego ejecutar el proceso de cosido y así poder visualizar la prenda. 

Para doblar la prenda el usuario debe seleccionar donde quiere que se doble la prenda, detectamos cuatro puntos de pivote donde se puede hacer un marcaje para el doblado de la prenda. Blender posee una manera de seleccionar aristas, las cuales se llaman costuras o seams. El usuario debe seleccionar cada arista donde habrá un doblez, luego el complemento se encargará de generar los helpers, o ayudadores para que puedan ser editados a gusto, según el diseño obtenido.

Luego de marcar cada doblez, se procede a crear y editar los parámetros para seleccionar qué áreas serán afectadas en el doblez.


## Asignarle la física de Cloth/Ropa de Blender.

Para que un objeto, cualquiera, se comporte con las propiedades de una tela, o verse como una vestimenta dentro de Blender se procede a aplicar "Cloth", al mismo tiempo, la ropa necesita donde apoyarse, y por tal motivo debe crearse un objeto donde colisione mediante "Collision", que puede ser cualquier objeto, un maniquí o un gemelo digital. 

### Cloth / ropa 

Sirve para dotar el comportamiento físico de tela al objeto creado.
Leer en Blender.

Ajustes de parámetros, para una remera de diseño de residuo cero:

Para lograr mejores simulaciones o simulaciones aproximadas al comportamiento que tendrán las prendas en la realidad, los datos ingresados deben ser ajustados para cada situación en particular.

			- Peso total de la tela dividido por la cantidad de vértices.
			- Fricción.
			- Cosido
			- Doblez de la tela

### Collision / Colisión

Ajustes sobre el gemelo digital
			- Peso total de la tela dividido por la cantidad de vértices.
			- Fricción.
			- Cosido
			- Doblez de la tela

Los resultados obtenidos son aproximaciones que pueden ayudar a tomar decisiones sobre la viabilidad de determinado patrón. 

## Simular la prenda sobre un gemelo digital.

Este procedimiento puede llevarse a cabo de diferentes maneras. La que se desarrolla a continuación utiliza un modelo de una persona, con las medidas de quién utilizará la vestimenta, generado en Makehuman y luego importado en Blender. 

Debido a la manera en particular en la que se cose la prenda, la simulación para vestir una figura humana en 3D fuerza a tomar medidas un poco fuera de lo común. Mientras en otras situaciones las partes se pegan o se proyectan sobre un cuerpo y se forma la prenda, en este tipo de prendas realizadas con la misma tela deben tomarse medidas un tanto extremas, como ya se describió antes el complemento "Doblar" ayuda a que las costuras sean posibles. Al coser la remera, esta no debe chocar o cruzarse con objetos mientras se unen las costuras virtuales ya que esto provocaría errores y deformaciones inesperadas. Por tal motivo, si la tela se cose rápido, debido a las características propias del funcionamiento de esa herramienta, y se cruza con partes del cuerpo, surgen los errores. Por lo tanto, se debe recurrir a acciones que procuren evitar que sucedan esos errores, una de ellas, es escalar o aplastar la figura humana mientras la prenda empieza a coserse, para luego mediante una animación simple y cuando la prenda ya esté conformada devolverle su tamaño original para que la caída de la tela pueda ser realizada de manera casi natural.

### Animación del cuerpo.

Se busca escalar o achicar el objeto para que no interfiera mientras suceda el proceso de cosido. Por lo tanto, se utilizarán dos tipos de escala, una en dirección frontal y otra en tamaño general. La animación inicial puede durar 50 frames, o cuadros de la animación.

## Complemento Exportar 

Luego de verificar la viabilidad del patrón por medio de las pruebas realizadas, se puede exportar el patrón en formato "svg", tanto para el estampado, como para la impresión o proyección del patrón.

El complemento desarrollado apunta a crear un archivo que puede contener varias capas de información, las necesarias para la confección, ya sea de manera artesanal o semi industrial, o industrial.

Se selecciona el patrón generado y se aplica la exportación del mismo. Con eso se obtiene un archivo en la carpeta "exports" en el escritorio que contiene el archivo svg con el nombre designado por el usuario.

El archivo svg cuenta con un modelo lineal sin cortes, a escala 1:1, listo para ser impreso, con distintas capas de información para su confección. El complemento sigue en desarrollo, aunque es funcional, posee información redundante y sin ordenar.

# Renderizado.

El proceso de renderizado es el mismo para cualquier proyecto de Blender.

## Blender

Al exportar el modelo de Makehuman, este cuenta la posibilidad de añadir una "armadura", una estructura con los "huesos" o "bones", necesarios para ser utilizados en una animación, que se adhiere al cuerpo humano, haciendo posible el movimiento de las distintas partes del cuerpo, que facilitará una postura para que la prenda pueda animarse y presentarse de distintas maneras.

# Visualizaciòn mediante IA.

Al obtener imágenes desde Blender posibilita por un lado generar datasets de remeras de diseño de residuo cero y por otro generar imágenes mediante inteligencia artificial.

## Visualización de remeras de diseño de residuo cero mediante  imágenes generadas o modificadas por IA.

Para generar o modificar imágenes mediante IA, se recurre a los modelos de IA generativos que sean capaces de utilizar una imagen como base para reinterpretar o dotar a la misma de otros elementos con el objetivo de representar las remeras sin la necesidad de materializarlas, para evitar residuos y promover un tipo de producción bajo demanda, donde la prenda se construye sólo cuando existe una compra asegurada. 

# Estampado | Textura.

Para realizar texturas o estampados sobre la remera, se parte del mismo patrón ya generado, ya que las medidas y las proporciones serán únicas de cada patrón modificado.

El patrón resultante de cada remera puede ser utilizado como base para generar diseños que luego sean estampados, impresos, tajeados mediante láser o proyectados virtualmente sobre la remera.

Inkscape - Importación para diseño vectorial de estampados a medida.
Krita - Diseño de estampado a medida.
The Gimp - Diseño de estampado a medida.

# Exportado.
Inkscape - Importación para impresión, corte láser
Scribus - Impresión del patrón, o información.
Pdf Reader - Impresión
