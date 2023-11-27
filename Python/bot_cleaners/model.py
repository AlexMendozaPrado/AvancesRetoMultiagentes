from mesa.model import Model
from mesa.agent import Agent
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
from collections import deque
import math
import random



import numpy as np
from queue import PriorityQueue
class Celda(Agent):
    def __init__(self, unique_id, model, sucia=False):
        super().__init__(unique_id, model)
        self.sucia = sucia

class Caja(Agent):
    def __init__(self,unique_id,model, estante_id = None, peso = 1, id_entrega = None):
        super().__init__(unique_id,model)
        self.pos = None
        self.sig_pos = None
        self.estante_id = estante_id
        self.peso = peso
        self.id_entrega = id_entrega


class Estante(Agent):
    def __init__(self,unique_id,model, pos = None):
        super().__init__(unique_id,model)
        self.pos = pos
        self.cantidad_cajas = 0
        self.cajas = []

        #TODO: pop caja cuando la recogen

class Banda(Agent):
    def __init__(self,unique_id,model):
        super().__init__(unique_id,model)
        self.tiene_caja = False
        self.caja_recoger = None

    def step(self):
        if not self.tiene_caja:
            nueva_caja = self.model.crear_caja()
            if nueva_caja:
                self.model.poner_caja(self.pos, nueva_caja)
                nueva_caja.pos = self.pos
                self.tiene_caja = True
                self.caja_recoger = nueva_caja

class BandaEntrega(Agent):
    def __init__(self, unique_id: int, model: Model) -> None:
        super().__init__(unique_id, model)
        self.cantidad_cajas = 0

        

class EstacionCarga(Agent):
      def __init__(self, unique_id, model):
          super().__init__(unique_id, model)
          self.reservada = False  # Añadir esta línea para el estado de reserva
          self.robot_reservante = None


      def reservar(self, robot):
            self.reservada = True
            self.robot_reservante = robot

      def liberar(self):
        self.reservada = False
        self.robot_reservante = None


class Mueble(Agent):
      def __init__(self, unique_id, model):
          super().__init__(unique_id, model)


