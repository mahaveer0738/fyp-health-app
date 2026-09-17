from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver # Simple in-memory checkpointer for testing

from backend.agent.state import AgentState
from backend.agent.nodes.retrieval_node import retrieval_node
from backend.agent.nodes.chatbot_node import chatbot_node, tools
from backend.ml.model import triage_model
from backend.cv.image_model import extract_text_from_image
import logging

logger = logging.getLogger(__name__)

# Data preparation nodes (run before the chatbot)
def prepare_vitals_node(state: AgentState) -> dict:
    """Gets ML prediction if vitals are provided."""
    vitals = state.get("vitals")
    if vitals:
        try:
            prediction = triage_model.predict(vitals)
            return {"ml_prediction": prediction}
        except Exception as e:
            logger.error(f"Error predicting vitals: {e}")
            return {}
    return {}

def ocr_node(state: AgentState) -> dict:
    """Extracts text from uploaded image."""
    image_bytes = state.get("image_bytes")
    if image_bytes:
        extracted_text = extract_text_from_image(image_bytes)
        return {"ocr_text": extracted_text}
    return {}

# 1. Initialize the Graph Builder
workflow = StateGraph(AgentState)

# 2. Add all Nodes
workflow.add_node("prepare_vitals", prepare_vitals_node)
workflow.add_node("ocr", ocr_node)
workflow.add_node("retrieval", retrieval_node)
workflow.add_node("chatbot", chatbot_node)
# LangGraph's prebuilt ToolNode automatically executes the tools requested by the LLM
workflow.add_node("tools", ToolNode(tools))

# 3. Define the Edges (The Flow)

# Entry point -> prepare vitals -> ocr -> retrieval (RAG)
workflow.add_edge(START, "prepare_vitals")
workflow.add_edge("prepare_vitals", "ocr")
workflow.add_edge("ocr", "retrieval")
workflow.add_edge("retrieval", "chatbot")

# The Agentic Loop: 
# After the chatbot runs, we use a conditional edge to check what the LLM did.
# `tools_condition` checks if the last message has `tool_calls`. 
# If YES -> routes to "tools". If NO -> routes to END.
workflow.add_conditional_edges(
    "chatbot",
    tools_condition,
)

# After the tools finish executing, always loop back to the chatbot 
# so it can read the tool results and form a final answer.
workflow.add_edge("tools", "chatbot")

# 4. Compile the Graph with Memory (Checkpointer)
# This memory saver keeps the conversation history alive between requests!
memory = MemorySaver()
clinical_agent = workflow.compile(checkpointer=memory)
