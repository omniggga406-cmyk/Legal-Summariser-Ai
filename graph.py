from langgraph.graph import StateGraph, END
import os
import sys

# Force absolute path discovery across Windows OneDrive architectures
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from src.state import LegalState
from src.agents import (
    document_router_agent, 
    chronology_agent, 
    contract_specialist_agent, 
    litigation_specialist_agent
)

def build_legal_graph():
    """Compiles individual processing agents into a stateful, cyclical pipeline workflow network."""
    workflow = StateGraph(LegalState)
    
    workflow.add_node("router", document_router_agent)
    workflow.add_node("chronology", chronology_agent)
    workflow.add_node("contract_summary", contract_specialist_agent)
    workflow.add_node("litigation_summary", litigation_specialist_agent)
    
    workflow.set_entry_point("router")
    
    def routing_condition(state: LegalState):
        if state["doc_type"] == "Contract":
            return "contract_summary"
        else:
            return "litigation_summary"
            
    workflow.add_conditional_edges(
        "router",
        routing_condition,
        {
            "contract_summary": "contract_summary",
            "litigation_summary": "litigation_summary"
        }
    )
    
    workflow.add_edge("contract_summary", "chronology")
    workflow.add_edge("litigation_summary", "chronology")
    workflow.add_edge("chronology", END)
    
    return workflow.compile()
