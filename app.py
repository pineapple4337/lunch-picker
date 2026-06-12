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
    with st.spinner("Searching for options near Funan..."):
        
        # New V1 Endpoint URL
        url = "https://places.googleapis.com/v1/places:searchText"
        
        # Mandatory Headers for the New API (including FieldMask to save costs)
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.priceLevel,places.regularOpeningHours"
        }
        
        # New API Payload Structure
        text_query = f"{cuisine} restaurant food" if cuisine else "restaurant food"
        payload = {
            "textQuery": text_query,
            "locationBias": {
                "circle": {
                    "center": {"latitude": FUNAN_LAT, "longitude": FUNAN_LNG},
                    "radius": float(max_distance)
                }
            }
        }
        
        # Send POST request
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            st.error(f"Google API Error ({response.status_code}): {response.text}")
            st.stop()
            
        data = response.json()
        results = data.get("places", [])
        
        if not results:
            st.warning("No places found matching those specific filters. Try expanding your search!")
        else:
            food_places = []
            for place in results:
                # Filter by price manually to guarantee accuracy against text search limits
                raw_price = place.get("priceLevel", "PRICE_LEVEL_UNSPECIFIED")
                if raw_price != "PRICE_LEVEL_UNSPECIFIED" and raw_price not in selected_prices:
                    continue
                
                name = place.get("displayName", {}).get("text", "unknown")
                address = place.get("formattedAddress", "unknown")
                rating = place.get("rating", "n/a")
                
                # Simplify status display
                is_open = place.get("regularOpeningHours", {}).get("openNow", None)
                status = "open now" if is_open else "closed/unknown"
                
                # Format price symbols
                price_icon_map = {"PRICE_LEVEL_INEXPENSIVE": "$", "PRICE_LEVEL_MODERATE": "$$", "PRICE_LEVEL_EXPENSIVE": "$$$", "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$"}
                price_display = price_icon_map.get(raw_price, "n/a")
                
                food_places.append({
                    "name": name.lower(),
                    "rating": rating,
                    "price": price_display,
                    "address": address.lower(),
                    "status": status
                })
            
            if not food_places:
                st.warning("Found options nearby, but none matched your exact price range filter.")
                st.stop()
                
            # Convert to DataFrame
            df = pd.DataFrame(food_places)
            
            # Highlight a random choice
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
