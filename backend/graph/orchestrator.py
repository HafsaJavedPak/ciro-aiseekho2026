from langgraph.graph import StateGraph, START, END
from backend.graph.state import IncidentState
from backend.graph.nodes import (
    fusion_node, credibility_node, recovery_node, 
    classification_node, allocation_node, simulation_node, messaging_node
)
from backend.graph.edges import route_after_recovery, route_after_classification

def build_graph() -> StateGraph:
    """Constructs the CIRO orchestrator DAG."""
    builder = StateGraph(IncidentState)

    # Register Nodes
    builder.add_node("fusion", fusion_node)
    builder.add_node("credibility", credibility_node)
    builder.add_node("recovery", recovery_node)
    builder.add_node("classification", classification_node)
    builder.add_node("allocation", allocation_node)
    builder.add_node("simulation", simulation_node)
    builder.add_node("messaging", messaging_node)

    # Standard Flow
    builder.add_edge(START, "fusion")
    builder.add_edge("fusion", "credibility")
    builder.add_edge("credibility", "recovery")

    # Conditional Edges
    builder.add_conditional_edges(
        "recovery",
        route_after_recovery,
        {
            "END": END,
            "CONTINUE": "classification"
        }
    )
    
    builder.add_conditional_edges(
        "classification",
        route_after_classification,
        {
            "END": END,
            "CONTINUE": "allocation"
        }
    )
    
    builder.add_edge("allocation", "simulation")
    builder.add_edge("simulation", "messaging")
    builder.add_edge("messaging", END)

    return builder

# Compiled graph
orchestrator_graph = build_graph().compile()
