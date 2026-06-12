import streamlit as st
import requests
import pandas as pd

# =====================================================================
# 1. SETUP APP LAYOUT & TITLE
# =====================================================================
st.set_page_config(page_title="Funan Food Radar", page_icon="🍔", layout="centered")
st.title("🍔 Funan Crew Food Radar")
st.write("Scan the building, filter out the noise, and lock down your crew's lunch pick.")

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
# 3. SIDEBAR FILTERS (INITIAL SETUP)
# =====================================================================
st.sidebar.header("Radar Configuration")

max_distance = st.sidebar.slider("Scan Radius (meters)", min_value=50, max_value=500, value=300, step=50)

price_tier = st.sidebar.select_slider(
    "Max Budget Tier",
    options=["$", "$$", "$$$", "$$$$"],
    value=("$", "$$")
)

price_map = {
    "$": "PRICE_LEVEL_INEXPENSIVE", 
    "$$": "PRICE_LEVEL_MODERATE", 
    "$$$": "PRICE_LEVEL_EXPENSIVE", 
    "$$$$": "PRICE_LEVEL_VERY_EXPENSIVE"
}
selected_prices = [key for key in price_map if price_tier[0] <= key <= price_tier[1]]
allowed_google_tiers = [price_map[tier] for tier in selected_prices] + ["PRICE_LEVEL_UNSPECIFIED"]

# Initialize session state to hold data across filter changes
if "raw_food_df" not in st.session_state:
    st.session_state.raw_food_df = None

# =====================================================================
# 4. STEP 1: SCAN THE BUILDING (API CALLS)
# =====================================================================
if st.button("📡 Scan All Funan Food Options"):
    with st.spinner("Sweeping all floors, basements, and perimeters..."):
        
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.priceLevel,places.regularOpeningHours,places.types"
        }
        
        category_batches = [
            ["restaurant", "fast_food_restaurant"],
            ["cafe", "bakery", "meal_takeaway"]
        ]
        
        raw_results = []
        
        # Parallel sweeps to bypass the 20-result limit
        for batch in category_batches:
            payload = {
                "includedTypes": batch,
                "locationRestriction": {
                    "circle": {
                        "center": {"latitude": FUNAN_LAT, "longitude": FUNAN_LNG},
                        "radius": float(max_distance)
                    }
                },
                "maxResultCount": 20,
                "rankPreference": "DISTANCE"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                raw_results.extend(response.json().get("places", []))
        
        # Wingstop target safety stitcher
        text_url = "https://places.googleapis.com/v1/places:searchText"
        text_payload = {
            "textQuery": "wingstop funan",
            "locationRestriction": {
                "circle": {"center": {"latitude": FUNAN_LAT, "longitude": FUNAN_LNG}, "radius": 300.0}
            }
        }
        text_headers = headers # Re-use same headers and field masks
        
        text_resp = requests.post(text_url, json=text_payload, headers=text_headers)
        if text_resp.status_code == 200:
            raw_results.extend(text_resp.json().get("places", []))

        if not raw_results:
            st.warning("No spots caught on radar. Try expanding your radius.")
        else:
            food_places = []
            for place in raw_results:
                name = place.get("displayName", {}).get("text", "unknown").lower()
                address = place.get("formattedAddress", "unknown").lower()
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
                
                # Create custom internal tag filters using address/name strings and API types
                tags = set()
                types_list = place.get("types", [])
                
                if "fast_food_restaurant" in types_list or "takeaway" in name or "stopp" in name:
                    tags.add("fast food")
                if "cafe" in types_list or "coffee" in name or "starbucks" in name:
                    tags.add("cafe & coffee")
                if "bakery" in types_list or "cookie" in name or "bread" in name:
                    tags.add("bakery & dessert")
                if any(x in name for x in ["japanese", "sushi", "ramen", "curry", "sukiya"]):
                    tags.add("japanese")
                if any(x in name for x in ["korean", "ajumma"]):
                    tags.add("korean")
                if any(x in name for x in ["noodle", "mala", "soup", "hotpot", "wok"]):
                    tags.add("chinese & noodles")
                if any(x in name for x in ["burger", "wings", "western"]):
                    tags.add("western")
                if any(x in name for x in ["stuff'd", "mexican", "taco", "kebab"]):
                    tags.add("mexican / wraps")
                
                # If no specific cuisine tag gets caught, fall back to a general tag
                if not tags:
                    if "cafe" in types_list or "bakery" in types_list:
                        tags.add("snacks & light bites")
                    else:
                        tags.add("other casual meals")
                
                food_places.append({
                    "name": name,
                    "rating": rating,
                    "price_tier": price_display,
                    "raw_price_level": raw_price,
                    "address": address,
                    "status": status,
                    "tags": list(tags)
                })
                
            # Drop duplicates and save to session state
            df = pd.DataFrame(food_places).drop_duplicates(subset=['name'])
            df = df[df['raw_price_level'].isin(allowed_google_tiers)]
            st.session_state.raw_food_df = df.drop(columns=['raw_price_level'])

# =====================================================================
# 5. STEP 2: REFINING WITH CUISINE & NOISE TAGS (MAIN INTERFACE)
# =====================================================================
if st.session_state.raw_food_df is not None:
    st.write("---")
    st.subheader("🎯 Step 2: Refine Your Crew's Cravings")
    
    # Extract every unique tag present in the downloaded dataset dynamically
    all_tags = sorted(list(set([tag for tags_list in st.session_state.raw_food_df['tags'] for tag in tags_list])))
    
    # Create the filter selection box on the main screen
    selected_tags = st.multiselect(
        "Choose tags to search within (Leave blank to see everything scanned):",
        options=all_tags,
        placeholder="e.g., fast food, japanese, western"
    )
    
    # Filter the DataFrame based on user selections
    if selected_tags:
        # Check if the list of tags for a restaurant overlaps with selected tags
        filtered_df = st.session_state.raw_food_df[
            st.session_state.raw_food_df['tags'].apply(lambda x: any(t in x for t in selected_tags))
        ]
    else:
        filtered_df = st.session_state.raw_food_df

    if filtered_df.empty:
        st.warning("No choices match that exact combo of tags. Try removing a filter tag!")
    else:
        # Clean tags column for elegant display mapping
        display_df = filtered_df.copy()
        display_df['tags'] = display_df['tags'].apply(lambda x: ", ".join(x))
        
        # =====================================================================
        # 6. STEP 3: THE SELECTION RANDOMIZER
        # =====================================================================
        st.write("---")
        if st.button("🎲 Choose For Us! (Roll Randomizer)"):
            random_pick = display_df.sample(n=1).iloc[0]
            st.success(f"### 🎰 Crew Pick: {random_pick['name'].title()}")
            st.markdown(f"**Rating:** {random_pick['rating']} ⭐ | **Budget:** {random_pick['price_tier']} | **Style:** `{random_pick['tags']}`")
            st.caption(f"📍 Location Info: {random_pick['address']}")
        
        # Display the filtered options grid right underneath
        st.subheader(f"Available Options ({len(display_df)} found)")
        st.dataframe(
            display_df,
            column_config={
                "name": "Restaurant Name",
                "rating": "Rating ⭐",
                "price_tier": "Price Tier",
                "address": "Location / Address",
                "status": "Status",
                "tags": "Tags / Cuisine"
            },
            use_container_width=True,
            hide_index=True
        )
