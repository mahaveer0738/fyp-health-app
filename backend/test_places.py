import os
import sys
import asyncio

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
# load .env from parent dir (fyp app/.env)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

# Important: we import search_places directly so we can inspect the raw result dictionary
from agent.tools.hospital_locator import search_places

async def test_api():
    print(f"Checking GOOGLE_PLACES_API_KEY in .env... Found: {bool(os.getenv('GOOGLE_PLACES_API_KEY'))}")
    print("Sending search request to Google Places...")
    
    # Run the search for a hospital in New York
    results = await search_places("hospital", "New York")
    
    if results and len(results) > 0 and results[0].get("source") == "Google Places":
        print("\n✅ SUCCESS! Google Places API is working correctly. Here are the top results:\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. {r['name']}")
            print(f"   Address: {r['address']}")
            print(f"   Rating: {r.get('rating')}")
            print()
    elif results and len(results) > 0 and results[0].get("source") == "OpenStreetMap":
        print("\n⚠️ Google Places API failed! The system fell back to the free OpenStreetMap API.")
        print("This usually means the API key is invalid, missing, or the Places API is not enabled in your Google Cloud Console.")
    else:
        print(f"\n❌ Something went wrong, neither API returned expected results: {results}")

if __name__ == "__main__":
    asyncio.run(test_api())
