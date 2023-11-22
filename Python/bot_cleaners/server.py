import random

import mesa

from .model import Habitacion, RobotLimpieza, Celda, Mueble, EstacionCarga, Banda, Estante, Caja

MAX_NUMBER_ROBOTS = 10


def agent_portrayal(agent):
    if isinstance(agent, RobotLimpieza):
        return {"Shape": "circle", "Filled": "false", "Color": "black", "Layer": 0, "r": 1.0,
                "text": f"{agent.banda_id}", "text_color": "yellow"}
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
    elif isinstance(agent, Estante):
        return {"Shape": "rect", "Filled": "true", "Color": "grey", "Layer": 0,
                "w": 0.9, "h": 0.9, "text": f"{agent.unique_id}", "text_color": "Black"}
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
    "porc_celdas_sucias": mesa.visualization.Slider(
        "Porcentaje de Celdas Sucias",
        0.3,
        0.0,
        0.75,
        0.05,
        description="Selecciona el porcentaje de celdas sucias",
    ),
    "porc_muebles": mesa.visualization.Slider(
        "Porcentaje de Muebles",
        0.1,
        0.0,
        0.25,
        0.01,
        description="Selecciona el porcentaje de muebles",
    ),
    "modo_pos_inicial": mesa.visualization.Choice(
        "Posición Inicial de los Robots",
        "Aleatoria",
        ["Fija", "Aleatoria"],
        "Selecciona la forma se posicionan los robots"
    ),
    "M": 15,
    "N": 15,
} 

server = mesa.visualization.ModularServer(
    Habitacion, [grid],
    "botCleaner", model_params, 8525
)