class RobotLimpieza(Agent):
        TIEMPO_ESPERA = 5  # Definir un tiempo de espera
        LIMITE_REPLANIFICACIONES = 100  # Definir un límite de replanificaciones
        def __init__(self, unique_id, model, banda_id = None, estacion_carga = None):
            super().__init__(unique_id, model)
            self.banda_id = banda_id
            self.sig_pos = None
            self.contador_espera = 0  # Inicializar el contador de espera
            self.movimientos = 0
            self.carga = 100
            self.umbral_bateria = 20  # Ejemplo de umbral de batería
            self.ruta_planeada = []  # Añadir para guardar la ruta planeada
            self.estacion_carga = None  # Añadir para ubicar la estación de carga
            self.necesita_cargar = True  # Or some initial value based on your logic
            self.contador_replanificaciones = 0  # Inicializar el contador de replanificaciones
            self.estacion_carga_propia = estacion_carga
            self.estaciones_carga_reservadas = [] # Añadir para almacenar las estaciones reservadas
            self.tiene_caja = False
            self.caja_cargando = None
            self.estacion_reservada = None
            self.pos_estantes_recojer = []
            self.dejando_caja = False
            self.all_robots_cargadores = False
            self.pos_estante_recogida = None
            self.caja_estante_recogida = None

        def limpiar_celda_actual(self):
            contenido_celda_actual = self.model.grid.get_cell_list_contents(self.pos)
            for obj in contenido_celda_actual:
                if isinstance(obj, Celda) and obj.sucia:
                    obj.sucia = False  # Cambiar el estado de la celda a "limpia"
                    break  # Suponiendo que solo hay una celda en la posición

        def step(self):
            # Si el robot está cargando, incrementar la batería
            if self.estoy_cargando() == True:
                self.carga = min(100, self.carga + 25)  # Suponiendo que se carga un 25% por step
                return  # No hacer más acciones si está cargando

            # if self.unique_id == 20 and self.tiene_caja:
            #     print("Robot ", self.unique_id, " se dirige a la posicion ", self.ruta_planeada)
            #     print(self.caja_cargando.pos)
            #     print(self.caja_cargando.estante_id)
            #     for estante in self.model.estantes:
            #         if estante.unique_id == self.caja_cargando.estante_id:
            #             punto_estante_entrega = (estante.pos[0], estante.pos[1] + 1)
            #             print(estante.pos)
            #             self.ruta_planeada = self.algoritmo_a_estrella(self.pos, punto_estante_entrega)       
            #             break

            if self.carga < self.umbral_bateria: 
                self.necesita_cargar = True 
                estacion_cercana = self.encontrar_estacion_carga_mas_cercana()
                if estacion_cercana:
                    self.reservar_estacion_carga(estacion_cercana)
                    self.ruta_planeada = self.algoritmo_a_estrella(self.pos, estacion_cercana.pos)
                    print(self.ruta_planeada)  # Imprime la ruta planeada

            if self.verificar_cargadores():
                self.all_robots_cargadores = True

            if not self.dejando_caja:
                self.checar_empezar_recoleccion()

            if self.dejando_caja and self.all_robots_cargadores and not self.ruta_planeada and not self.tiene_caja:
                    if not self.pos_estantes_recojer:
                        self.dejando_caja = False
                        return
                    estante = self.pos_estantes_recojer.pop(0) 
                    pos_estante = estante[0]
                    ruta_estante = self.algoritmo_a_estrella(self.pos, pos_estante)
                    caja = estante[1]
                    banda_entrega = self.obtener_banda_entrega(caja.id_entrega)
                    pos_banda = banda_entrega.pos
                    destino_banda = (pos_banda[0], pos_banda[1] + 1)
                    #ruta_banda_entrega = self.algoritmo_a_estrella(pos_estante, destino_banda)
                    
                    self.ruta_planeada = ruta_estante
                    self.pos_estante_recogida = pos_estante
                    self.caja_estante_recogida = caja
                    return

            # Planificar ruta hacia celda sucia si no hay ruta planeada
            if not self.ruta_planeada:
                if not self.tiene_caja: 
                    if not self.puede_hacer_el_recorrido():
                        self.ruta_planeada = self.algoritmo_a_estrella(self.pos, self.estacion_carga_propia.pos)
                        return
                    
                    if not self.dejando_caja:
                        for banda in self.model.bandas:
                            if banda.unique_id == self.banda_id:
                                # Cambia banda.pos en y-1
                                punto_recoleccion = (banda.pos[0], banda.pos[1] - 1)
                                ##Verificar si robot tiene bateri disponible para ir por 
                                self.ruta_planeada = self.algoritmo_a_estrella(self.pos, punto_recoleccion)
                                break

                        # TODO: Robot en estación de recolección recoge la caja
                        # Si el robot es vecino de la caja con su ID, cambia la posicion de la caja a la misma posicion del robot
                        for caja in self.model.cajas:
                            if self.son_vecinos_ortogonales(caja):
                                caja.pos = self.pos
                                self.tiene_caja = True
                                self.caja_cargando = caja
                                for banda in self.model.bandas:
                                    if banda.unique_id == self.banda_id:
                                        banda.tiene_caja = False
                                        banda.caja_recoger = None
                                        self.model.cajas.remove(caja)
                                        break


                else: # tiene caja, la deja en el estante y regresa a su banda
                    if not self.dejando_caja:
                        id_estante = self.caja_cargando.estante_id
                        for estante in self.model.estantes:
                            if estante.unique_id == id_estante:
                                punto_estante_entrega = (estante.pos[0], estante.pos[1] + 1)
                                self.ruta_planeada = self.algoritmo_a_estrella(self.pos, punto_estante_entrega)
                            if self.son_vecinos_ortogonales(estante):
                                if not self.dejando_caja:
                                    estante.cajas.append(self.caja_cargando)
                                    self.pos_estantes_recojer.append((self.pos, self.caja_cargando))
                                    estante.cantidad_cajas += 1
                                    
                                    self.tiene_caja = False
                                    self.caja_cargando = None
                    else:
                        banda_entrega = self.obtener_banda_entrega(self.caja_cargando.id_entrega)
                        if self.son_vecinos_ortogonales(banda_entrega):
                            self.tiene_caja = False
                            self.caja_cargando = None
                            banda_entrega.cantidad_cajas += 1
                            return

                # TODO: Robot entrega la caja en el estante
                #si tiene batteria para ir por la caja, dejarla, y luego cargarse, ir por la caja, si no cargarse
                # self.comunicar_ruta()
                self.contador_replanificaciones = 0

                # total_colisiones[i][0] = robot con el que colisiono
                # total_colisiones[i][1] = indice donde colisiono
                # total_colisiones[i][2] = lugar donde colisiono
                total_colisiones = self.obtener_colisiones()

                # No se cumple ninguna de las sigueientes condiciones cuando no hay colisiones
                if len(total_colisiones) == 1:
                    # la nueva ruta provoca una colision, se puede negociar con el otro robot que provoca colision
                    replanificar_robot = self.negociar(total_colisiones[0][0])
                    if replanificar_robot != self:
                        total_colisiones[0][0] = self # colision desde el punto de vista del otro robot
                    replanificar_robot.planificar_nueva_ruta(total_colisiones)
                elif len(total_colisiones) > 1:
                    # la nueva ruta provoca mas de una colision, no se puede negociar, el robot debe ajustarse a las demas rutas
                    self.planificar_nueva_ruta(total_colisiones)

            else:
                if self.tiene_caja:
                    if not self.dejando_caja:
                        for estante in self.model.estantes:
                            if (estante == self.caja_cargando.estante_id and self.son_vecinos_ortogonales(estante)):
                                caja.pos = estante.pos
                                self.tiene_caja = False
                                self.caja_cargando = None
                                estante.cantidad_cajas += 1
                                estante.cajas.append(caja)
                                self.ruta_planeada = self.algoritmo_a_estrella(self.pos, self.estacion_reservada.pos)
                                break
                    else:
                        banda_entrega = self.obtener_banda_entrega(self.caja_cargando.id_entrega)
                        if self.son_vecinos_ortogonales(banda_entrega):
                            self.tiene_caja = False
                            self.caja_cargando = None
                            #aumentarle una caja a la banda de entrega
                            return
                else:
                    if self.dejando_caja and self.caja_estante_recogida:
                        estante = self.obtener_estante(self.caja_estante_recogida)
                        if self.son_vecinos_ortogonales(estante) and self.caja_estante_recogida in estante.cajas:
                            estante.cantidad_cajas -= 1
                            estante.cajas.remove(self.caja_estante_recogida)
                            self.caja_cargando = self.caja_estante_recogida
                            self.tiene_caja = True
                            banda_entrega = self.obtener_banda_entrega(self.caja_cargando.id_entrega)
                            pos_banda = banda_entrega.pos
                            destino_banda = (pos_banda[0], pos_banda[1] + 1)
                            self.ruta_planeada = self.algoritmo_a_estrella(self.pos, destino_banda)
                            return

                        

            # Verificar nivel de batería y planificar ruta hacia estación de carga si es necesario

            # Mover el robot a lo largo de la ruta planeada
            self.mover_a_siguiente_posicion_en_ruta()
            # self.limpiar_celda_actual()  # Limpia la celda si es necesario
            # Comunicar ruta y resolver conflictos (aunque en tu caso no se comuniquen)
            # Suponiendo que tienes una función para comunicar la ruta planeada
            # self.actualizar_ruta()
            # self.resolver_deadlocks()

        def obtener_banda_entrega(self, id_banda_entrega):
            for banda in self.model.bandas_entrega:
                if banda.unique_id == id_banda_entrega:
                    return banda
            return None

        def verificar_cargadores(self):
            for robot in self.model.schedule.agents:
                if isinstance(robot, RobotLimpieza):
                    if robot.pos != robot.estacion_carga_propia.pos or robot.carga != 100:
                        self.all_robots_cargadores = False
                        return False
            self.all_robots_cargadores = True
            return True

        def checar_empezar_recoleccion(self):
            cantidad_cajas = 0
            for estante in self.model.estantes:
                cantidad_cajas += estante.cantidad_cajas
            self.dejando_caja = cantidad_cajas == self.model.cajas_creadas

        def puede_hacer_el_recorrido(self):
            caja = self.obtener_caja()
            if not caja:
                return False
            banda = self.obtener_banda()

            punto_banda = (banda.pos[0], banda.pos[1] - 1)
            ruta_hacia_banda = self.algoritmo_a_estrella(self.pos, punto_banda)
            estante = self.obtener_estante(caja)
            punto_estante_entrega = (estante.pos[0], estante.pos[1] + 1)
            ruta_banda_estante = self.algoritmo_a_estrella(punto_banda, punto_estante_entrega)
            ruta_estante_cargador = self.algoritmo_a_estrella(punto_estante_entrega, self.estacion_carga_propia.pos)

            costo_total = len(ruta_hacia_banda) + (len(ruta_banda_estante) * caja.peso) + len(ruta_estante_cargador)
            if costo_total > self.carga:
                return False
            print("Robot ", self.unique_id, " puede hacer el recorrido ", costo_total, " bateria disponible ", self.carga)
            return True

        def obtener_banda(self):
            for banda in self.model.bandas:
                if banda.unique_id == self.banda_id:
                    return banda
            return None

        def obtener_caja(self):
            for banda in self.model.bandas:
                if banda.unique_id == self.banda_id:
                    return banda.caja_recoger
            return None
        

        def obtener_estante(self, caja):
            for estante in self.model.estantes:
                if estante.unique_id == caja.estante_id:
                    return estante
            return None
        
        #codigo de copilot que igual y jala
        def resolver_deadlocks(self):
            # Ejemplo de detección de deadlock
            if self.contador_espera >= RobotLimpieza.TIEMPO_ESPERA:
                # Lógica para resolver deadlock
                self.contador_espera = 0
                self.replanificar_ruta()
            else:
                # Continúa esperando
                pass

        def son_vecinos_ortogonales(self, agente2):
            """
            Determina si dos agentes son vecinos en una cuadrícula.

            :param self: El primer agente.
            :param agente2: El segundo agente.
            :return: True si los agentes son vecinos, False en caso contrario.
            """
            # Obtener las posiciones de los agentes
            x1, y1 = self.pos
            """
            print("============================")
            print("============================")
            print(agente2.pos)
            print("============================")
            print("============================")
            """
            
            x2, y2 = agente2.pos

            # Calcular la diferencia absoluta en las coordenadas x e y
            diff_x = abs(x1 - x2)
            diff_y = abs(y1 - y2)

            # Los agentes son vecinos si están en celdas adyacentes ortogonalmente
            return diff_x + diff_y == 1
        

        def verificar_ruta(self):
            for pos in self.ruta_planeada:
                if not (0 <= pos[0] < self.model.grid.width and
                        0 <= pos[1] < self.model.grid.height):
                    print(f"Posición inválida en la ruta: {pos}")

        def estoy_cargando(self):
            # Comprueba si el robot está en la misma posición que alguna estación de carga
            contenido_celda_actual = self.model.grid.get_cell_list_contents(self.pos)
            # Create a list of coordinates from the objects in the current cell
            coordenadas_celda_actual = [obj.pos for obj in contenido_celda_actual]
            
            
            # Imprimir todos los objetos en la celda actual
            
            # Comprobar si hay una instancia de EstacionCarga en la celda
            en_estacion_carga = any(isinstance(obj, EstacionCarga) for obj in contenido_celda_actual)
            
            # Comprobar si hay una instancia de EstacionCarga en la celda
            # if en_estacion_carga:
            #     print(f"Robot {self.unique_id} ha encontrado una estación de carga en la celda {self.pos}")
            
            
            # Retorna True si está en una estación de carga
            return en_estacion_carga and self.carga < 100
        
 
        def comunicar_ruta(self):
             # Enviar información de ruta a otros robots
            for robot in self.model.schedule.agents:
                if robot != self and isinstance(robot, RobotLimpieza):
                    # No incluir la estación reservada en la ruta comunicada
                    robot.recibir_ruta(self.ruta_planeada, self)
                

        def recibir_ruta(self, ruta_otro_robot, otro_robot):
            # Detectar colisión y negociar una nueva ruta si es necesario
            # colision[0]: indica si hubo colision o no
            # colision[1]: indice donde ocurre la colision
            # colision[2]: lugar donde ocurre la colision
            colision = self.detectar_colision(ruta_otro_robot)
            # Extraer coordenadas donde ocurre colision
            if colision[0]:
               print("=======================================")
               print("COLISION DETECTADA ENTRE EL ROBOT", self.unique_id, "y", otro_robot.unique_id, "en los lugares", self.ruta_planeada[colision[1]], "y", otro_robot.ruta_planeada[colision[1]])
               print("=======================================")
               # Mandar a esta funcion coordenadas donde ocurre la colision
               self.resolver_conflicto(otro_robot, colision)
            # Comprobar si la ruta recibida incluye la estación de carga que este robot ha reservado
            elif any(estacion for estacion in self.model.estaciones_carga if estacion.pos in ruta_otro_robot and estacion.reservada and estacion.robot_reservante == self):
                self.resolver_conflicto(otro_robot)  # Considerar esto como un conflicto y replanificar la ruta

        def negociar(self, otro_robot):
            
            """
            if self.estacion_reservada and self.estacion_reservada.reservada and self.estacion_reservada.robot_reservante != self:
                # Si la estación de carga está reservada por otro robot, replanificar sin incrementar el contador
                self.replanificar_ruta()
                return  # Finalizar el método aquí para evitar incrementar el contador de replanificaciones
            if self.contador_replanificaciones < self.LIMITE_REPLANIFICACIONES:
                # Lógica actual para ceder o replanificar
                if self.debe_ceder(otro_robot):
                    self.replanificar_ruta()
                else:
                    otro_robot.replanificar_ruta()
                self.contador_replanificaciones += 1
            else:
                # Acción alternativa: esperar o cambiar ruta
                self.esperar_o_cambiar_ruta()
                self.contador_replanificaciones = 0
            """

            """
            REGLAS DE NEGOCIACION

            1. Un robot va a su estacion de carga, el otro no:
               1.1. Si el otro robot no va a su estacion de carga ni tiene caja se le cede el paso al robot que va a su estacion de carga
                1.2. Si el otro robot tiene una caja se le cede el paso a ese robot
                1.3. Ambos robots van a sus estaciones de carga:
                    1.3.1. Se le cede el paso  al robot que tenga menos bateria
                    1.3.2. Si ambos robots tienen la misma bateria:
                        1.3.2.1. Se le cede el paso al robot que tenga mas replanificaciones
                        1.3.2.2. Si ambos tienen la misma cantidad de replanificaciones se le cede el paso al robot con el menor id

            2. Ambos robots cargan una caja:
                2.1. Se le cede el paso al robot con la caja mas pesada
                2.2. Ambos robots tienen una caja del mismo peso:
                    2.2.1. Se le cede el paso al robot que tenga menos bateria
                    2.2.2. Si ambos robots tienen la misma bateria:
                        2.2.2.1. Se le cede el paso al robot que tenga mas replanificaciones
                        2.2.2.2. Si ambos tienen la misma cantidad de replanificaciones se le cede el paso al robot con el menor id

            3. Uno de los robots esta desocupado:
                3.1. Si el otro robot esta cargando una caja se le cede el paso a ese robot
                3.2. Si el otro robot no esta ocupado ni necesita ir a su estacion de carga se le cede el paso al que tenga menos bateria
                3.3. Si ambos tienen la misma bateria:
                    3.3.1. Se le cede el paso al robot con menos bateria
                    3.3.2. Si ambos robots tienen la misma bateria:
                        3.3.2.1. Se le cede el paso al robot que tenga mas replanificaciones
                        3.3.2.2. Si ambos tienen la misma cantidad de replanificaciones se le cede el paso al robot con el menor id

            NOTA IMPORTANTE: AL FINALIZAR LA MODIFICACION DE LA RUTA DE UN ROBOT VOLVER A LLAMAR LA FUNCION self.comunicar_ruta()

            CASOS EXTREMOS NO RESUELTOS:

            2 robots en camino a la misma estacion de carga y el punto de colision es justo enfrente de la banda de tal modo que uno
            queda enfrente de la banda y otro queda atras porque se freno para no colisionar. Despues de que el robot de la banda
            recoge su caja no puede moverse porque el robot de atras esta ocupando su espacio y ese robot necesita recoger una caja
            de la banda. En este caso no funciona el frenado de uno de los 2 robots, se necesita replanificar las rutas de ambos 
            ignorando las posiciones ocupadas del mapa.

            
            Hay 2 robots:
            * 1. Esta en cualquier estado (cargando, yendo a recoger una caja o yendo a su estacion de carga)
            * 2. Esta yendo a recoger una caja o cargando una caja
            Si el robot 2 tiene prioridad el robot 1 debe ceder el paso. En algunos casos es suficiente que el robot que cede solo
            espere 1 step parado pero en otros es necesario que espere 2 steps porque si el camino del robot 1 se atraviesa con el
            camino del robot 2 puede suceder que el robot 2 tenga que dejar una caja, en ese caso el robot 1 debe esperar a que el 2
            vaya a su posicion (acaba de ceder para evitar colision) y que en el siguiente step el robot 2 deje la caja (el robot 1
            volvio a ceder para no chocar con el robot 1).

            Una posible explicacion es que cuando un robot recoge/deja una caja despues de recogerla/dejarla replanifica su nueva
            ruta en el mismo step y en el siguiente la nueva ruta incluye ese espacio donde recogio/dejo la caja. Falta experimentar
            si eso sucede solo al momento de dejar una caja o tambien al recogerla y si se debe a la funcion de resolver_conflicto
            o no.

            Al recoger una caja solo llega al lugar, recoge y se mueve, pero al dejar una caja llega al lugar, deja la caja y a veces
            se mueve pero otras veces despues de dejar la caja se queda quieta en su posicion otro step y luego se mueve. En teoria
            solo deberia llegar al lugar, dejar la caja y luego moverse no esperar en el mismo lugar otro step despues de dejar la
            caja.
            """
            
            # 1
            if ((self.ruta_planeada[-1] == self.estacion_carga_propia.pos and otro_robot.ruta_planeada[-1] != otro_robot.estacion_carga_propia.pos) or (self.ruta_planeada[-1] != self.estacion_carga_propia.pos and otro_robot.ruta_planeada[-1] == otro_robot.estacion_carga_propia.pos)):
                # 1.1
                if ((self.ruta_planeada[-1] == self.estacion_carga_propia.pos) and (otro_robot.ruta_planeada[-1] != otro_robot.estacion_carga_propia.pos) and (otro_robot.tiene_caja == False)):
                    # Debe ceder el otro robot (esta desocupado)
                    print("==========================================")
                    print("COLISION EN EL CASO 1.1")
                    print("==========================================")
                    return otro_robot
                elif ((otro_robot.ruta_planeada[-1] == otro_robot.estacion_carga_propia.pos) and (self.ruta_planeada[-1] != self.estacion_carga_propia.pos) and (self.tiene_caja == False)):
                    # Debe ceder el robot actual (esta desocupado)
                    print("==========================================")
                    print("COLISION EN EL CASO 1.1")
                    print("==========================================")
                    return self
                
                # 1.2
                if ((self.ruta_planeada[-1] == self.estacion_carga_propia.pos) and (otro_robot.ruta_planeada[-1] != otro_robot.estacion_carga_propia.pos) and (otro_robot.tiene_caja == True)):
                    # Debe ceder el robot actual porque el otro tiene caja
                    print("==========================================")
                    print("COLISION EN EL CASO 1.2")
                    print("==========================================")
                    return self
                elif((otro_robot.ruta_planeada[-1] == otro_robot.estacion_carga_propia.pos) and (self.ruta_planeada[-1] != self.estacion_carga_propia.pos) and (self.tiene_caja == True)):
                    # Debe ceder el otro robot porque el actual tiene caja
                    print("==========================================")
                    print("COLISION EN EL CASO 1.2")
                    print("==========================================")
                    return otro_robot
                
                # 1.3
                if ((self.ruta_planeada[-1] == self.estacion_carga_propia.pos) and (otro_robot.ruta_planeada[-1] == otro_robot.estacion_carga_propia.pos)):
                    # 1.3.1
                    if (self.carga < otro_robot.carga):
                        # Debe ceder el otro robot porque el actual tiene menos bateria
                        print("==========================================")
                        print("COLISION EN EL CASO 1.3.1")
                        print("==========================================")
                        return otro_robot
                    elif (self.carga > otro_robot.carga):
                        # Debe ceder el robot actual porque el otro tiene menos bateria
                        print("==========================================")
                        print("COLISION EN EL CASO 1.3.1")
                        print("==========================================")
                        return self

                    # 1.3.2
                    if (self.carga == otro_robot.carga):
                        # 1.3.2.1
                        if (self.contador_replanificaciones < otro_robot.contador_replanificaciones):
                            # Debe ceder el robot actual porque el otro tiene mas replanificaciones
                            print("==========================================")
                            print("COLISION EN EL CASO 1.3.2")
                            print("==========================================")
                            return self
                        elif (self.contador_replanificaciones > otro_robot.contador_replanificaciones):
                            # Debe ceder el otro robot porque el actual tiene mas replanificaciones
                            print("==========================================")
                            print("COLISION EN EL CASO 1.3.2")
                            print("==========================================")
                            return otro_robot
                        
                        # 1.3.2.2
                        if (self.contador_replanificaciones == otro_robot.contador_replanificaciones):
                            if (self.unique_id < otro_robot.unique_id):
                                # Debe ceder el otro robot porque tiene el id mas grande
                                print("==========================================")
                                print("COLISION EN EL CASO 1.3.2.2")
                                print("==========================================")
                                return otro_robot
                            else:
                                # Debe ceder el robot actual porque tiene el id mas grande
                                print("==========================================")
                                print("COLISION EN EL CASO 1.3.2.2")
                                print("==========================================")
                                return self

            # 2
            if ((self.tiene_caja == True) and (otro_robot.tiene_caja == True)):
                # 2.1
                if (self.caja_cargando.peso > otro_robot.caja_cargando.peso):
                    # Debe ceder el otro robot porque el actual tiene la caja mas pesada
                    print("==========================================")
                    print("COLISION EN EL CASO 2.1")
                    print("==========================================")
                    return otro_robot
                elif (self.caja_cargando.peso < otro_robot.caja_cargando.peso):
                    # Debe ceder el robot actual porque el otro tiene la caja mas pesada
                    print("==========================================")
                    print("COLISION EN EL CASO 2.1")
                    print("==========================================")
                    return self
                
                # 2.2
                if (self.caja_cargando.peso == otro_robot.caja_cargando.peso):

                    # 2.2.1
                    if (self.carga < otro_robot.carga):
                        # Debe ceder el otro robot porque el actual tiene menos bateria
                        print("==========================================")
                        print("COLISION EN EL CASO 2.2.1")
                        print("==========================================")
                        return otro_robot
                    elif (self.carga > otro_robot.carga):
                        # Debe ceder el robot actual porque el otro tiene menos bateria
                        print("==========================================")
                        print("COLISION EN EL CASO 2.2.1")
                        print("==========================================")
                        return self
                    
                    # 2.2.2
                    if (self.carga == otro_robot.carga):
                        # 2.2.2.1
                        if (self.contador_replanificaciones < otro_robot.contador_replanificaciones):
                            # Debe ceder el robot actual porque el otro tiene mas replanificaciones
                            print("==========================================")
                            print("COLISION EN EL CASO 2.2.2.1")
                            print("==========================================")
                            return self
                        elif (self.contador_replanificaciones > otro_robot.contador_replanificaciones):
                            # Debe ceder el otro robot porque el actual tiene mas replanificaciones
                            print("==========================================")
                            print("COLISION EN EL CASO 2.2.2.1")
                            print("==========================================")
                            return otro_robot
                        
                        # 2.2.2.2
                        if (self.contador_replanificaciones == otro_robot.contador_replanificaciones):
                            if (self.unique_id < otro_robot.unique_id):
                                # Debe ceder el otro robot porque tiene el id mas grande
                                print("==========================================")
                                print("COLISION EN EL CASO 2.2.2.2")
                                print("==========================================")
                                return otro_robot
                            else:
                                # Debe ceder el robot actual porque tiene el id mas grande
                                print("==========================================")
                                print("COLISION EN EL CASO 2.2.2.2")
                                print("==========================================")
                                return self

            # 3
            if ((self.ruta_planeada[-1] != self.estacion_carga_propia.pos and self.tiene_caja == False) or (otro_robot.ruta_planeada[-1] != otro_robot.estacion_carga_propia.pos and otro_robot.tiene_caja == False)):
                # 3.1
                if (self.tiene_caja == True and otro_robot.tiene_caja == False):
                    # Debe ceder el otro robot porque el actual esta cargando una caja
                    print("==========================================")
                    print("COLISION EN EL CASO 3.1")
                    print("==========================================")
                    return otro_robot
                elif(self.tiene_caja == False and otro_robot.tiene_caja == True):
                    # Debe ceder el robot actual porque el otro esta cargando una caja
                    print("==========================================")
                    print("COLISION EN EL CASO 3.1")
                    print("==========================================")
                    return self

                # 3.2
                if (self.tiene_caja == False and otro_robot.tiene_caja == False):
                    if (self.carga < otro_robot.carga):
                        # Debe ceder el otro robot porque el actual tiene menos bateria
                        print("==========================================")
                        print("COLISION EN EL CASO 3.2")
                        print("==========================================")
                        return otro_robot
                    elif (self.carga > otro_robot.carga):
                        # Debe ceder el robot actual porque el otro tiene menos bateria
                        print("==========================================")
                        print("COLISION EN EL CASO 3.2")
                        print("==========================================")
                        return self

                    # 3.3
                    if (self.carga == otro_robot.carga):
                        # 3.3.1
                        if (self.contador_replanificaciones < otro_robot.contador_replanificaciones):
                            # Debe ceder el robot actual porque el otro tiene mas replanificaciones
                            print("==========================================")
                            print("COLISION EN EL CASO 3.3.1")
                            print("==========================================")
                            return self
                        elif (self.contador_replanificaciones > otro_robot.contador_replanificaciones):
                            # Debe ceder el otro robot porque el actual tiene mas replanificaciones
                            print("==========================================")
                            print("COLISION EN EL CASO 3.3.1")
                            print("==========================================")
                            return otro_robot
                        
                        # 3.3.2
                        if (self.contador_replanificaciones == otro_robot.contador_replanificaciones):
                            if (self.unique_id < otro_robot.unique_id):
                                # Debe ceder el otro robot porque tiene el id mas grande
                                print("==========================================")
                                print("COLISION EN EL CASO 3.3.2")
                                print("==========================================")
                                return otro_robot
                            else:
                                # Debe ceder el robot actual porque tiene el id mas grande
                                print("==========================================")
                                print("COLISION EN EL CASO 3.3.2")
                                print("==========================================")
                                return self    

        def esperar_o_cambiar_ruta(self):
            # Ejemplo: el robot podría esperar un tiempo antes de replanificar
            self.esperar()
            # O buscar una ruta completamente nueva
            self.planificar_ruta_nueva()
        
        def debe_ceder(self, otro_robot):
            # El robot con menos batería debe ceder
            if self.carga < otro_robot.carga:
                return True
            elif self.carga == otro_robot.carga:
                # Si la carga de batería es la misma, el robot con el ID más alto debe ceder
                return self.unique_id > otro_robot.unique_id
            else:
                return False

        
        def replanificar_ruta(self):
            # Decidir cuál ruta necesita ser replanificada
            if self.necesita_cargar:
                # Si el robot necesita cargar, planifica ruta a la estación de carga
                estacion_cercana = self.encontrar_estacion_carga_mas_cercana()
                if estacion_cercana:
                    self.ruta_planeada = self.algoritmo_a_estrella(self.pos, estacion_cercana.pos)
            else:
                # Si el robot está limpiando, planifica ruta a celda sucia más cercana
                celda_objetivo = self.encontrar_celda_sucia_mas_cercana()
                if celda_objetivo:
                    self.ruta_planeada = self.algoritmo_a_estrella(self.pos, celda_objetivo.pos)
        
        def esperar(self):
            self.contador_espera += 1
            if self.contador_espera >= RobotLimpieza.TIEMPO_ESPERA:
                # Lógica para reanudar actividades después de esperar
                self.contador_espera = 0
                self.replanificar_ruta()
            else:
                # Continúa esperando
                pass

        def detectar_colision(self, ruta_otro_robot):
            # Simple chequeo de colisión
            # indice 0: indica si hubo colision o no
            # indice 1: indice donde ocurre la colision
            # indice 2: lugar donde ocurre la colision

            for idx in range(min(len(self.ruta_planeada), len(ruta_otro_robot))):
                if ruta_otro_robot[idx] == self.ruta_planeada[idx]:
                    return [True, idx, self.ruta_planeada[idx]]
            
            return [False, None, None]


        def ir_a_estacion_carga(self):
            # Implementar la lógica para ir a la estación de carga más cercana
            estacion_mas_cercana = self.encontrar_estacion_carga_mas_cercana()
            if estacion_mas_cercana:
                self.ruta_planeada = self.planificar_ruta_a_estacion(estacion_mas_cercana.pos)
                # Mover el robot hacia la primera posición en la ruta planeada
                # Suponiendo que tienes una función para mover al robot
                self.mover_a_siguiente_posicion_en_ruta()

        def mover_a_siguiente_posicion_en_ruta(self):
            # Mueve el robot a la siguiente posición en su ruta planeada
            if self.ruta_planeada:
                self.sig_pos = self.ruta_planeada.pop(0)  # Obtiene y elimina el primer elemento de la lista
                # Comprobar si self.sig_pos es una posición válida en la cuadrícula
                if (0 <= self.sig_pos[0] < self.model.grid.width and
                    0 <= self.sig_pos[1] < self.model.grid.height):
                    self.model.grid.move_agent(self, self.sig_pos)
                    # Reducir la batería por movimiento
                    if self.tiene_caja:
                        self.carga -= self.caja_cargando.peso
                    else:
                        self.carga -= 1
                else:
                    print(f"Posición inválida: {self.sig_pos}")


        def encontrar_estacion_carga_mas_cercana(self):
            min_distancia = float('inf')
            estacion_cercana = None
            for estacion in self.model.estaciones_carga:
                if not estacion.reservada:
                    distancia = self.distancia_hasta(estacion.pos)
                    if distancia < min_distancia:
                        min_distancia = distancia
                        estacion_cercana = estacion
            return estacion_cercana  # Solo retorna la estación más cercana sin reservarla
        
        def reservar_estacion_carga(self, estacion):
            if estacion.reservada:
                return False
            estacion.reservada = True
            self.estacion_reservada = estacion

            self.comunicar_reserva_a_todos(estacion)
            return True
        def comunicar_reserva_a_todos(self,estacion):
            # Enviar información de la estación de carga reservada a otros robots
             for robot in self.model.schedule.agents:
                if isinstance(robot, RobotLimpieza):
                    robot.recibir_informacion_reserva(estacion)

        def recibir_informacion_reserva(self,estacion):
            # Reaccionar a la información de reserva recibida
            if estacion.reservada and estacion not in self.estaciones_carga_reservadas:
                self.estaciones_carga_reservadas.append(estacion)

        def encontrar_celda_sucia_mas_cercana(self):
            # Crear una cola y agregar la posición actual del robot
            cola = deque([self.pos])
            # Crear un conjunto para almacenar las posiciones visitadas
            visitados = set([self.pos])

            while cola:
                pos = cola.popleft()
                contenido_celda = self.model.grid.get_cell_list_contents(pos)

                # Comprobar si la celda está sucia
                for obj in contenido_celda:
                    if isinstance(obj, Celda) and obj.sucia:
                        return pos

                # Agregar las posiciones adyacentes a la cola (incluyendo las diagonales)
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    nueva_pos = (pos[0] + dx, pos[1] + dy)
                    if (0 <= nueva_pos[0] < self.model.grid.width and
                        0 <= nueva_pos[1] < self.model.grid.height and
                        nueva_pos not in visitados and self.model.is_cell_empty(nueva_pos)):
                        cola.append(nueva_pos)
                        visitados.add(nueva_pos)

            # No hay celdas sucias en la cuadrícula
            return None


        def distancia_hasta(self, destino):
            # Implementación simple de la distancia Manhattan
            (x1, y1) = self.pos
            (x2, y2) = destino
            return abs(x1 - x2) + abs(y1 - y2)
           
        def actualizar_ruta(self):
             # Comprobar si la ruta actual sigue siendo válida
            if not self.ruta_es_valida() or (self.estacion_reservada and self.estacion_reservada.reservada and self.estacion_reservada.robot_reservante != self):
                self.replanificar_ruta()
        
        def ruta_es_valida(self):
            # Ejemplo de comprobación de validez de la ruta
            # Esto es solo un esquema y debería ser adaptado según las necesidades específicas del modelo
            if self.ruta_planeada:
                # Comprobar si el objetivo sigue siendo relevante (por ejemplo, si es una celda sucia, verificar que siga sucia)
                ultimo_destino = self.ruta_planeada[-1]
                contenido_ultimo_destino = self.model.grid.get_cell_list_contents([ultimo_destino])
                if any(isinstance(obj, Celda) and obj.sucia for obj in contenido_ultimo_destino):
                    return True
                else:
                    return False
            else:
                # Si no hay ruta planeada, no es válida
                return False

        def planificar_ruta_limpieza(self):
            # Encuentra la celda sucia más cercana
            celda_mas_cercana = self.encontrar_celda_sucia_mas_cercana()

            # Si no hay celdas sucias, no hay necesidad de planificar una ruta
            if celda_mas_cercana is None:
                return
            # Planifica una ruta hasta la celda sucia más cercana utilizando A*

        

        def algoritmo_a_estrella(self, inicio, destino):
            frontera = PriorityQueue()
            frontera.put((0, inicio))
            camino = {inicio: None}
            costo_hasta_ahora = {inicio: 0}

            while not frontera.empty():
                _, actual = frontera.get()

                if actual == destino:
                    break

                # Mandar a obtener_vecinos() las coordenadas donde ocurre la colision
                for siguiente in self.obtener_vecinos(actual, destino):
                    nuevo_costo = costo_hasta_ahora[actual] + 1  # Assuming a uniform cost
                    if siguiente not in costo_hasta_ahora or nuevo_costo < costo_hasta_ahora[siguiente]:
                        costo_hasta_ahora[siguiente] = nuevo_costo
                        prioridad = nuevo_costo + self.heuristica(siguiente, destino)
                        frontera.put((prioridad, siguiente))
                        camino[siguiente] = actual

            #checar si en la ultima posicion del camino hay un robot
            # if not self.model.grid.is_cell_empty(destino):
            #     camino.pop(destino)

            return self.reconstruir_camino(camino, inicio, destino)

            
        def planificar_ruta_a_estacion(self, destino):
            inicio = self.pos
            self.ruta_planeada = self.algoritmo_a_estrella(inicio, destino)



        def obtener_vecinos(self, pos, destino):
            # Agregar la posicion en coordenadas donde ocurre colision
            vecinos = []
            # direcciones = [(0, 1), (1, 0), (0, -1), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]  # Movimientos posibles
            direcciones = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Movimientos posibles

            for dx, dy in direcciones:
                x, y = pos[0] + dx, pos[1] + dy
                if 0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height:
                    # Las celdas vecinas deben estar vacias y no pueden ser la posicion donde ocurre una colision
                    # Si hay una celda vacia solo se agrega como si no es una celda de colision
                    if self.is_cell_empty((x, y)):
                        vecinos.append((x, y))
                        continue
                    
                    
            return vecinos


        def heuristica(self, a, b):
            (x1, y1) = a
            (x2, y2) = b
            return abs(x1 - x2) + abs(y1 - y2)

        def reconstruir_camino(self, camino, inicio, destino):
            ruta = []
            actual = destino
            while actual != inicio:
                if actual not in camino:  # Safety check for unreachable destination
                    return []  # Or raise an exception or handle it as per the simulation's requirement
                ruta.append(actual)
                actual = camino[actual]
            ruta.reverse()  # The path is reconstructed backwards, so we need to reverse it at the end
            return ruta
        
        def is_cell_empty(self, pos):
            """
                    Comprueba si una celda está vacía o contiene ciertos tipos de agentes.
                    :param pos: Tupla de posición (x, y).
                    :return: True si la celda está "vacía" para los propósitos del robot.
                    """
            
            cell_contents = self.model.grid.get_cell_list_contents(pos)

            if not cell_contents:
                return True  # La celda está literalmente vacía

                    # Considera la celda "vacía" si solo contiene agentes que no bloquean el movimiento
            for agent in cell_contents:
                if isinstance(agent, (Caja, Estante)) or (isinstance(agent, RobotLimpieza) and agent.unique_id != self.unique_id) or (isinstance(agent, EstacionCarga) and agent.unique_id != self.estacion_carga_propia.unique_id):
                    return False

            return True  # La celda contiene agentes, pero son del tipo no bloqueante
        
        def replanificacion_a_estrella(self, inicio, destino, total_colisiones):
            frontera = PriorityQueue()
            frontera.put((0, inicio))
            camino = {inicio: None}
            costo_hasta_ahora = {inicio: 0}

            while not frontera.empty():
                _, actual = frontera.get()

                if actual == destino:
                    break

                # Mandar a obtener_vecinos() las coordenadas donde ocurre la colision
                for siguiente in self.replanificacion_obtener_vecinos(actual, destino, total_colisiones):
                    nuevo_costo = costo_hasta_ahora[actual] + 1  # Assuming a uniform cost
                    if siguiente not in costo_hasta_ahora or nuevo_costo < costo_hasta_ahora[siguiente]:
                        costo_hasta_ahora[siguiente] = nuevo_costo
                        prioridad = nuevo_costo + self.heuristica(siguiente, destino)
                        frontera.put((prioridad, siguiente))
                        camino[siguiente] = actual

            #checar si en la ultima posicion del camino hay un robot
            # if not self.model.grid.is_cell_empty(destino):
            #     camino.pop(destino)

            return self.reconstruir_camino(camino, inicio, destino)
        
        def replanificacion_obtener_vecinos(self, pos, destino, total_colisiones):
            # Agregar la posicion en coordenadas donde ocurre colision
            vecinos = []
