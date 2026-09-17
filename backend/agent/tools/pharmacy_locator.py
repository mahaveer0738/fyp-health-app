from langchain_core.tools import tool

@tool
def pharmacy_locator(medicine_name: str, location: str) -> str:
    """
    Finds a nearby pharmacy that has the specified medicine in stock.
    
    Args:
        medicine_name: The name of the required medication.
        location: The city or neighborhood of the patient.
    """
    # Mock API call
    return f"Mock API Result: 'Apollo Pharmacy' in {location} has {medicine_name} in stock. It is open 24/7."
