import json
import matplotlib.pyplot as plt
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def main():
    #Lectura del archivo .json
    try:
        with open("datos_ejemplo.json", "r", encoding="utf-8") as f:
            datos = json.load(f)
    except FileNotFoundError:
        print("ERROR: No se ha encontrado el archivo .json")
        return

    # DATOS

    #Obtencion de datos del .json
    nombres_clientes = datos.get("nombres_clientes", [])
    coordenadas = datos.get("coordenadas", [])
    distancias = datos.get("matriz_distancias")
    tiempos = datos.get("matriz_tiempos")
    demandas = datos.get("volumen_pedidos")

    #Invertimos lat y lon para que la api lo pueda interpretar
    coordenadas_api = [[c[1], c[0]] for c in coordenadas]

    #Conversor a enteros para proceder al posterior correcto procesado de los datos
    matriz_distancia = [[int(col) for col in fila] for fila in distancias]
    matriz_tiempo = [[int(col) for col in fila] for fila in tiempos]


    #Configuracion de OR-Tools
    num_vehiculos = 4
    manager = pywrapcp.RoutingIndexManager(len(matriz_distancia), num_vehiculos, 0) #Definimos los parametros: Num de puntos totales, num_vehiculos, almacén origen
    routing = pywrapcp.RoutingModel(manager)

    #CALCULAR DISTANCIA
    def calcular_distancia(index_origen, index_destino):
        return matriz_distancia[manager.IndexToNode(index_origen)][manager.IndexToNode(index_destino)]

    transit_dist_index = routing.RegisterTransitCallback(calcular_distancia)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_dist_index)

    #CALCULAR TIEMPO
    def calcular_tiempo(index_origen, index_destino):
        from_node = manager.IndexToNode(index_origen)
        viaje = matriz_tiempo[from_node][manager.IndexToNode(index_destino)]
        return viaje + 900 if from_node != 0 else viaje #Añadimos 15 minutos de descarga

    #CALCULAR CAPACIDAD
    def demanda_callback(from_index):
        node_idx = manager.IndexToNode(from_index)
        return demandas[node_idx]

    demanda_callback_index = routing.RegisterUnaryTransitCallback(demanda_callback)

    #Capacidad: 4.2 (largo) * 2 (ancho) = 8.4m || 8.4 * 3 (alto) = 25.2m = 25200cm
    capacidad_max_cm = 25200
    capacidad_vehiculos = [capacidad_max_cm] * num_vehiculos

    routing.AddDimensionWithVehicleCapacity(
        demanda_callback_index,
        0, #Sin holgura
        capacidad_vehiculos,
        True, #Empieza en 0, y va sumando cm
        "Capacidad"
    )

    dimension_capacidad = routing.GetDimensionOrDie("Capacidad")

    transit_time_index = routing.RegisterTransitCallback(calcular_tiempo)
    tiempo_maximo_h = 8 #Jornada laboral
    tiempo_maximo_s = tiempo_maximo_h * 3600
    tiempo_objetivo_s = 7 * 3600
    #Usamos primero el cálculo de tiempo, slack_max es el tiempo maximo que puede esperar a que abra un cliente sin hacer nada mas,
    # el siguiente parametro es para asegurarnos de que salen en el index 0 (Almacén) y el 4º parametro es para darle un nombre y poder llamarla luego.
    routing.AddDimension(transit_time_index, 600, tiempo_maximo_s, True, "Tiempo")
    dimension_tiempo = routing.GetDimensionOrDie("Tiempo")

    #Penalización de tiempo extra
    #Esto lo que hace es penalizar el tiempo total desde que sale hasta que vuelve
    for v in range(num_vehiculos):
        dimension_tiempo.SetSpanCostCoefficientForVehicle(100, v)
        index_final = routing.End(v)
        dimension_tiempo.SetCumulVarSoftUpperBound(index_final, tiempo_objetivo_s, 100)
        dimension_tiempo.SetSpanCostCoefficientForVehicle(100, v)


    #Multa por saltarse clientes
    for node in range(1,len(matriz_distancia)):
        routing.AddDisjunction([manager.NodeToIndex(node)], 1000000) #Si no va a un cliente porque no puede le metemos una multa de 1M

    #GENERACIÓN DE RUTA ÓPTIMA
    ruta = pywrapcp.DefaultRoutingSearchParameters() #Cargar la ruta con un lienzo estándar para poder modificarlo
    ruta.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC) #Aquí dictamos que primero siga una ruta que vaya al cliente más cercano para poder empezar a trabajar
    ruta.time_limit.seconds = 45 #El tiempo de ejecución en segundos de búsqueda de ruta, pasado este tiempo te da lo mejor que haya encontrado

    solucion = routing.SolveWithParameters(ruta) #Verifica que nadie pase el tiempo o las condiciones dadas anteriormente

    # Comprobación y aviso de clientes no visitados
    clientes_visitados = []
    for vehiculo in range(num_vehiculos):
        index = routing.Start(vehiculo)
        while not routing.IsEnd(index):
            node_idx = manager.IndexToNode(index)
            if node_idx != 0:  # Apartamos el almacén
                clientes_visitados.append(node_idx)
            index = solucion.Value(routing.NextVar(index))
    if len(clientes_visitados) < len(nombres_clientes) - 1:
        print("NO SE HAN PODIDO VISITAR TODOS LOS CLIENTES")
        for i in range(1, len(nombres_clientes)):
            if i not in clientes_visitados:
                print(f"NO VISITADO: {nombres_clientes[i]}")
    else:
        print("Se han visitado todos los clientes correctamente")

    if solucion:

        print("Rutas calculadas correctamente")
        plt.figure(figsize=(14, 12))
        colores = ['#e6194b', '#3cb44b', '#4363d8', "#f58231"]  # Rojo, Verde, Azul, Naranja

        lon = [c[0] for c in coordenadas_api]
        lat = [c[1] for c in coordenadas_api]

        plt.scatter(lon[1:], lat[1:], c='gray', s=50, alpha=0.7, label='Clientes')
        plt.scatter(lon[0], lat[0], c='yellow', s=250, edgecolors='black', marker='*', label='(Origen)', zorder=5)

        for id_vehiculo in range(num_vehiculos):
            index = routing.Start(id_vehiculo)          #punto de inicio
            x_ruta, y_ruta = [], []                     #una libreta para que vaya escribiendo por donde va
            print("------------------------------------------")
            print(f"CAMION {id_vehiculo + 1}")
            while not routing.IsEnd(index):             #El programa va saltando de cliente en cliente hasta llegar al final de la ruta (almacén)
                node_idx = manager.IndexToNode(index)   #Número de cliente
                x_ruta.append(coordenadas_api[node_idx][0])      #Escribe las coordenadas en la libreta
                y_ruta.append(coordenadas_api[node_idx][1])

                #Carga del camion que ya traía procesada de clientes anteriores
                carga_anterior = solucion.Value(dimension_capacidad.CumulVar(index))

                #Carga específica de este cliente (si es almacén es 0)
                carga_este_pedido = demandas[node_idx] if node_idx != 0 else 0

                #Carga total ya gestionada con este cliente incluido
                carga_total = carga_anterior + carga_este_pedido

                nombre = nombres_clientes[node_idx] if node_idx < len(nombres_clientes) else f"Punto {node_idx}"    #Vinculamos los nodos a sus nombres

                #Si es cliente
                if node_idx != 0:
                    print(f"--> {nombre}")
                    print(f"     [+] Pedido de este cliente: {carga_este_pedido} cm")
                    print(f"     [=] Total transportado/entregado en esta ruta: {carga_total} cm")
                else:
                    # Si es el almacén, simplemente avisamos que es la salida
                    print(f"--> {nombre} (Salida del Almacén con el camión cargado)")

                index = solucion.Value(routing.NextVar(index))  #Esto es como si hemos llegado a un cliente y tenemos que ir al siguiente, reemplazamos index por el siguiente cliente
            print("------------------------------------------")

            #Una vez el camión acabe la ruta volvemos al almacén
            x_ruta.append(coordenadas_api[0][0])
            y_ruta.append(coordenadas_api[0][1])

            #Comprobamos el tiempo que ha tardado en hacer la ruta
            index_final = routing.End(id_vehiculo)
            tiempo_gastado_s = solucion.Min(dimension_tiempo.CumulVar(index_final))
            print(f"Tiempo invertido: {tiempo_gastado_s // 3600} horas, {(tiempo_gastado_s % 3600) // 60} minutos.")

            #Por último dibujamos en el gráfico la ruta que haya seguido nuestro camión
            plt.plot(x_ruta, y_ruta, color=colores[id_vehiculo], linewidth=2, marker= "o", markersize=4, label=f"Ruta {id_vehiculo + 1}", alpha=0.8)

        plt.title("MAPA DE DISTRIBUCIÓN LOGÍSTICA - TFM", fontsize=16)
        plt.xlabel("Longitud", fontsize=12)
        plt.ylabel("Latitud", fontsize=12)
        plt.legend(loc='lower right')
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.show()
    else:
        print("ERROR: Dados los parámetros actuales no se ha podido encontrar ninguna solución concluyente. Ajuste el tiempo, numero de camiones o numero de pedidos.")

if __name__ == "__main__":
    main()