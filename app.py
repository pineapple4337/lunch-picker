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
# 4. FETCH DATA TRIGGER (THE MULTI-CATEGORY RADAR SPLIT)
# =====================================================================
if st.button("Scan All Floors & Perimeters 🎯"):
    with st.spinner("Running deep category sweeps of Funan..."):
        
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            # REMOVED: 'nextPageToken' from the mask to fix the 400 error completely
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.priceLevel,places.regularOpeningHours,places.types"
        }
        
        # We split the query into two distinct parallel sweeps. 
        # This bypasses the 20-limit cap, yielding up to 40 combined results!
        category_batches = [
            ["restaurant", "fast_food_restaurant"],
            ["cafe", "bakery", "meal_takeaway"]
        ]
        
        raw_results = []
        
        for batch in category_batches:
            payload = {
                "includedTypes": batch,
                "locationRestriction": {
                    "circle": {
                        "center": {"latitude": FUNAN_LAT, "longitude": FUNAN_LNG},
                        "radius": float(max_distance)
                    }
                },
                "maxResultCount": 20, # Max allowed by Google per category array
                "rankPreference": "DISTANCE"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                batch_places = data.get("places", [])
                raw_results.extend(batch_places)
            else:
                st.error(f"Google API Error ({response.status_code}): {response.text}")
                st.stop()
                
        if not raw_results:
            st.warning("No spots caught on the radar. Try bumping the scan radius slider higher!")
        else:
            food_places = []
            for place in raw_results:
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
                
            # Convert to DataFrame and drop any duplicate stores that appeared in both lists
            df = pd.DataFrame(food_places).drop_duplicates(subset=['name'])
            
            # Apply local budget tier filters
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
            
            # Render clear data table
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
