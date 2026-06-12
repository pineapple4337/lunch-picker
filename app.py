import streamlit as st
import requests
import pandas as pd

# =====================================================================
# 1. SETUP APP LAYOUT & TITLE
# =====================================================================
st.set_page_config(page_title="Funan Food Radar", page_icon="🍔", layout="centered")
st.title("🍔 Funan Casual Food Radar")
st.write("Surfacing every fast-casual joint, basement stall, and student favorite around the building.")

# =====================================================================
# 2. SAFELY FETCH API KEY FROM STREAMLIT SECRETS
# =====================================================================
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("Please configure your GOOGLE_API_KEY in Streamlit secrets.")
    st.stop()

# Precise Funan Centerpoint Coordinates
FUNAN_LAT = 1.2913
FUNAN_LNG = 103.8499

# =====================================================================
# 3. SIDEBAR FILTERS
# =====================================================================
st.sidebar.header("Radar Filters")

# We use a tight 150m radius by default to force focus on the physical building structure
max_distance = st.sidebar.slider("Scan Radius (meters)", min_value=50, max_value=500, value=150, step=50)

price_tier = st.sidebar.select_slider(
    "Max Budget Tier",
    options=["$", "$$", "$$$", "$$$$"],
    value=("$", "$$")
)

# Mapping user choice to Google API schema constants
price_map = {
    "$": "PRICE_LEVEL_INEXPENSIVE", 
    "$$": "PRICE_LEVEL_MODERATE", 
    "$$$": "PRICE_LEVEL_EXPENSIVE", 
    "$$$$": "PRICE_LEVEL_VERY_EXPENSIVE"
}
selected_prices = [key for key in price_map if price_tier[0] <= key <= price_tier[1]]
allowed_google_tiers = [price_map[tier] for tier in selected_prices] + ["PRICE_LEVEL_UNSPECIFIED"]

# =====================================================================
# 4. FETCH DATA TRIGGER (THE DEEP MULTI-FLOOR RADAR)
# =====================================================================
if st.button("Scan All Floors & Perimeters 🎯"):
    with st.spinner("Running a deep multi-level radar sweep..."):
        
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.priceLevel,places.regularOpeningHours,places.types,nextPageToken"
        }
        
        payload = {
            "includedTypes": ["restaurant", "fast_food_restaurant", "cafe", "bakery", "meal_takeaway"],
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": FUNAN_LAT, "longitude": FUNAN_LNG},
                    "radius": float(max_distance)
                }
            },
            "maxResultCount": 20, # Pull 20 per page loop
            "rankPreference": "DISTANCE"
        }
        
        all_results = []
        
        # Loop up to 3 times to grab up to 60 options total (clearing out database bottlenecks)
        for page in range(3):
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                st.error(f"Google API Error ({response.status_code}): {response.text}")
                st.stop()
                
            data = response.json()
            page_results = data.get("places", [])
            all_results.extend(page_results)
            
            # Check if there are more places further up/out
            next_token = data.get("nextPageToken")
            if next_token:
                payload["pageToken"] = next_token
            else:
                break
                
        if not all_results:
            st.warning("No spots caught on the radar. Try bumping the scan radius slider higher!")
        else:
            food_places = []
            for place in all_results:
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
                
            # Load into DataFrame and eliminate potential pagination duplicates
            df = pd.DataFrame(food_places).drop_duplicates(subset=['name'])
            
            # Filter rows against budget constraints
            df = df[df['raw_price_level'].isin(allowed_google_tiers)]
            df = df.drop(columns=['raw_price_level'])
            
            if df.empty:
                st.warning("Eateries were found, but they don't match your current budget filter.")
                st.stop()
            
            # Show a random pick
            st.success("### 🎲 Random Suggestion For Today:")
            random_pick = df.sample(n=1).iloc[0]
            st.markdown(f"**{random_pick['name'].title()}** — Rating: {random_pick['rating']} ⭐ ({random_pick['price_tier']})")
            st.caption(f"📍 {random_pick['address']}")
            
            st.write("---")
            
            # Render clean data table
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
