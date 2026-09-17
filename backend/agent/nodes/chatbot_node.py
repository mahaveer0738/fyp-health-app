from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from backend.agent.state import AgentState
from backend.core.config import settings
from backend.agent.tools.hospital_locator import hospital_locator
from backend.agent.tools.pharmacy_locator import pharmacy_locator
import logging

logger = logging.getLogger(__name__)

# Define the tools the agent can use
tools = [hospital_locator, pharmacy_locator]

try:
    # Initialize the LLM and bind the tools to it
    llm = ChatGroq(
        model=settings.GROQ_MODEL,
        temperature=0,
        api_key=settings.GROQ_API_KEY
    )
    llm_with_tools = llm.bind_tools(tools)
except Exception as e:
    logger.warning(f"Failed to initialize Groq client: {e}")
    llm_with_tools = None

def chatbot_node(state: AgentState) -> dict:
    """
    The reasoning engine. Looks at the state (vitals, OCR, RAG context, and chat history)
    and either answers the user or calls a tool.
    """
    if not llm_with_tools:
        return {"messages": [SystemMessage(content="LLM is not configured properly.")]}
        
    # We only want to inject the context on the FIRST turn of a new conversation
    # to save tokens. But for simplicity, we'll build a rich system prompt here.
    
    ml_prediction = state.get("ml_prediction")
    retrieved_context = state.get("retrieved_context", [])
    symptoms = state.get("symptoms_text", "")
    ocr_text = state.get("ocr_text", "")
    user_location = state.get("user_location", "Unknown Location")
    
    patient_profile = state.get("patient_profile", {})
    visit_history = state.get("visit_history", [])
    
    context_str = "\n".join(retrieved_context) if retrieved_context else "No specific guidelines retrieved."
    triage_info = f"Level: {ml_prediction.triage_label} (Probability: {ml_prediction.probability}%)" if ml_prediction else "Not provided"
    
    # Format Patient Profile
    profile_str = "No profile available."
    if patient_profile:
        profile_str = f"Name: {patient_profile.get('name', 'Unknown')}, Age: {patient_profile.get('age', 'Unknown')}, Gender: {patient_profile.get('gender', 'Unknown')}\nChronic Conditions: {patient_profile.get('chronic_conditions', 'None')}"
        
    # Format Visit History
    history_str = "No past visits found."
    if visit_history:
        history_str = ""
        for visit in visit_history[-3:]: # Get last 3 visits
            history_str += f"- [Date: {visit.get('timestamp')}] Symptoms: {visit.get('symptoms')}, Triage: {visit.get('triage_label')}\n"

    system_prompt = f"""
You are an advanced clinical decision-support agent.
Your job is to analyze patient symptoms, ML triage predictions, and retrieved medical guidelines to advise the user.

### Patient Details:
{profile_str}

### Current Visit:
- Symptoms: {symptoms}
- Location: {user_location}
- Scanned Document Text: {ocr_text if ocr_text else "None"}

### Past Visit History:
{history_str}

### ML Triage Prediction:
{triage_info}

### Clinical Guidelines Context:
{context_str}

**Instructions:**
1. You have access to tools (e.g., hospital_locator, pharmacy_locator). Use them if the user needs to find a physical location based on their severity or prescription.
2. ALWAYS use the provided context to explain your reasoning.
3. If the triage level is emergent, strongly advise them to go to the hospital and use the hospital_locator tool to find one.
4. Do not invent medical facts. You are an assistant, not a doctor.
"""

    # We inject the SystemMessage at the start of the message history
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    
    # Run the LLM
    try:
        response = llm_with_tools.invoke(messages)
        # LangGraph expects a dictionary with the state updates. 
        # The 'messages' reducer will append this response to the state.
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"Error during LLM reasoning: {e}")
        return {"messages": [SystemMessage(content=f"Error generating response: {e}")]}
