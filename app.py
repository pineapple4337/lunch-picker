import streamlit as st
import requests
import random

# =====================================================================
# 1. MOBILE-FIRST UI LAYOUT & CUSTOM CSS STYLING
# =====================================================================
st.set_page_config(page_title="lunch picker", page_icon="🍟", layout="centered")

# Inject clean sans-serif typography, vibrant colors, mobile cards, and custom slider CSS
st.markdown("""
    <style>
        /* Force font styles across the application */
        html, body, [data-testid="stWidgetLabel"] p {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }
        
        /* Vibrant gradient header */
        .app-title {
            font-size: 32px !important;
            font-weight: 800 !important;
            background: linear-gradient(45deg, #FF4B4B, #FF8333);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
            text-align: center;
        }
        
        .app-subtitle {
            color: #666666;
            font-size: 14px;
            text-align: center;
            margin-bottom: 20px;
        }
        
        /* 🎨 STREAMLIT SLIDER CSS FIX: Transforms the ugly white bubble handle into a clean circle */
        div[data-testid="stSlider"] [data-handle="true"] {
            background-color: #FF4B4B !important;
            border: 2px solid #ffffff !important;
            box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.2) !important;
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
        
        /* Mobile Stacked Card Containers */
        .food-card {
            background-color: #ffffff;
            border: 1px solid #eef2f6;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 6px;
        }
        
        .restaurant-name {
            font-size: 18px !important;
            font-weight: 700 !important;
            color: #1e293b;
            margin: 0;
            text-transform: capitalize;
        }
        
        .rating-badge {
            background-color: #fef3c7;
            color: #d97706;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 700;
        }
        
        .card-meta {
            font-size: 13px;
            color: #64748b;
            margin-bottom: 8px;
        }
        
        .tag-pill {
            display: inline-block;
            background-color: #f1f5f9;
            color: #475569;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-right: 4px;
            margin-bottom: 4px;
            text-transform: lowercase;
        }
        
        /* Interactive Highlight Banner for Random Selection */
        .winner-box {
            background: linear-gradient(135deg, #fff5f5 0%, #fff0ea 100%);
            border: 2px solid #ff4b4b;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 24px;
            text-align: center;
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

FUNAN_LAT, FUNAN_LNG = 1.2913, 103.8499

# The Comprehensive Google API V1 to SG-Crew Tag Translation Matrix
GOOGLE_TYPE_TRANSLATOR = {
    "japanese_restaurant": "japanese", "sushi_restaurant": "japanese", "ramen_restaurant": "japanese",
    "tonkatsu_restaurant": "japanese", "japanese_curry_restaurant": "japanese", "japanese_izakaya_restaurant": "japanese",
    "yakiniku_restaurant": "japanese", "yakitori_restaurant": "japanese",
    "korean_restaurant": "korean", "korean_barbecue_restaurant": "korean",
    "thai_restaurant": "thai / SE asian", "vietnamese_restaurant": "thai / SE asian", "cambodian_restaurant": "thai / SE asian",
    "indonesian_restaurant": "thai / SE asian", "malaysian_restaurant": "thai / SE asian", "burmese_restaurant": "thai / SE asian", "filipino_restaurant": "thai / SE asian",
    "chinese_restaurant": "chinese", "cantonese_restaurant": "chinese", "dim_sum_restaurant": "chinese",
    "dumpling_restaurant": "chinese", "chinese_noodle_restaurant": "chinese", "noodle_shop": "chinese",
    "hot_pot_restaurant": "chinese", "taiwanese_restaurant": "chinese", "soup_restaurant": "chinese",
    "fast_food_restaurant": "fast food", "meal_takeaway": "fast food", "hamburger_restaurant": "fast food",
    "chicken_restaurant": "fast food", "chicken_wings_restaurant": "fast food", "hot_dog_restaurant": "fast food",
    "sandwich_shop": "fast food", "snack_bar": "fast food", "burrito_restaurant": "fast food", "taco_restaurant": "fast food",
    "western_restaurant": "western", "steak_house": "western", "pizza_restaurant": "western", "bar_and_grill": "western",
    "american_restaurant": "western", "italian_restaurant": "western", "french_restaurant": "western",
    "spanish_restaurant": "western", "mediterranean_restaurant": "western", "european_restaurant": "western", "bistro": "western", "diner": "western",
    "cafe": "cafe & snacks", "coffee_shop": "cafe & snacks", "coffee_roastery": "cafe & snacks", "coffee_stand": "cafe & snacks",
    "tea_house": "cafe & snacks", "juice_shop": "cafe & snacks", "acai_shop": "cafe & snacks", "cafeteria": "cafe & snacks",
    "bakery": "cafe & snacks", "cake_shop": "cafe & snacks", "pastry_shop": "cafe & snacks", "dessert_restaurant": "cafe & snacks",
    "dessert_shop": "cafe & snacks", "ice_cream_shop": "cafe & snacks", "donut_shop": "cafe & snacks", "chocolate_shop": "cafe & snacks", "confectionery": "cafe & snacks",
    "vegan_restaurant": "vegetarian / vegan", "vegetarian_restaurant": "vegetarian / vegan", "salad_shop": "vegetarian / vegan"
}

if "radar_matches" not in st.session_state:
    st.session_state.radar_matches = None
if "executed_vibe" not in st.session_state:
    st.session_state.executed_vibe = ""

# =====================================================================
# 3. MOBILE INTERACTIVE CONTROLS
# =====================================================================
st.write("### 🎯 step 1: any cravings?")

# Generate base culinary choices from our translation map dictionary headers
unique_display_tags = sorted(list(set(GOOGLE_TYPE_TRANSLATOR.values())))

# Setup clean options with the new dynamic "Surprise Me" selection function built in
dropdown_options = unique_display_tags + ["🎲 surprise me! (random category)"]
selected_vibe = st.selectbox("what kinda meal are we looking for?", options=dropdown_options)

# Sidebar Max Scan Limit Controller
max_distance = st.sidebar.slider("scan radius (metres)", min_value=50, max_value=1000, value=300, step=50)

price_tier = st.select_slider(
    "max budget range",
    options=["$", "$$", "$$$", "$$$$"],
    value=("$", "$$")
)

# Convert display price choices to match Google API pricing strings
price_map = {"$": 1, "$$": 2, "$$$": 3, "$$$$": 4}
max_allowed_price = price_map[price_tier[1]]

# =====================================================================
# 4. LOGICAL AREA TEXT SEARCH WITH DYNAMIC CATEGORY PICKER
# =====================================================================
if st.button("📡 search!", use_container_width=True):
    with st.spinner("Analyzing building registry..."):
        
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.priceLevel,places.regularOpeningHours,places.types"
        }
        
        # 🎲 THE DYNAMIC SURPRISE OVERRIDE ENGINE:
        # Resolves the 20-result cap by rolling a randomized target array selection *before* the API execution call
        if selected_vibe == "🎲 Surprise Me! (Random Category)":
            target_vibe = random.choice(unique_display_tags)
        else:
            target_vibe = selected_vibe
            
        # Lock final execution tag choice into memory layout state for headers
        st.session_state.executed_vibe = target_vibe
        
        # Build logical query string targeted specifically to find active structural listings
        search_string = f"{target_vibe.lower()} joints in funan singapore"
            
        # Secure max_distance variable boundary layout setup
        search_radius = float(max_distance) if 'max_distance' in locals() else 300.0
            
        payload = {
            "textQuery": search_string,
            "locationBias": {
                "circle": {
                    "center": {
                        "latitude": FUNAN_LAT, 
                        "longitude": FUNAN_LNG
                    },
                    "radius": search_radius
                }
            }
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            places = response.json().get("places", [])
            processed_list = []
            
            for p in places:
                name = p.get("displayName", {}).get("text", "Unknown")
                address = p.get("formattedAddress", "Funan Mall")
                rating = p.get("rating", "N/A")
                
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
                
                # Programmatic evaluation mapping
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
                    "tags": list(tags)
                })
            
            # Apply strict local filters to verify downloaded arrays
            filtered_list = []
            for item in processed_list:
                if item["price_score"] > max_allowed_price:
                    continue
                if target_vibe not in item["tags"]:
                    continue
                filtered_list.append(item)
                
            st.session_state.radar_matches = filtered_list
        else:
            st.error(f"API Engine Error: {response.text}")

# =====================================================================
# 5. MOBILE RENDERING LAYER (CARDS & RANDOMIZER)
# =====================================================================
if st.session_state.radar_matches is not None:
    st.write("---")
    
    if len(st.session_state.radar_matches) == 0:
        st.warning(f"No spots matching '{st.session_state.executed_vibe}' found within budget/distance parameters. Try adjusting your sliders!")
    else:
        # Large Mobile-Friendly Randomizer Action Button
        if st.button("🎲 roll random selection", use_container_width=True):
            winner = random.choice(st.session_state.radar_matches)
            tag_pills = "".join([f'<span class="tag-pill">{t}</span>' for t in winner["tags"]])
            
            st.markdown(f"""
                <div class="winner-box">
                    <p style="color: #FF4B4B; font-weight: 800; font-size: 14px; margin: 0 0 4px 0; letter-spacing: 1px; text-transform: lowercase;">🎰 chosen option!</p>
                    <p class="restaurant-name" style="font-size: 24px !important;">{winner['name']}</p>
                    <p style="margin: 8px 0;">{tag_pills}</p>
                    <p style="font-size: 14px; color: #333333; margin: 0;"><b>rating:</b> {winner['rating']} ⭐ | <b>price:</b> {winner['price_tier']}</p>
                    <p style="font-size: 12px; color: #666666; margin-top: 6px;">{winner['status']}</p>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown(f'<h3 style="font-size: 20px; font-weight: bold; margin-bottom: 15px;">📋 {st.session_state.executed_vibe} results ({len(st.session_state.radar_matches)})</h3>', unsafe_allow_html=True)
        
        # Loop over filtered list and render interactive mobile dropdown modules
        for spot in st.session_state.radar_matches:
            pills_html = "".join([f'<span class="tag-pill">{tag}</span>' for tag in spot["tags"]])
            
            # Use an expander header that looks exactly like your clean card title layout
            expander_title = f"🥞 {spot['name'].title()}  |  {spot['rating']} ⭐"
            
            with st.expander(expander_title):
                st.markdown(f"""
                    <div style="padding: 5px 0px;">
                        <p style="font-size: 13px; color: #64748b; margin-bottom: 8px;">
                            <b>budget:</b> {spot['price_tier']} | <b>status:</b> {spot['status']}
                        </p>
                        <div style="margin-bottom: 12px;">
                            {pills_html}
                        </div>
                        <div style="background-color: #f8fafc; border-left: 3px solid #ff4b4b; padding: 10px; border-radius: 6px;">
                            <p style="font-size: 12px; color: #334155; margin: 0; font-family: monospace;">
                                📍 {spot['address'].lower()}
                            </p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
