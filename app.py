import streamlit as st
import requests
import random
import math

# =====================================================================
# 1. MOBILE-FIRST UI LAYOUT & PASTEL PINK-PURPLE CSS STYLING
# =====================================================================
st.set_page_config(page_title="lunch picker", page_icon="🍟", layout="centered")

st.markdown("""
    <style>
        /* Force clean sans-serif typography across the app */
        html, body, [data-testid="stWidgetLabel"] p {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }
        
        /* Pastel Pink to Purple gradient title */
        .app-title {
            font-size: 34px !important;
            font-weight: 800 !important;
            background: linear-gradient(135deg, #ec4899, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
            text-align: center;
        }
        
        .app-subtitle {
            color: #8b5cf6;
            font-size: 14px;
            font-weight: 500;
            text-align: center;
            margin-bottom: 25px;
            letter-spacing: 0.5px;
        }
        
        /* 🎨 CUSTOM PASTEL SLIDER & SELECTION CONTROLS */
        div[data-testid="stSlider"] [data-handle="true"] {
            background-color: #a855f7 !important;
            border: 2px solid #ffffff !important;
            box-shadow: 0px 2px 6px rgba(168, 85, 247, 0.4) !important;
            border-radius: 50% !important;
            width: 20px !important;
            height: 20px !important;
            top: -2px !important;
        }
        
        div[data-testid="stSlider"] [data-testid="stSliderTooltip"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
        }
        
        /* Pastel Pink/Purple Tag Pills */
        .tag-pill {
            display: inline-block;
            background-color: #f3e8ff;
            color: #6b21a8;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            margin-right: 5px;
            margin-bottom: 5px;
            text-transform: lowercase;
            border: 1px solid #e9d5ff;
        }
        
        /* Soft Pastel Pink/Purple Highlight Box for Randomizer Winner */
        .winner-box {
            background: linear-gradient(135deg, #fdf2f8 0%, #f3e8ff 100%);
            border: 2px dashed #ec4899;
            border-radius: 16px;
            padding: 22px;
            margin-bottom: 24px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(236, 72, 153, 0.05);
        }
        
        /* Style adjustments for Streamlit's container widgets */
        div[data-testid="stExpander"] {
            background-color: #ffffff !important;
            border: 1px solid #fae8ff !important;
            border-radius: 10px !important;
            box-shadow: 0 2px 4px rgba(243, 232, 255, 0.3) !important;
            margin-bottom: 8px !important;
        }
        
        /* Styled buttons matching the palette */
        .stButton>button {
            background: linear-gradient(135deg, #f472b6, #c084fc) !important;
            color: white !important;
            border: none !important;
            padding: 10px 20px !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            transition: all 0.2s ease !important;
        }
        
        .stButton>button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(192, 132, 252, 0.4) !important;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="app-title">🍟 lunch picker</p>', unsafe_allow_html=True)
st.markdown('<p class="app-subtitle">what to eat!!!</p>', unsafe_allow_html=True)

# =====================================================================
# 2. KEY INTEGRATION & CONSTANTS
# =====================================================================
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("Missing GOOGLE_API_KEY in secrets configuration.")
    st.stop()

# =====================================================================
# 3. UTILITY MODULES: GEOMATH ENGINE
# =====================================================================
def get_custom_coordinates(location_query):
    geo_url = "https://places.googleapis.com/v1/places:searchText"
    geo_headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.location"
    }
    geo_payload = {"textQuery": f"{location_query} singapore"}
    
    try:
        geo_resp = requests.post(geo_url, json=geo_payload, headers=geo_headers, timeout=5.0)
        if geo_resp.status_code == 200:
            places_found = geo_resp.json().get("places", [])
            if places_found:
                loc = places_found[0].get("location", {})
                return loc.get("latitude"), loc.get("longitude")
    except Exception:
        pass
    return 1.2913, 103.8499

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """computes the absolute straight-line walking distance in meters completely for free"""
    if not lat1 or not lon1 or not lat2 or not lon2:
        return 0
    radius = 6371000 # earth radius in metres
    
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(d_lat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return int(radius * c)

# Google API Tag Translation Matrix
GOOGLE_TYPE_TRANSLATOR = {
    "japanese_restaurant": "japanese  🍣 🍜 🍱", "sushi_restaurant": "japanese  🍣 🍜 🍱", "ramen_restaurant": "japanese  🍣 🍜 🍱",
    "tonkatsu_restaurant": "japanese  🍣 🍜 🍱", "japanese_curry_restaurant": "japanese  🍣 🍜 🍱", "japanese_izakaya_restaurant": "japanese  🍣 🍜 🍱",
    "yakiniku_restaurant": "japanese  🍣 🍜 🍱", "yakitori_restaurant": "japanese  🍣 🍜 🍱",
    "korean_restaurant": "korean  🇰🇷 🍲 🥢", "korean_barbecue_restaurant": "korean  🇰🇷 🍲 🥢",
    "thai_restaurant": "thai / SE asian  🍛 🦐 🥘", "vietnamese_restaurant": "thai / SE asian  🍛 🦐 🥘", "cambodian_restaurant": "thai / SE asian  🍛 🦐 🥘",
    "indonesian_restaurant": "thai / SE asian  🍛 🦐 🥘", "malaysian_restaurant": "thai / SE asian  🍛 🦐 🥘", "burmese_restaurant": "thai / SE asian  🍛 🦐 🥘", "filipino_restaurant": "thai / SE asian  🍛 🦐 🥘",
    "chinese_restaurant": "chinese  🥟 🍜 🥡", "cantonese_restaurant": "chinese  🥟 🍜 🥡", "dim_sum_restaurant": "chinese  🥟 🍜 🥡",
    "dumpling_restaurant": "chinese  🥟 🍜 🥡", "chinese_noodle_restaurant": "chinese  🥟 🍜 🥡", "noodle_shop": "chinese  🥟 🍜 🥡",
    "hot_pot_restaurant": "chinese  🥟 🍜 🥡", "taiwanese_restaurant": "chinese  🥟 🍜 🥡", "soup_restaurant": "chinese  🥟 🍜 🥡",
    "fast_food_restaurant": "fast food  🍟 🍔 🍗", "meal_takeaway": "fast food  🍟 🍔 🍗", "hamburger_restaurant": "fast food  🍟 🍔 🍗",
    "chicken_restaurant": "fast food  🍟 🍔 🍗", "chicken_wings_restaurant": "fast food  🍟 🍔 🍗", "hot_dog_restaurant": "fast food  🍟 🍔 🍗",
    "sandwich_shop": "fast food  🍟 🍔 🍗", "snack_bar": "fast food  🍟 🍔 🍗", "burrito_restaurant": "fast food  🍟 🍔 🍗", "taco_restaurant": "fast food  🍟 🍔 🍗",
    "western_restaurant": "western  🍕 🥩 🍝", "steak_house": "western  🍕 🥩 🍝", "pizza_restaurant": "western  🍕 🥩 🍝", "bar_and_grill": "western  🍕 🥩 🍝",
    "american_restaurant": "western  🍕 🥩 🍝", "italian_restaurant": "western  🍕 🥩 🍝", "french_restaurant": "western  🍕 🥩 🍝",
    "spanish_restaurant": "western  🍕 🥩 🍝", "mediterranean_restaurant": "western  🍕 🥩 🍝", "european_restaurant": "western  🍕 🥩 🍝", "bistro": "western  🍕 🥩 🍝", "diner": "western  🍕 🥩 🍝",
    "cafe": "cafe & snacks  🧋 🍩 🍵", "coffee_shop": "cafe & snacks  🧋 🍩 🍵", "coffee_roastery": "cafe & snacks  🧋 🍩 🍵", "coffee_stand": "cafe & snacks  🧋 🍩 🍵",
    "tea_house": "cafe & snacks  🧋 🍩 🍵", "juice_shop": "cafe & snacks  🧋 🍩 🍵", "acai_shop": "cafe & snacks  🧋 🍩 🍵", "cafeteria": "cafe & snacks  🧋 🍩 🍵",
    "bakery": "cafe & snacks  🧋 🍩 🍵", "cake_shop": "cafe & snacks  🧋 🍩 🍵", "pastry_shop": "cafe & snacks  🧋 🍩 🍵", "dessert_restaurant": "cafe & snacks  🧋 🍩 🍵",
    "dessert_shop": "cafe & snacks  🧋 🍩 🍵", "ice_cream_shop": "cafe & snacks  🧋 🍩 🍵", "donut_shop": "cafe & snacks  🧋 🍩 🍵", "chocolate_shop": "cafe & snacks  🧋 🍩 🍵", "confectionery": "cafe & snacks  🧋 🍩 🍵",
    "vegan_restaurant": "vegetarian / salad  🥗 🥑 🥦", "vegetarian_restaurant": "vegetarian / salad  🥗 🥑 🥦", "salad_shop": "vegetarian / salad  🥗 🥑 🥦"
}

if "radar_matches" not in st.session_state:
    st.session_state.radar_matches = None
if "executed_vibe" not in st.session_state:
    st.session_state.executed_vibe = ""

# =====================================================================
# 4. MOBILE INTERACTIVE CONTROLS
# =====================================================================
st.write("### 📍 step 1: where u?")
starting_point = st.text_input("enter current location (e.g. bugis, chinatown)", placeholder="funan mall").strip()

st.write("### 🎯 step 2: any cravings?")
unique_display_tags = sorted(list(set(GOOGLE_TYPE_TRANSLATOR.values())))
dropdown_options = unique_display_tags + ["🎲 surprise me! (random category)"]
selected_vibe = st.selectbox("what kinda meal are we looking for?", options=dropdown_options)

price_tier = st.select_slider(
    "max budget range",
    options=["$", "$$", "$$$", "$$$$"],
    value=("$", "$$")
)

price_map = {"$": 1, "$$": 2, "$$$": 3, "$$$$": 4}
max_allowed_price = price_map[price_tier[1]]

# =====================================================================
# 5. LOGICAL AREA TEXT SEARCH WITH DISTANCE CALCULATION
# =====================================================================
if st.button("📡 search!", use_container_width=True):
    with st.spinner("loading..."):
        
        target_lat, target_lng = get_custom_coordinates(starting_point if starting_point else "funan mall")
        
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.priceLevel,places.regularOpeningHours,places.types,places.location"
        }
        
        if selected_vibe == "🎲 surprise me! (random category)":
            target_vibe = random.choice(unique_display_tags)
        else:
            target_vibe = selected_vibe
            
        st.session_state.executed_vibe = target_vibe
        clean_vibe_name = target_vibe.split('  ')[0]
        
        # 🛡️ Fallback fix to protect coordinate boundary integrity
        base_location = starting_point if starting_point else "funan mall"
        search_string = f"{clean_vibe_name} food near {base_location.lower()} singapore"
        
        payload = {
            "textQuery": search_string,
            "locationBias": {
                "circle": {
                    "center": {
                        "latitude": target_lat, 
                        "longitude": target_lng
                    },
                    "radius": 1500.0  # open default radius up to capturing roughly 2 MRT stops out
                }
            }
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            places = response.json().get("places", [])
            processed_list = []
            
            for p in places:
                name = p.get("displayName", {}).get("text", "Unknown")
                address = p.get("formattedAddress", "Singapore")
                rating = p.get("rating", "N/A")
                
                # Fetch restaurant coordinates from payload block
                spot_loc = p.get("location", {})
                spot_lat = spot_loc.get("latitude")
                spot_lng = spot_loc.get("longitude")
                
                # Run the math equation completely locally for free
                meters_away = calculate_haversine_distance(target_lat, target_lng, spot_lat, spot_lng)
                
                raw_price_level = p.get("priceLevel", "PRICE_LEVEL_UNSPECIFIED")
                price_numeric = 0
                price_display = "??? 💵"
                
                if "INEXPENSIVE" in raw_price_level:
                    price_numeric, price_display = 1, "$"
                elif "MODERATE" in raw_price_level:
                    price_numeric, price_display = 2, "$$"
                elif "EXPENSIVE" in raw_price_level:
                    price_numeric, price_display = 3, "$$$"
                elif "VERY_EXPENSIVE" in raw_price_level:
                    price_numeric, price_display = 4, "$$$$"
                
                tags = set()
                google_types = p.get("types", [])
                for g_type in google_types:
                    if g_type in GOOGLE_TYPE_TRANSLATOR:
                        tags.add(GOOGLE_TYPE_TRANSLATOR[g_type])
                
                if not tags:
                    tags.add("Casual Dining")
                    
                is_open = p.get("regularOpeningHours", {}).get("openNow", None)
                status = "🟢 open!" if is_open else "⚪ closed (i think)"
                
                processed_list.append({
                    "name": name,
                    "rating": rating,
                    "price_score": price_numeric,
                    "price_tier": price_display,
                    "address": address,
                    "status": status,
                    "tags": list(tags),
                    "distance": meters_away
                })
            
            filtered_list = []
            for item in processed_list:
                if item["price_score"] > max_allowed_price:
                    continue
                if target_vibe not in item["tags"]:
                    continue
                filtered_list.append(item)
                
            # Sort the list so the absolute closest spot is index 0
            filtered_list = sorted(filtered_list, key=lambda x: x["distance"])
                
            st.session_state.radar_matches = filtered_list
        else:
            st.error(f"API Engine Error: {response.text}")

# =====================================================================
# 6. MOBILE RENDERING LAYER (CARDS & RANDOMISER)
# =====================================================================
if st.session_state.radar_matches is not None:
    st.write("---")
    
    if len(st.session_state.radar_matches) == 0:
        st.warning(f"no spots matching '{st.session_state.executed_vibe}' found within budget/distance parameters")
    else:
        if st.button("🎲 roll random selection", use_container_width=True):
            winner = random.choice(st.session_state.radar_matches)
            tag_pills = "".join([f'<span class="tag-pill">{t}</span>' for t in winner["tags"]])
            
            st.markdown(f"""
                <div class="winner-box">
                    <p style="color: #ec4899; font-weight: 800; font-size: 14px; margin: 0 0 4px 0; letter-spacing: 1px; text-transform: lowercase;">🔮 chosen option!</p>
                    <p class="restaurant-name" style="font-size: 24px !important; color: #4c1d95;">{winner['name']}</p>
                    <p style="margin: 8px 0;">{tag_pills}</p>
                    <p style="font-size: 14px; color: #5b21b6; margin: 0;"><b>dist:</b> {winner['distance']}m away | <b>rating:</b> {winner['rating']} ⭐</p>
                    <p style="font-size: 12px; color: #701a75; margin-top: 6px;">{winner['status']}</p>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown(f'<h3 style="font-size: 20px; font-weight: bold; margin-bottom: 15px; color: #6b21a8;">📋 {st.session_state.executed_vibe} results ({len(st.session_state.radar_matches)})</h3>', unsafe_allow_html=True)
        
        for spot in st.session_state.radar_matches:
            pills_html = "".join([f'<span class="tag-pill">{tag}</span>' for tag in spot["tags"]])
            
            # Formatted headers to explicitly print out distance right away
            expander_title = f"✨ {spot['name'].title()}  |  🚶 {spot['distance']}m  |  {spot['rating']} ⭐"
            
            with st.expander(expander_title):
                st.markdown(f"""
                    <div style="padding: 5px 0px;">
                        <p style="font-size: 13px; color: #6b7280; margin-bottom: 8px;">
                            <b>budget:</b> {spot['price_tier']} | <b>status:</b> {spot['status']}
                        </p>
                        <div style="margin-bottom: 12px;">
                            {pills_html}
                        </div>
                        <div style="background-color: #faf5ff; border-left: 3px solid #d8b4fe; padding: 10px; border-radius: 6px;">
                            <p style="font-size: 12px; color: #5b21b6; margin: 0; font-family: monospace;">
                                📍 {spot['address'].lower()}
                            </p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
