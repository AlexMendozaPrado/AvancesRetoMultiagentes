import random

import mesa

from .model import Habitacion, RobotLimpieza, Celda, Mueble, EstacionCarga, Banda, Estante, Caja, BandaEntrega

MAX_NUMBER_ROBOTS = 10


def agent_portrayal(agent):
    if isinstance(agent, RobotLimpieza):
        portrayal = {"Shape": "circle", "Filled": "true", "Color": "black", "Layer": 0, "r": 1.0}
        if agent.tiene_caja:
            portrayal["Color"] = "black"
            portrayal["text"] = "🤖📦"

        else:
            portrayal["Color"] = "black"
            portrayal["text_color"] = "white"
            portrayal["text"] = f"🤖{agent.carga}"
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

grid = mesa.visualization.CanvasGrid(
    agent_portrayal, 15, 15, 350, 350)


model_params = {
    "num_agentes": mesa.visualization.Slider(
        "Número de Robots",
        5,
        2,
        MAX_NUMBER_ROBOTS,
        1,
        description="Escoge cuántos robots deseas implementar en el modelo",
    ),
    "num_estantes": mesa.visualization.Slider(
        "Número de estantes",
        5,
        2,
        15,
        1
    ),
    "num_cajas": mesa.visualization.Slider(
        "Número de Cajas",
        5,
        5,
        30,
        1,
        description="Escoge cuántas cajas deseas implementar en el modelo",
    ),
    "M": 15,
    "N": 15,
} 

server = mesa.visualization.ModularServer(
    Habitacion, [grid],
    "botCleaner", model_params, 8525
)