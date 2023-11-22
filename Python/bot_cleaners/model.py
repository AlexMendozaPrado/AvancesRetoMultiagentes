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
    def __init__(self,unique_id,model, estante_id = None):
        super().__init__(unique_id,model)
        self.pos = None
        self.sig_pos = None
        self.estante_id = estante_id


class Estante(Agent):
    def __init__(self,unique_id,model):
        super().__init__(unique_id,model)
        

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
        def __init__(self, unique_id, model, banda_id = None):
            super().__init__(unique_id, model)
            self.banda_id = banda_id
            self.sig_pos = None
            self.contador_espera = 0  # Inicializar el contador de espera
            self.movimientos = 0
            self.carga = 21
            self.umbral_bateria = 20  # Ejemplo de umbral de batería
            self.ruta_planeada = []  # Añadir para guardar la ruta planeada
            self.estacion_carga = None  # Añadir para ubicar la estación de carga
            self.necesita_cargar = True  # Or some initial value based on your logic
            self.contador_replanificaciones = 0  # Inicializar el contador de replanificaciones
            self.estacion_reservada = None
            self.estaciones_carga_reservadas = [] # Añadir para almacenar las estaciones reservadas



     
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


            # Planificar ruta hacia celda sucia si no hay ruta planeada
            if not self.ruta_planeada:
                # TODO: Robot mas cercano se dirige a la banda de su ID
                # Busca la banda con el mismo ID que el robot
                # Imprime todos los ids de las bandas
                for banda in self.model.schedule.agents:
                    if isinstance(banda, Banda):
                        print(banda.unique_id)
                        if banda.unique_id == self.banda_id:
                            print("ID Match")
                            print(banda.pos)
                            # Cambia banda.pos en y-1
                            punto_recoleccion = (banda.pos[0], banda.pos[1] - 1)
                            print(punto_recoleccion)
                            self.ruta_planeada = self.algoritmo_a_estrella(self.pos, punto_recoleccion)
                            
                            print(self.ruta_planeada)

                # TODO: Robot en estación de recolección recoge la caja
                # Si el robot es vecino de la caja con su ID, cambia la posicion de la caja a la misma posicion del robot
                for caja in self.model.schedule.agents:
                    if isinstance(caja, Caja):
                        print(caja.unique_id)
                        print(caja.pos)


                        if (self.son_vecinos_ortogonales(caja)):
                            caja.pos = self.pos
                            # self.model.caja.sig_pos = self.pos
                            print("La caja se encuentra en la posicion del robot")

                # TODO: Robot con caja se dirige a el estante con el ID de la caja
                # Busca la posicion del estante con el mismo ID que la caja


                # TODO: Robot entrega la caja en el estante
                #si tiene batteria para ir por la caja, dejarla, y luego cargarse, ir por la caja, si no cargarse


            # Verificar nivel de batería y planificar ruta hacia estación de carga si es necesario
            if self.carga < self.umbral_bateria and not self.estacion_reservada: 
                self.necesita_cargar = True 
                estacion_cercana = self.encontrar_estacion_carga_mas_cercana()
                if estacion_cercana:
                    self.reservar_estacion_carga(estacion_cercana)
                    self.ruta_planeada = self.algoritmo_a_estrella(self.pos, estacion_cercana.pos)
                    print(self.ruta_planeada)
                    print(self.ruta_planeada)  # Imprime la ruta planeada

            # Mover el robot a lo largo de la ruta planeada
            self.mover_a_siguiente_posicion_en_ruta()
            self.limpiar_celda_actual()  # Limpia la celda si es necesario
            # Comunicar ruta y resolver conflictos (aunque en tu caso no se comuniquen)
            # Suponiendo que tienes una función para comunicar la ruta planeada
            self.comunicar_ruta()
            self.actualizar_ruta()
            #self.resolver_deadlocks()

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
            if en_estacion_carga:
                print(f"Robot {self.unique_id} ha encontrado una estación de carga en la celda {self.pos}")
            
            
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
            if self.detectar_colision(ruta_otro_robot):
               self.resolver_conflicto(otro_robot)
            # Comprobar si la ruta recibida incluye la estación de carga que este robot ha reservado
            elif any(estacion for estacion in self.model.estaciones_carga if estacion.pos in ruta_otro_robot and estacion.reservada and estacion.robot_reservante == self):
                self.resolver_conflicto(otro_robot)  # Considerar esto como un conflicto y replanificar la ruta

        def resolver_conflicto(self, otro_robot):

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

            for idx in range(min(len(self.ruta_planeada), len(ruta_otro_robot))):
                if ruta_otro_robot[idx] == self.ruta_planeada[idx]:
                    return True
            
            return False


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

                for siguiente in self.obtener_vecinos(actual):
                    nuevo_costo = costo_hasta_ahora[actual] + 1  # Assuming a uniform cost
                    if siguiente not in costo_hasta_ahora or nuevo_costo < costo_hasta_ahora[siguiente]:
                        costo_hasta_ahora[siguiente] = nuevo_costo
                        prioridad = nuevo_costo + self.heuristica(siguiente, destino)
                        frontera.put((prioridad, siguiente))
                        camino[siguiente] = actual

            return self.reconstruir_camino(camino, inicio, destino)

            
        def planificar_ruta_a_estacion(self, destino):
            inicio = self.pos
            self.ruta_planeada = self.algoritmo_a_estrella(inicio, destino)



        def obtener_vecinos(self, pos, evitar_obstaculos=True):
            vecinos = []
            direcciones = [(0, 1), (1, 0), (0, -1), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]  # Movimientos posibles
            for dx, dy in direcciones:
                x, y = pos[0] + dx, pos[1] + dy
                if 0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height:
                    if evitar_obstaculos and self.model.grid.is_cell_empty((x, y)):
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

