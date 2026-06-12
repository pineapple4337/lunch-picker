import streamlit as st
import requests
import pandas as pd

# =====================================================================
# 1. SETUP APP LAYOUT & TITLE
# =====================================================================
st.set_page_config(page_title="Funan Food Picker", page_icon="🍔", layout="centered")
st.title("🍔 Funan Food Picker")
st.write("Find where to eat with your office crew using the modern Nearby Radar!")

# =====================================================================
# 2. SAFELY FETCH API KEY FROM STREAMLIT SECRETS
# =====================================================================
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("Please configure your GOOGLE_API_KEY in Streamlit secrets.")
    st.stop()

# Static Funan Coordinates
FUNAN_LAT = 1.2913
FUNAN_LNG = 103.8499

# =====================================================================
# 3. SIDEBAR FILTERS
# =====================================================================
st.sidebar.header("Filters")

# Dropdown choices to map to Google's strict type fields instead of messy text queries
cuisine_type = st.sidebar.selectbox(
    "Establishment Category",
    options=["All Food Places", "Fast Food Only", "Cafes & Bakeries", "Standard Restaurants"]
)

max_distance = st.sidebar.slider("Max Distance (meters)", min_value=50, max_value=800, value=200, step=50)

price_tier = st.sidebar.select_slider(
    "Price Range",
    options=["$", "$$", "$$$", "$$$$"],
    value=("$", "$$")
)

# Map price icons to Google V1 Price Levels
price_map = {
    "$": "PRICE_LEVEL_INEXPENSIVE", 
    "$$": "PRICE_LEVEL_MODERATE", 
    "$$$": "PRICE_LEVEL_EXPENSIVE", 
    "$$$$": "PRICE_LEVEL_VERY_EXPENSIVE"
}
selected_prices = [key for key in price_map if price_tier[0] <= key <= price_tier[1]]
allowed_google_tiers = [price_map[tier] for tier in selected_prices] + ["PRICE_LEVEL_UNSPECIFIED"]

# =====================================================================
# 4. FETCH DATA TRIGGER (USING NEARBY SEARCH)
# =====================================================================
if st.button("Find Food Options 🎯"):
    with st.spinner("Scanning Funan perimeter layer by layer..."):
        
        # Switched to the dedicated nearbySearch endpoint
        url = "https://places.googleapis.com/v1/places:searchNearby"
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.priceLevel,places.regularOpeningHours,places.primaryType"
        }
        
        # Determine strict category filters based on selection
        # These are official Google classification tags that catch tiny basement stalls easily
        if cuisine_type == "Fast Food Only":
            included_types = ["fast_food_restaurant"]
        elif cuisine_type == "Cafes & Bakeries":
            included_types = ["cafe", "bakery", "coffee_shop"]
        elif cuisine_type == "Standard Restaurants":
            included_types = ["restaurant"]
        else:
            # Broad sweeping catch-all for general lunch runs
            included_types = ["restaurant", "food", "fast_food_restaurant", "cafe", "bakery"]
            
        payload = {
            "includedTypes": included_types,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": FUNAN_LAT, "longitude": FUNAN_LNG},
                    "radius": float(max_distance)
                }
            },
            "maxResultCount": 20,
            "rankPreference": "DISTANCE" # Forces Google to prioritize immediate proximity over global fame
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            st.error(f"Google API Error ({response.status_code}): {response.text}")
            st.stop()
            
        data = response.json()
        results = data.get("places", [])
        
        if not results:
            st.warning("No registered food spots caught on radar. Try broadening the distance slider slightly!")
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
                price_display = price_icon_map.get(raw_price, "unspecified")
                
                food_places.append({
                    "name": name.lower(),
                    "rating": rating,
                    "price_tier": price_display,
                    "raw_price_level": raw_price,
                    "address": address.lower(),
                    "status": status
                })
                
            # Load into DataFrame and process local filters
            df = pd.DataFrame(food_places)
            
            # Keep items if they are within selected price levels OR unspecified (basement stalls)
            df = df[df['raw_price_level'].isin(allowed_google_tiers)]
            df = df.drop(columns=['raw_price_level'])
            
            if df.empty:
                st.warning("Places were found nearby, but they were filtered out by your current price range selections.")
                st.stop()
            
            # Highlight random pick
            st.success("### 🎲 Random Suggestion For Today:")
            random_pick = df.sample(n=1).iloc[0]
            st.markdown(f"**{random_pick['name'].title()}** — Rating: {random_pick['rating']} ⭐ ({random_pick['price_tier']})")
            st.caption(f"📍 {random_pick['address']}")
            
            st.write("---")
            
            # Show all options in a table
            st.subheader("All Nearby Options")
            st.dataframe(
                df,
                column_config={
                    "name": "Restaurant Name",
                    "rating": "Rating ⭐",
                    "price_tier": "Price Tier",
                    "address": "Location / Address",
                    "status": "Status"
                },
                use_container_width=True,
                hide_index=True
            )