#            direcciones = [(0, 1), (1, 0), (0, -1), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]  # Movimientos posibles
            direcciones = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Movimientos posibles

            for dx, dy in direcciones:
                x, y = pos[0] + dx, pos[1] + dy
                if 0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height:
                    # Las celdas vecinas deben estar vacias y no pueden ser la posicion donde ocurre una colision
                    # Si hay una celda vacia solo se agrega como vecina si no es una celda de colisiones
                    conflicto_en_celda = False
                    for colision in total_colisiones:
                        if self.is_cell_empty((x, y)) and (x, y) == colision[1]:
                            conflicto_en_celda = True
                            break
                    if conflicto_en_celda == False:
                        vecinos.append((x, y))
                        continue
                    
            return vecinos
        
        def obtener_colisiones(self):
            colisiones = []
            for robot in self.model.schedule.agents:
                if robot != self and isinstance(robot, RobotLimpieza):
                    # Comparar ruta del robot actual con la ruta de otros robots
                    max_length = min(len(self.ruta_planeada), len(robot.ruta_planeada)) - 1
                    for i in range(max_length):
                        if self.ruta_planeada[i] == robot.ruta_planeada[i]:
                            colisiones.append([robot, self.ruta_planeada[i]])
            return colisiones
        
        def planificar_nueva_ruta(self, total_colisiones):
            nueva_ruta = self.replanificacion_a_estrella(self.pos, self.ruta_planeada[-1], total_colisiones)
            self.ruta_planeada = nueva_ruta
            nuevas_colisiones = self.obtener_colisiones()
            # Iterar mientras se obtenga una ruta con colisiones y la longitud de la ruta sea mayor que 0
            while len(nuevas_colisiones) > 0 and len(nueva_ruta) > 0:
                # Agregar a todas las colisiones las nuevas colisiones encontradas
                for colision in nuevas_colisiones:
                    total_colisiones.append(colision)

                # Buscar una nueva ruta omitiendo todas las colisiones
                nueva_ruta = self.replanificacion_a_estrella(self.pos, self.ruta_planeada[-1], total_colisiones)

                # Buscar las nuevas colisiones generadas por esa ruta
                nuevas_colisiones = self.obtener_colisiones()

                self.ruta_planeada = nueva_ruta

            self.contador_replanificaciones += 1

            if len(nuevas_colisiones) == 0 and len(nueva_ruta) > 0:
                # Se encontro una ruta sin colisiones
                self.ruta_planeada = nueva_ruta
            elif len(nueva_ruta) == 0:
                # No se encontro una ruta sin colisiones, el robot debe esperar en su posicion actual hasta el proximo step
                self.ruta_planeada = [self.pos]

