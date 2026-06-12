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
# 4. FETCH DATA TRIGGER (THE UNRESTRICTED PERIMETER & VIP SWEEP)
# =====================================================================
if st.button("Scan All Floors & Perimeters 🎯"):
    with st.spinner("Running deep category sweeps of Funan..."):
        
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.priceLevel,places.regularOpeningHours,places.types"
        }
        
        # We split the query into parallel batches to break the 20-result barrier
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
                        # Boost this to 250m+ in the sidebar slider to capture upper levels safely
                        "radius": float(max_distance)
                    }
                },
                "maxResultCount": 20,
                "rankPreference": "DISTANCE"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                raw_results.extend(response.json().get("places", []))
        
        # 🌟 THE WINGSTOP SAFETY NET: 
        # If the proximity radar choked it out due to density, we run a quick direct query 
        # to pull it and stitch it right back into your app dynamically.
        text_url = "https://places.googleapis.com/v1/places:searchText"
        text_payload = {
            "textQuery": "wingstop funan",
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": FUNAN_LAT, "longitude": FUNAN_LNG},
                    "radius": 300.0
                }
            }
        }
        text_headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.priceLevel,places.regularOpeningHours,places.types"
        }
        
        text_resp = requests.post(text_url, json=text_payload, headers=text_headers)
        if text_resp.status_code == 200:
            vip_places = text_resp.json().get("places", [])
            raw_results.extend(vip_places) # Inject Wingstop manually if missing!

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
                
            # Convert to DataFrame and drop any duplicates from the cross-endpoint merges
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
