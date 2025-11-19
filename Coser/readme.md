# Coser – Addon para Blender

Coser es un complemento diseñado para unir digitalmente las partes del patrón de una prenda de diseño de residuo cero directamente en Blender. Permite coser vértices en serie de manera simple, controlada y sin intervención manual compleja.

* * *

## Características principales

*   Cose dos series de vértices seleccionados.
    
*   Dos modos de orientación:
    
    *   Direccional: ABCD → ABCD
        
    *   Invertido: ABCD → DCBA
        
*   Ideal para patrones Zero Waste que requieren costuras sobre la misma pieza de tela.
    
*   Interfaz minimalista desde el panel lateral (N-Panel).
    
*   Emparejamiento automático de vértices.
    
*   Totalmente no destructivo: no altera la topología fuera de las aristas creadas.
    

* * *

## Requisitos

*   Blender 3.6
    
*   Un objeto tipo Mesh con un patrón generado previamente (por ejemplo con Patronaje + Relleno/fill)
    

* * *

## Instalación

1.  Abrir Blender
    
2.  Ir a Edit > Preferences > Add-ons
    
3.  Seleccionar Install…
    
4.  Elegir el archivo .py de este addon
    
5.  Activarlo desde la lista de Add-ons
    
6.  Abrir el N-Panel → Coser
    

* * *

## Uso

1.  Seleccionar dos series de vértices en modo Edición.
    
2.  Elegir el modo de costura:
    
    *   Mismo orden
        
    *   Orden invertido
        
3.  Ejecutar el operador "Coser".
    
4.  Blender generará las aristas correspondientes emparejando cada vértice de la primera serie con el correspondiente de la segunda.
    

* * *

## Flujo de trabajo recomendado

El addon forma parte de una cadena de herramientas:

*   Patronaje (crear patrón)
    
*   Relleno (malla simulable)
    
*   Coser (este addon)
    
*   Doblar (marcado de pliegues no destructivos)
    
*   Exportar SVG (patrón final para impresión o corte)
    

* * *

## Cambios recientes

Ver la sección “Changelog”.

* * *

## Licencia

GPL-3.0 license
Open Source. Puede modificarse y adaptarse a cualquier proyecto
