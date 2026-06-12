import streamlit as st
import requests
import random
import math

# =====================================================================
# 1. MOBILE-FIRST UI LAYOUT & CRISP PASTEL CSS STYLING
# =====================================================================
st.set_page_config(page_title="lunch picker", page_icon="🍟", layout="centered")

st.markdown("""
    <style>
        /* Global soothing text and clean typography */
        html, body, [data-testid=\"stWidgetLabel\"] p {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            color: #4a4e69 !important;
        }
        
        /* Clean solid pastel purple title */
        .app-title {
            font-size: 34px !important;
            font-weight: 700 !important;
            color: #b79ced !important;
            margin-bottom: 0px;
            text-align: center;
        }
        
        .app-subtitle {
            color: #9a8c98;
            font-size: 14px;
            font-weight: 400;
            text-align: center;
            margin-bottom: 25px;
            letter-spacing: 0.5px;
        }
        
        /* 🎨 CLEAN PASTEL SLIDER */
        div[data-testid=\"stSlider\"] [data-handle="true"] {
            background-color: #c8b6ff !important;
            border: 2px solid #ffffff !important;
            box-shadow: 0px 2px 5px rgba(200, 182, 255, 0.4) !important;
            border-radius: 50% !important;
            width: 18px !important;
            height: 18px !important;
            top: -1px !important;
        }
        
        div[data-testid=\"stSlider\"] [data-testid=\"stSliderTooltip\"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
        }
        
        /* Matte grey/purple lowercase tags */
        .tag-pill {
            display: inline-block;
            background-color: #e8e8e4;
            color: #6d597a;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 500;
            margin-right: 5px;
            margin-bottom: 5px;
            text-transform: lowercase;
            border: 1px solid #d8e2dc;
        }
        
        /* Solid soft blush pink box for choice winner */
        .winner-box {
            background-color: #fff0f1;
            border: 1px solid #ffccd5;
            border-radius: 12px;
            padding: 22px;
            margin-bottom: 24px;
            text-align: center;
        }
        
        /* Low contrast matte cards for search items */
        div[data-testid=\"stExpander\"] {
            background-color: #ffffff !important;
            border: 1px solid #f0efeb !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 8px rgba(216, 226, 220, 0.2) !important;
            margin-bottom: 8px !important;
        }
        
        /* 🛠️ INDIVIDUAL SOLID COLORS FOR BUTTONS */
        
        /* Button 1: Main Search (Solid Soft Lavender) */
        div.stButton > button:first-child, 
        div[data-testid=\"stFormSubmitButton\"] > button {
            background-color: #e8dff5 !important;
            color: #6d597a !important;
            border: 1px solid #dcd1eb !important;
            padding: 10px 20px !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
            width: 100%;
        }
        
        /* Button 2: Random Selection (Solid Soft Pink) */
        div.stBlock:has(div.winner-box) + div.stButton > button,
        .stButton:nth-of-type(2) > button, 
        div[data-testid=\"element-container\"] + div.stButton > button {
            background-color: #fce1e4 !important;
            color: #c97a8e !important;
            border: 1px solid #f9ccd2 !important;
        }
        
        .stButton>button:hover {
            transform: translateY(-1px) !important;
            opacity: 0.9 !important;
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
    if not lat1 or not lon1 or not lat2 or not lon2:
        return 0
    radius = 6371000
    
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(d_lat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return int(radius * c)

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
                    "radius": 1500.0
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
                
                spot_loc = p.get("location", {})
                spot_lat = spot_loc.get("latitude")
                spot_lng = spot_loc.get("longitude")
                
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
                    <p style="color: #ca948a; font-weight: 700; font-size: 14px; margin: 0 0 4px 0; letter-spacing: 1px; text-transform: lowercase;">✨ chosen option!</p>
                    <p class="restaurant-name" style="font-size: 24px !important; color: #4a4e69; font-weight:700;">{winner['name'].lower()}</p>
                    <p style="margin: 8px 0;">{tag_pills}</p>
                    <p style="font-size: 14px; color: #6d597a; margin: 0;"><b>dist:</b> {winner['distance']}m away | <b>rating:</b> {winner['rating']} ⭐</p>
                    <p style="font-size: 12px; color: #9a8c98; margin-top: 6px;">{winner['status']}</p>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown(f'<h3 style="font-size: 20px; font-weight: bold; margin-bottom: 15px; color: #6d597a;">📋 {st.session_state.executed_vibe} results ({len(st.session_state.radar_matches)})</h3>', unsafe_allow_html=True)
        
        for spot in st.session_state.radar_matches:
            pills_html = "".join([f'<span class="tag-pill">{tag}</span>' for tag in spot["tags"]])
            
            expander_title = f"✨ {spot['name'].lower()}  |  🚶 {spot['distance']}m  |  {spot['rating']} ⭐"
            
            with st.expander(expander_title):
                st.markdown(f"""
                    <div style="padding: 5px 0px;">
                        <p style="font-size: 13px; color: #9a8c98; margin-bottom: 8px;">
                            <b>budget:</b> {spot['price_tier']} | <b>status:</b> {spot['status']}
                        </p>
                        <div style="margin-bottom: 12px;">
                            {pills_html}
                        </div>
                        <div style="background-color: #f8f9fa; border-left: 3px solid #d8e2dc; padding: 10px; border-radius: 6px;">
                            <p style="font-size: 12px; color: #6d597a; margin: 0; font-family: monospace;">
                                📍 {spot['address'].lower()}
                            </p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
