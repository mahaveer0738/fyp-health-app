from langchain_core.tools import tool

@tool
def hospital_locator(location: str, severity: str) -> str:
    """
    Finds the nearest hospitals or emergency rooms based on the location and severity of the issue.
    
    Args:
        location: The city or neighborhood of the patient.
        severity: 'Emergent', 'Urgent', or 'Non-Urgent'.
    """
    # In a real app, this would call Google Places API. 
    # For now, we mock the response to demonstrate LangGraph tool calling.
    
    if severity.lower() in ["emergent", "life-threatening"]:
        return f"Mock API Result: Found nearest Trauma Center in {location} at 123 Main St. 2 minutes away. Immediate admission available."
    elif severity.lower() == "urgent":
        return f"Mock API Result: Found Urgent Care Clinic in {location} at 456 Elm St. 10 minutes away."
    else:
        return f"Mock API Result: Found General Hospital in {location}. Open from 9 AM to 5 PM."
