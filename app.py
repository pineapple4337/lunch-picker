import streamlit as st
import requests
import pandas as pd

# 1. Setup App Layout & Title
st.set_page_config(page_title="Funan Food Picker", page_icon="🍔", layout="centered")
st.title("🍔 Funan Food Picker")
st.write("Find where to eat with your office crew using the modern Places API!")

# 2. Safely Fetch API Key from Streamlit Secrets
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("Please configure your GOOGLE_API_KEY in Streamlit secrets.")
    st.stop()

# Funan Coordinates
FUNAN_LAT = 1.2913
FUNAN_LNG = 103.8499

# 3. Sidebar Filters
st.sidebar.header("Filters")

cuisine = st.sidebar.text_input("Cuisine Type (e.g., Japanese, Mexican, Cafe)", value="")
max_distance = st.sidebar.slider("Max Walking Distance (meters)", min_value=100, max_value=2000, value=500, step=100)
price_tier = st.sidebar.select_slider(
    "Price Range",
    options=["$", "$$", "$$$", "$$$$"],
    value=("$", "$$")
)

# Map price icons to Google V1 Price Levels
price_map = {"$": "PRICE_LEVEL_INEXPENSIVE", "$$": "PRICE_LEVEL_MODERATE", "$$$": "PRICE_LEVEL_EXPENSIVE", "$$$$": "PRICE_LEVEL_VERY_EXPENSIVE"}
selected_prices = [price_map[key] for key in price_map if price_tier[0] <= key <= price_tier[1]]

# 4. Fetch Data Trigger
if st.button("Find Food Options 🎯"):
    with st.spinner("Searching for options inside Funan..."):
        
        url = "https://places.googleapis.com/v1/places:searchText"
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            # Added targeted fields like subDestinations to catch complex basement mall layouts
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.priceLevel,places.regularOpeningHours,places.subDestinations"
        }
        
        # Broaden keyword search so it picks up basement stalls, fast-casual, and quick-service counters
        text_query = f"{cuisine} food" if cuisine else "fast casual food arcade stall restaurant"
        
        payload = {
            "textQuery": text_query,
            # FIX 1: Change Bias to Restriction so Google is forced to look inside the specified radius
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": FUNAN_LAT, "longitude": FUNAN_LNG},
                    "radius": float(max_distance)
                }
            },
            # FIX 2: Pass price levels directly to the API endpoint to filter at the database level
            "priceLevels": selected_prices
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            st.error(f"Google API Error ({response.status_code}): {response.text}")
            st.stop()
            
        data = response.json()
        results = data.get("places", [])
        
        if not results:
            st.warning("No spots found matching those exact settings. Try increasing your walking distance slider to catch adjacent basement food courts!")
        else:
            food_places = []
            for place in results:
                name = place.get("displayName", {}).get("text", "unknown")
                address = place.get("formattedAddress", "unknown")
                rating = place.get("rating", "n/a")
                
                is_open = place.get("regularOpeningHours", {}).get("openNow", None)
                status = "open now" if is_open else "closed/unknown"
                
                raw_price = place.get("priceLevel", "PRICE_LEVEL_UNSPECIFIED")
                price_icon_map = {
                    "PRICE_LEVEL_INEXPENSIVE": "$", 
                    "PRICE_LEVEL_MODERATE": "$$", 
                    "PRICE_LEVEL_EXPENSIVE": "$$$", 
                    "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$"
                }
                price_display = price_icon_map.get(raw_price, "$") # Default to $ if unrated to avoid hiding casual spots
                
                food_places.append({
                    "name": name.lower(),
                    "rating": rating,
                    "price": price_display,
                    "address": address.lower(),
                    "status": status
                })
                
            df = pd.DataFrame(food_places)
            
            # Highlight random pick
            st.success("### 🎲 Random Suggestion For Today:")
            random_pick = df.sample(n=1).iloc[0]
            st.markdown(f"**{random_pick['name'].title()}** — Rating: {random_pick['rating']} ⭐ ({random_pick['price']})")
            st.caption(f"📍 {random_pick['address']}")
            
            st.write("---")
            
            # Show all options
            st.subheader("All Nearby Options")
            st.dataframe(
                df,
                column_config={
                    "name": "Restaurant Name",
                    "rating": "Rating ⭐",
                    "price": "Price Tier",
                    "address": "Location / Address",
                    "status": "Status"
                },
                use_container_width=True,
                hide_index=True
            )
