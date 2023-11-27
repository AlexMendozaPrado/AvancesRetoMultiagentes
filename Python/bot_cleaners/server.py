import random
import mesa
from flask import Flask, request, jsonify
from flask_cors import CORS
from .model import Habitacion, RobotLimpieza, Celda, Mueble, EstacionCarga, Banda, Estante, Caja, BandaEntrega
import threading

# Variables globales para configurar la simulación
NUMBER_ROBOTS = 5
NUMBER_SHELFS = 5
NUMBER_BOXES = 10

# Inicialización de la aplicación Flask
app = Flask(__name__)
CORS(app)

# Definición del agente para visualización en Mesa
def agent_portrayal(agent):
    if isinstance(agent, RobotLimpieza):
        portrayal = {"Shape": "circle", "Filled": "true", "Color": "black", "Layer": 0, "r": 1.0}
        if agent.tiene_caja:
            portrayal["Color"] = "black"
            portrayal["text"] = "🤖📦"

        else:
            portrayal["Color"] = "black"
            portrayal["text_color"] = "white"
            portrayal["text"] = f"{agent.unique_id}"
            #portrayal["text"] = f"{agent.unique_id}"
        return portrayal
    elif isinstance(agent, Mueble):
        return {"Shape": "rect", "Filled": "true", "Color": "white", "Layer": 0,
                "w": 0.9, "h": 0.9, "text_color": "Black", "text": f"{agent.unique_id}"}
    elif isinstance(agent, EstacionCarga):
        return {"Shape": "rect", "Filled": "true", "Color": "blue", "Layer": 0,
                "w": 0.9, "h": 0.9, "text": f"{agent.unique_id}", "text_color": "Black"}
    elif isinstance(agent, Celda):
        portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "w": 0.9, "h": 0.9, "text_color": "Black"}
        if agent.sucia:
            portrayal["Color"] = "white"
            portrayal["text"] = "🦠"
        else:
            portrayal["Color"] = "white"
            portrayal["text"] = f"{agent.unique_id}"
        return portrayal
    elif isinstance(agent, Banda):
        portrayal = {"Shape": "rect", "Filled": "true", "Layer": "1", "w": 0.9, "h": 0.9, "text_color": "Black"}
        if agent.tiene_caja:
            portrayal["Color"] = "Yellow"
            portrayal["text"] = f"{agent.caja_recoger.estante_id}"
        else:
            portrayal["Color"] = "Red"
            portrayal["text"] = f"{agent.unique_id}"
        return portrayal
    elif isinstance(agent, BandaEntrega):
        portrayal = {"Shape": "rect", "Filled": "true", "Layer": "1", "w": 0.9, "h": 0.9, "text_color": "Black"}
        portrayal["Color"] = "Purple"
        portrayal["text"] = f"{agent.unique_id}"
        return portrayal
    elif isinstance(agent, Estante):
        portrayal = {"Shape": "rect", "Filled": "true", "Color": "grey", "Layer": 0, "w": 0.9, "h": 0.9, "text_color": "Black"}
        if agent.cantidad_cajas == 0:
            portrayal["Color"] = "grey"
            portrayal["text"] = "🤡"
        elif agent.cantidad_cajas == 1:
            portrayal["Color"] = "grey"
            portrayal["text"] = "📦"
        elif agent.cantidad_cajas == 2:
            portrayal["Color"] = "grey"
            portrayal["text"] = "📦📦"
        elif agent.cantidad_cajas == 3:
            portrayal["Color"] = "grey"
            portrayal["text"] = "📦📦📦"    
        return portrayal
    
    elif isinstance(agent, Caja):
        return {"Shape": "circle", "Filled": "true", "Color": "brown", "Layer": 2,
                "w": 0.9, "h": 0.9, "text": "📦", "text_color": "Black"}

# Creación del grid para la visualización
model = None

@app.route('/start-simulation', methods=['POST'])
def receive_data():
    global NUMBER_ROBOTS, NUMBER_SHELFS, NUMBER_BOXES, model

    # Verificar si el cuerpo de la solicitud es JSON
    if not request.is_json:
        return "Formato no JSON", 400

    # Obtener los datos del JSON
    data = request.get_json()
    NUMBER_ROBOTS = data["robots"]
    NUMBER_SHELFS = data["almacenes"]
    NUMBER_BOXES = data["cajas"]

    # Parámetros del modelo
    model_params = {
        "num_agentes": NUMBER_ROBOTS,
        "num_estantes": NUMBER_SHELFS,
        "num_cajas": NUMBER_BOXES,
        "M": 21,
        "N": 21,
    }

    # Creación del servidor de visualización de Mesa
    model = Habitacion(**model_params)

    return "Submit data", 200

@app.route('/start-simulation', methods=['GET'])
def start_simulation():
    global model
    # Creación del servidor de visualización de Mesa
    data = None
    if model is not None:
        data = model.datacollector.get_starting_grid()
    return "Start simulation", 200