class Habitacion(Model):
      def __init__(self, M: int, N: int,
                   num_agentes: int = 5,
                   porc_celdas_sucias: float = 0.6,
                   porc_muebles: float = 0.1,
                   modo_pos_inicial: str = 'Fija',
                    ):
          super().__init__()
          self.current_id = 0
          self.estaciones_carga = []
          self.num_agentes = num_agentes
          self.porc_celdas_sucias = porc_celdas_sucias
          self.porc_muebles = porc_muebles
          self.ids_estantes = []
          self.cajas_estante = {}
          self.grid = MultiGrid(M, N, False)
          self.schedule = SimultaneousActivation(self)
          self.posiciones_cargadores = []
          self.num_agentes = num_agentes
          self.id_robot = 1

          self.iniciar_bandas()
          self.iniciar_estantes()
          self.iniciar_cargadores()
          self.iniciar_robots()
        # Iniciar cajas
          
      def poner_caja(self, pos, caja):
            # self.grid.place_agent(caja, pos)
            self.schedule.add(caja)

      def crear_caja(self):
          id_estante = None
          while True:
                id_estante = random.choice(self.ids_estantes)
                if id_estante not in self.cajas_estante or self.cajas_estante[id_estante] <= 3:
                    break
          if id_estante not in self.cajas_estante:
                self.cajas_estante[id_estante] = 1
          else:
                self.cajas_estante[id_estante] += 1
          caja = Caja(self.next_id(), self, id_estante)
          return caja
      def iniciar_robots(self):
          for pos in self.posiciones_cargadores:
              next_id = self.next_id()
              id_estacion_robot = self.id_robot
              self.id_robot += 1
              if self.id_robot > 5:
                  self.id_robot = 1
              robot = RobotLimpieza(next_id, self, id_estacion_robot)
              self.grid.place_agent(robot, pos)
              self.schedule.add(robot)      

      def iniciar_cargadores(self):
          pos_y_cargador = 11
          for i in range(self.num_agentes):
              if i % 2 == 0:
                  pos = (0, pos_y_cargador)
                  self.posiciones_cargadores.append(pos)
              else:
                  pos = (14, pos_y_cargador)
                  self.posiciones_cargadores.append(pos)
                  pos_y_cargador -= 2

              cargador = EstacionCarga(self.next_id(), self)
              self.grid.place_agent(cargador, pos)

      def iniciar_estantes(self):
          posiciones_estantes = [(3,7), (5,7), (7, 7), (9, 7), (11, 7)]
          for pos in posiciones_estantes:
              estante = Estante(self.next_id(), self)
              self.grid.place_agent(estante, pos)
              self.schedule.add(estante)
              self.ids_estantes.append(estante.unique_id)
      
      def iniciar_bandas(self):
          posiciones_banda_entrada = [(3,14), (5,14), (7,14), (9,14), (11,14)]
          for pos in posiciones_banda_entrada:
              banda = Banda(self.next_id(), self)
              self.grid.place_agent(banda, pos)
              self.schedule.add(banda)
      
      def is_cell_empty(self, pos):
          """
                Comprueba si una celda está vacía o contiene ciertos tipos de agentes.
                :param pos: Tupla de posición (x, y).
                :return: True si la celda está "vacía" para los propósitos del robot.
                """
          cell_contents = self.grid.get_cell_list_contents(pos)
          if not cell_contents:
             return True  # La celda está literalmente vacía

                # Considera la celda "vacía" si solo contiene agentes que no bloquean el movimiento
          for agent in cell_contents:
              if isinstance(agent, (Mueble, RobotLimpieza, EstacionCarga)):
                 return False  # La celda está bloqueada

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
            print("Todas las estaciones de carga se han agregado correctamente")

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
                       
                   

            

            

        
