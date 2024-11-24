import mesa
print(f"Mesa version: {mesa.__version__}")

from mesa.visualization import SolaraViz, make_plot_component, make_space_component

# Import the local MoneyModel.py
from MoneyModel import MoneyModel

def agent_portrayal(agent):
    return {
        "color": "tab:blue",
        "size": 50,
    }

model_params = {
    "n": {
        "type": "SliderInt",
        "value": 50,
        "label": "Number of agents:",
        "min": 10,
        "max": 100,
        "step": 1,
    },
    "width": 10,
    "height": 10,
}

# Create initial model instance
model1 = MoneyModel(50, 10, 10)

SpaceGraph = make_space_component(agent_portrayal)
GiniPlot = make_plot_component("Gini")

page = SolaraViz(
    model1,
    components=[SpaceGraph, GiniPlot],
    model_params=model_params,
    name="Boltzmann Wealth Model",
)
# This is required to render the visualization in the Jupyter notebook
#page