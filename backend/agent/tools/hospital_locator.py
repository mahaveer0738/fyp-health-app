import os
import httpx
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# --- Google Places API (Primary) ---
GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

async def _google_places_search(query: str, location: str, place_type: str = "hospital") -> list[dict]:
    """
    Searches Google Places API (New) for nearby hospitals/pharmacies.
    Uses the Text Search endpoint for natural language queries.
    Docs: https://developers.google.com/maps/documentation/places/web-service/text-search
    """
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.currentOpeningHours,places.nationalPhoneNumber,places.googleMapsUri"
    }
    payload = {
        "textQuery": f"{query} near {location}",
        "languageCode": "en",
        "maxResultCount": 5
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
    
    results = []
    for place in data.get("places", []):
        results.append({
            "name": place.get("displayName", {}).get("text", "Unknown"),
            "address": place.get("formattedAddress", "N/A"),
            "rating": place.get("rating", "N/A"),
            "phone": place.get("nationalPhoneNumber", "N/A"),
            "maps_url": place.get("googleMapsUri", ""),
            "open_now": place.get("currentOpeningHours", {}).get("openNow", "Unknown"),
            "source": "Google Places"
        })
    return results


# --- OpenStreetMap / Nominatim (Fallback) ---
async def _overpass_search(location: str, place_type: str = "hospital") -> list[dict]:
    """
    Searches OpenStreetMap via the Nominatim API for hospitals/pharmacies.
    100% free, no API key required, uses real global data.
    """
    amenity = "hospital" if place_type == "hospital" else "pharmacy"
    
    # Query Nominatim directly for the amenity near the location
    nominatim_url = "https://nominatim.openstreetmap.org/search"
    query = f"{amenity} near {location}"
    params = {"q": query, "format": "json", "addressdetails": 1, "limit": 5}
    headers = {"User-Agent": "FYP-Health-App/2.0 (student-project)"}
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(nominatim_url, params=params, headers=headers)
            if resp.status_code != 200:
                logger.warning(f"Nominatim API returned status {resp.status_code}")
                return [{"name": f"OSM returned error {resp.status_code}", "address": location, "source": "OpenStreetMap"}]
            data = resp.json()
    except Exception as e:
        logger.warning(f"Nominatim API failed: {str(e)}")
        return [{"name": "OSM Timeout — try again shortly", "address": location, "source": "OpenStreetMap"}]
    
    if not data:
        return [{"name": f"No {amenity} found", "address": location, "source": "OpenStreetMap"}]
    
    results = []
    for element in data[:5]:
        name = element.get("name") or element.get("address", {}).get("amenity") or f"Unnamed {amenity.title()}"
        address = element.get("display_name", location)
        lat = element.get("lat")
        lon = element.get("lon")
        
        results.append({
            "name": name,
            "address": address,
            "phone": "N/A", # Nominatim doesn't always return phone directly without extra lookup
            "lat": lat,
            "lon": lon,
            "maps_url": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=17/{lat}/{lon}" if lat and lon else "",
            "open_now": "Check link",
            "source": "OpenStreetMap"
        })
    
    return results


# --- Unified search with graceful fallback ---
async def search_places(query: str, location: str, place_type: str = "hospital") -> list[dict]:
    """
    Hybrid search: Tries Google Places first, falls back to OpenStreetMap.
    This demonstrates graceful API degradation in production systems.
    """
    # Try Google Places first (if API key is configured)
    if GOOGLE_API_KEY:
        try:
            results = await _google_places_search(query, location, place_type)
            if results:
                logger.info(f"✅ Google Places returned {len(results)} results for '{query}' in {location}")
                return results
        except Exception as e:
            logger.warning(f"⚠️ Google Places API failed ({str(e)}), falling back to OpenStreetMap...")
    else:
        logger.info("ℹ️ No Google Places API key configured, using OpenStreetMap directly.")
    
    # Fallback to OpenStreetMap (always free, no key needed)
    try:
        results = await _overpass_search(location, place_type)
        logger.info(f"✅ OpenStreetMap returned {len(results)} results for '{place_type}' in {location}")
        return results
    except Exception as e:
        logger.error(f"❌ Both APIs failed: {str(e)}")
        return [{"name": "Service temporarily unavailable", "address": "Please try again later", "source": "error"}]


def _format_results(results: list[dict]) -> str:
    """Formats the results list into a clean, readable string for the LLM Agent."""
    if not results:
        return "No results found."
    
    output_lines = []
    for i, r in enumerate(results, 1):
        line = f"{i}. **{r.get('name', 'Unknown')}**"
        if r.get("address") and r["address"] != "N/A":
            line += f"\n   📍 {r['address']}"
        if r.get("rating") and r["rating"] != "N/A":
            line += f"\n   ⭐ Rating: {r['rating']}/5"
        if r.get("phone") and r["phone"] != "N/A":
            line += f"\n   📞 {r['phone']}"
        if r.get("maps_url"):
            line += f"\n   🗺️ Map: {r['maps_url']}"
        line += f"\n   (Source: {r.get('source', 'N/A')})"
        output_lines.append(line)
    
    return "\n\n".join(output_lines)


# ==========================================
# LangGraph Tools (used by the Agent)
# ==========================================

@tool
async def hospital_locator(location: str, severity: str) -> str:
    """
    Finds the nearest hospitals or emergency rooms based on the patient's location and severity.
    Uses Google Places API with OpenStreetMap fallback for reliability.
    
    Args:
        location: The city or neighborhood of the patient (e.g., 'Mumbai', 'Andheri West').
        severity: The triage severity level — 'Emergent', 'Urgent', or 'Non-Urgent'.
    """
    if severity.lower() in ["emergent", "life-threatening"]:
        query = "trauma center emergency hospital"
    elif severity.lower() == "urgent":
        query = "urgent care clinic hospital"
    else:
        query = "general hospital clinic"
    
    results = await search_places(query, location, place_type="hospital")
    
    header = f"🏥 Nearest Hospitals for **{severity}** case in **{location}**:\n\n"
    return header + _format_results(results)


@tool
async def pharmacy_locator(medicine_name: str, location: str) -> str:
    """
    Finds nearby pharmacies in the patient's area. Uses Google Places with OpenStreetMap fallback.
    Note: Medicine stock availability requires a real inventory API and is not verified here.
    
    Args:
        medicine_name: The name of the required medication (e.g., 'Paracetamol', 'Insulin').
        location: The city or neighborhood of the patient (e.g., 'Delhi', 'Koramangala').
    """
    results = await search_places(f"pharmacy {medicine_name}", location, place_type="pharmacy")
    
    header = f"💊 Nearest Pharmacies for **{medicine_name}** in **{location}**:\n\n"
    note = "\n\n⚠️ *Note: Medicine stock availability shown above is based on pharmacy proximity. Please call ahead to confirm stock.*"
    return header + _format_results(results) + note