class Habitacion(Model):
      def __init__(self, M: int, N: int,
                   num_agentes: int = 5,
                   porc_celdas_sucias: float = 0.6,
                   porc_muebles: float = 0.1,
                   modo_pos_inicial: str = 'Fija',
                   num_cajas: int = 8,
                   num_estantes: int = 5
                    ):
          super().__init__()
          self.current_id = 0
          self.estaciones_carga = []
          self.num_agentes = num_agentes
          self.num_cajas = num_cajas
          self.porc_celdas_sucias = porc_celdas_sucias
          self.porc_muebles = porc_muebles
          self.ids_estantes = []
          self.bandas = []
          self.bandas_entrega = []
          self.cajas = []
          self.estantes = []
          self.cajas_estante = {}
          self.grid = MultiGrid(M, N, False)
          self.schedule = SimultaneousActivation(self)
          self.cargadores = []
          self.num_agentes = num_agentes
          self.id_robot = 1
          self.num_estantes = num_estantes
          self.yendo_cargador = False
          self.cajas_creadas = 0

          self.iniciar_bandas()
          self.iniciar_bandas_entrega()
          self.iniciar_estantes()
          self.iniciar_cargadores()
          self.iniciar_robots()
        # Iniciar cajas
          
      def iniciar_bandas_entrega(self):
            posiciones_banda_entrega = [(3,0), (5,0), (7,0), (9,0), (11,0)]
            for pos in posiciones_banda_entrega:
                banda = BandaEntrega(self.next_id(), self)
                self.grid.place_agent(banda, pos)
                self.schedule.add(banda)
                self.bandas_entrega.append(banda)

      def poner_caja(self, pos, caja):
            # self.grid.place_agent(caja, pos)
            self.schedule.add(caja)

      def crear_caja(self):
          if self.num_cajas <= 0:
                return None
          
          id_estante = None
          while True:
                id_estante = random.choice(self.ids_estantes)
                if id_estante not in self.cajas_estante or self.cajas_estante[id_estante] < 3:
                    break
          if id_estante not in self.cajas_estante:
                self.cajas_estante[id_estante] = 1
          else:
                self.cajas_estante[id_estante] += 1
          peso_caja = random.randint(2, 5)
          id_entrega = random.randint(6, 10)
          caja = Caja(self.next_id(), self, id_estante, peso_caja, id_entrega)
          self.num_cajas -= 1
          self.cajas.append(caja)
          self.cajas_creadas += 1
          return caja
      
      def iniciar_robots(self):
          for cargador in self.cargadores:
              next_id = self.next_id()
              id_estacion_robot = self.id_robot
              self.id_robot += 1    
              if self.id_robot > 5:
                  self.id_robot = 1
              
              robot = RobotLimpieza(next_id, self, id_estacion_robot, cargador)
              self.grid.place_agent(robot, cargador.pos)
              self.schedule.add(robot)      

      def iniciar_cargadores(self):
          pos_y_cargador = 11
          for i in range(self.num_agentes):
              if i % 2 == 0:
                  pos = (0, pos_y_cargador)
              else:
                  pos = (14, pos_y_cargador)
                  pos_y_cargador -= 2

              cargador = EstacionCarga(self.next_id(), self)
              self.cargadores.append(cargador)
              self.grid.place_agent(cargador, pos)

      def iniciar_estantes(self):
          x = 3
          y = 0
          if self.num_estantes > 10:
              y = 10
          elif self.num_estantes > 5 and self.num_estantes <= 10: 
              y = 9
          else:
              y = 7

          for i in range(self.num_estantes):
              if i % 5 == 0 and i != 0:
                  x = 3
                  y -= 3
              pos = (x, y)
              estante = Estante(self.next_id(), self, pos)
              self.grid.place_agent(estante, pos)
              self.schedule.add(estante)
              self.ids_estantes.append(estante.unique_id)
              self.estantes.append(estante)
              x += 2
        #   for pos in posiciones_estantes:
        #       estante = Estante(self.next_id(), self, pos)
        #       self.grid.place_agent(estante, pos)
        #       self.schedule.add(estante)
        #       self.ids_estantes.append(estante.unique_id)
        #       self.estantes.append(estante)
      
      def iniciar_bandas(self):
          posiciones_banda_entrada = [(3,14), (5,14), (7,14), (9,14), (11,14)]
          for pos in posiciones_banda_entrada:
              banda = Banda(self.next_id(), self)
              self.grid.place_agent(banda, pos)
              self.schedule.add(banda)
              self.bandas.append(banda)
      
      def is_cell_empty(self, pos):
          """
                Comprueba si una celda está vacía o contiene ciertos tipos de agentes.
                :param pos: Tupla de posición (x, y).
                :return: True si la celda está "vacía" para los propósitos del robot.
                """
          cell_contents = self.grid.get_cell_list_contents(pos)
          print("en el is_cell_empty: ", self.yendo_cargador)
          if not cell_contents:
             return True  # La celda está literalmente vacía

                # Considera la celda "vacía" si solo contiene agentes que no bloquean el movimiento
          for agent in cell_contents:
              if self.yendo_cargador:
                if isinstance(agent, (RobotLimpieza, Caja, Estante)):
                    return False
              else:
                if isinstance(agent, (RobotLimpieza, Caja, Estante, EstacionCarga)):
                    return False

          return True  # La celda contiene agentes, pero son del tipo no bloqueante
      
      def next_id(self):
            """ Returns the next available ID for a new agent. """
            self.current_id += 1
            return self.current_id
      def agregar_estaciones_carga(self):
            # Determinar el número de estaciones de carga necesarias
            num_estaciones = (self.grid.width * self.grid.height) // 100


            # Añadir estaciones de carga
            for _ in range(num_estaciones):
                pos = self.seleccionar_posicion_para_estacion()
                estacion = EstacionCarga(self.next_id(), self)
                self.grid.place_agent(estacion, pos)
                self.estaciones_carga.append(estacion)

            # Verificar que cada estación de carga se ha agregado correctamente
            for estacion in self.estaciones_carga:
                celda = self.grid.get_cell_list_contents([estacion.pos])
                assert any(isinstance(obj, EstacionCarga) for obj in celda), f"La celda {estacion.pos} no contiene una estación de carga"

      def seleccionar_posicion_para_estacion(self):
                    # Implementar la lógica para seleccionar una posición válida
            posiciones_disponibles = [pos[1] for pos in self.grid.coord_iter()]
                    # Eliminar posiciones ocupadas por muebles o agentes
            posiciones_disponibles = [pos for pos in posiciones_disponibles if self.is_cell_empty(pos)]
                    # Escoger una posición aleatoria de las disponibles
            return self.random.choice(posiciones_disponibles)

      def step(self):
          self.schedule.step()

      def todoLimpio(self):
            for (content, x, y) in self.grid.coord_iter():
                    for obj in content:
                        if isinstance(obj, Celda) and obj.sucia:
                            return False
            return True
      @staticmethod
      def get_grid(model: Model) -> np.ndarray:
            grid = np.zeros((model.grid.width, model.grid.height))
            for cell in model.grid.coord_iter():
                cell_content, pos = cell
                x, y = pos
                for obj in cell_content:
                    if isinstance(obj, RobotLimpieza):
                       grid[x][y] = 2   
                    elif isinstance(obj, Celda):
                         grid[x][y] = int(obj.sucia)
            return grid
      @staticmethod      
      def get_cargas(model: Model):
           return [(agent.unique_id, agent.carga) for agent in model.schedule.agents]
      @staticmethod
      def get_sucias(model: Model) -> int:
            sum_sucias = 0
            for cell in model.grid.coord_iter():
                cell_content, pos = cell
                for obj in cell_content:
                    if isinstance(obj, Celda) and obj.sucia:
                       sum_sucias += 1
            return sum_sucias / model.num_celdas_sucias
      def get_movimientos(agent: Agent) -> dict:
            if isinstance(agent, RobotLimpieza):
                return {agent.unique_id: agent.movimientos}
                        # else:
                        #    return 0   
                       
