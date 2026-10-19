# Optimización de rutas logísticas (VRP) con Python y OR-Tools

Proyecto del Trabajo de Fin de Máster en Inteligencia Artificial y Big Data (Digitech).
Resuelve el **Problema de Rutas de Vehículos (VRP)**: decide qué camión visita a qué cliente y en qué orden para repartir los pedidos con el menor coste posible.

## Qué hace

- Usa **Google OR-Tools** como motor de optimización.
- Trabaja con una flota de **4 camiones** que salen y vuelven a un mismo almacén.
- Respeta estas restricciones:
  - **Capacidad** de carga de cada camión.
  - **Jornada máxima de 8 horas**, con una penalización si se pasa de 7.
  - **15 minutos de descarga** en cada cliente.
- Si un cliente no se puede visitar, aplica una multa muy alta para que el sistema lo evite y lo avisa por pantalla.
- Muestra por consola la ruta de cada camión (clientes, carga y tiempo total) y dibuja un **mapa de rutas** con Matplotlib.

## Datos de ejemplo

Los datos exactos del TFM pertenecen a una empresa real y no se publican.
El archivo `datos_ejemplo.json` tiene la misma estructura, pero con datos modificados:

- Los clientes están anonimizados (`Cliente1`, `Cliente2`...).
- Las coordenadas son aproximadas: cada punto está desplazado entre 0,8 y 1,8 km de su ubicación real.
- Las matrices de distancias (metros) y de tiempos (segundos) se han recalculado a partir de esas coordenadas.
- Los volúmenes de los pedidos son valores de ejemplo.

Si quieres usar tus propios datos, crea un JSON con las mismas claves:
`nombres_clientes`, `coordenadas`, `volumen_pedidos`, `matriz_distancias` y `matriz_tiempos`. El almacén es el primer elemento de cada lista.

## Cómo ejecutarlo

Necesitas Python 3.8 o superior.

```bash
# 1. Crear y activar un entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar
python TFM.py
```

La búsqueda tarda unos 45 segundos y al final se abre el mapa de rutas.

## Estructura

| Archivo | Descripción |
|---|---|
| `TFM.py` | Modelo VRP, restricciones, resolución y mapa |
| `datos_ejemplo.json` | Datos de ejemplo (anonimizados) |
| `requirements.txt` | Dependencias |

## Tecnologías

Python · Google OR-Tools · Matplotlib

## Autor

Rubén Alcalde Rodríguez
