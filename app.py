import streamlit as st
import requests
import random
import math
import feedparser

# =====================================================================
# 1. MOBILE-FIRST UI LAYOUT & DUSTY ROSE PASTEL THEME WITH PINK BG
# =====================================================================
st.set_page_config(page_title="lunch picker", page_icon="🍟", layout="centered")

st.markdown("""
    <style>
        /* Global typography and muted warm dark text */
        html, body, [data-testid="stWidgetLabel"] p {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            color: #5c4d50 !important;
        }
        
        /* Muted Dusty Rose Header Elements */
        .app-title {
            font-size: 34px !important;
            font-weight: 700 !important;
            color: #c97a8e !important;
            margin-bottom: 0px;
            text-align: center;
        }
        
        .app-subtitle {
            color: #ca948a;
            font-size: 14px;
            font-weight: 400;
            text-align: center;
            margin-bottom: 25px;
            letter-spacing: 0.5px;
        }
        
        /* Soft Pink Tag Pills */
        .tag-pill {
            display: inline-block;
            background-color: #fff5f6;
            color: #c97a8e;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 500;
            margin-right: 5px;
            margin-bottom: 5px;
            text-transform: lowercase;
            border: 1px solid #ffccd5;
        }
        
        /* Solid White Choice Container */
        .winner-box {
            background-color: #ffffff;
            border: 1px solid #ffccd5;
            border-radius: 12px;
            padding: 22px;
            margin-bottom: 24px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(255, 204, 213, 0.2);
        }
        
        /* Inline Status Banner Styling - Distinct Pop Out Edition */
        .status-banner {
            background-color: #fce1e4;
            border-left: 5px solid #c97a8e;
            border-top: 1px solid #f9ccd2;
            border-right: 1px solid #f9ccd2;
            border-bottom: 1px solid #f9ccd2;
            padding: 14px 12px;
            border-radius: 6px;
            text-align: center;
            color: #5c4d50;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.3px;
            margin-bottom: 25px;
            box-shadow: 0 2px 6px rgba(201, 122, 142, 0.1);
        }
        
        /* Expansion result cards styling */
        div[data-testid="stExpander"] {
            background-color: #ffffff !important;
            border: 1px solid #fff0f1 !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 8px rgba(255, 204, 213, 0.15) !important;
            margin-bottom: 8px !important;
        }
        
        /* COHESIVE SOLID PINK BUTTON STYLES */
        div.stButton > button:first-child, 
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #fff0f1 !important;
            color: #c97a8e !important;
            border: 1px solid #ffccd5 !important;
            padding: 10px 20px !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
            width: 100%;
        }
        
        div.stBlock:has(div.winner-box) + div.stButton > button,
        .stButton:nth-of-type(2) > button, 
        div[data-testid="element-container"] + div.stButton > button {
            background-color: #fce1e4 !important;
            color: #c97a8e !important;
            border: 1px solid #f9ccd2 !important;
        }
        
        .stButton>button:hover {
            transform: translateY(-1px) !important;
            opacity: 0.9 !important;
        }
        
        /* Forces expander titles to respect string line breaks beautifully on mobile viewports */
        div[data-testid="stExpander"] summary p {
            white-space: pre-line !important;
            line-height: 1.4 !important;
            padding-top: 4px !important;
            padding-bottom: 4px !important;
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
# 3. UTILITY MODULES: GEOMATH ENGINE & ESTIMATION TRICKS
# =====================================================================
def get_custom_coordinates(location_query):
    geo_url = "https://places.googleapis.com/v1/places:searchText"
    geo_headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.location"
    }
    
    query_lower = location_query.lower()
    international_keywords = ["stockholm", "kth", "sweden", "malaysia", "johor", "tokyo", "japan", "london", "paris", "europe"]
    local_anchors = ["condo", "singapore", "mrt", "mall", "road", "street", "hdb", "avenue", "clove"]
    
    if any(inter_word in query_lower for inter_word in international_keywords):
        full_query = location_query
    elif any(local_word in query_lower for local_word in local_anchors):
        full_query = f"{location_query} singapore" if "singapore" not in query_lower else location_query
    else:
        full_query = location_query
        
    geo_payload = {"textQuery": full_query}
    
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

def get_walking_time_string(distance_meters):
    minutes = math.ceil(distance_meters / 80)
    if minutes <= 1:
        return "~1 min walk"
    return f"~{minutes} mins walk"


def generate_discussion_topic():
    fallback_topics = [
        "⚖️ ETHICS: If a self-driving car must choose between hitting a group of elderly pedestrians or a single young child, how should the algorithm calculate the value of a life? Who bears moral responsibility?",
        "🏫 UNI LIFE: Is the modern university system primarily an institution for genuine intellectual growth, or has it just devolved into an expensive, multi-year compliance test to signal capability to employers?",
        "👁️ SOCIETY: If total global surveillance could permanently eradicate all violent crime overnight at the cost of absolute personal privacy, is that a trade-off a civilized society should accept?",
        "🧠 ETHICS: If memory-wiping technology existed to perfectly erase traumatic events or painful breakups without physical side effects, is it ethically sound to use it, or do we fundamentally need our pain to remain human?"
    ]
    
    try:
        from google import genai
    except ImportError:
        return random.choice(fallback_topics)
        
    try:
        # Pull from the standard primary outbound top stories feed which always stays functional
        feed = feedparser.parse("https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=10416")
        if not feed.entries:
            return random.choice(fallback_topics)
            
        random_entry = random.choice(feed.entries[:12])
        headline = random_entry.title
        article_link = random_entry.link
        
        if "GEMINI_API_KEY" not in st.secrets:
            return f"⚠️ Missing GEMINI_API_KEY in Streamlit Secrets!\n\nFound Headline: '{headline}'"
            
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        
        system_instruction = (
            "You are an academic debate moderator creating ultra-short icebreakers for university students. "
            "Your tone is direct, sharp, objective, and clear. Avoid dramatic, flowery, or bombastic language. "
            "You must strictly use British English spelling (e.g., analyse, behaviour, programme, characterised)."
        )
        
        prompt_payload = f"""
        Read this headline: "{headline}"
        
        Tasks:
        1. Write a single, brief, direct sentence identifying the core structural or ethical problem behind it. No filler words. Enforce strict lowercase.
        2. Formulate one highly succinct, open-ended debate question for university students. Keep it punchy and short. Enforce strict lowercase.
        
        Format your response exactly like this template (labels must remain lowercase), leave a line break between the headline and 'to ponder':
        📰 headline:
        {headline}

        to ponder:
        [Insert the single brief sentence here in all lowercase]
        
        question:
        [Insert the short debate question here in all lowercase]
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_payload,
            config={"system_instruction": system_instruction, "temperature": 0.85}
        )
        
        if response.text:
            return f"{response.text.strip()}\n\n🔗 Source: {article_link}"
            
    except Exception as e:
        st.sidebar.caption(f"🔧 debug diagnostic flag: {e}")
        
    return random.choice(fallback_topics)


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
if "show_inline_banner" not in st.session_state:
    st.session_state.show_inline_banner = False

# =====================================================================
# 4. MOBILE INTERACTIVE CONTROLS
# =====================================================================
st.write("### 📍 step 1: where u?")
starting_point = st.text_input("enter current location (e.g. bugis, chinatown)", placeholder="funan mall").strip()

st.write("### 🎯 step 2: any cravings?")
unique_display_tags = sorted(list(set(GOOGLE_TYPE_TRANSLATOR.values())))
dropdown_options = unique_display_tags + ["🎲 surprise me! (random category)"]
selected_vibe = st.selectbox("what kinda meal are we looking for?", options=dropdown_options)

# =====================================================================
# 5. API SEARCH WITH LOGICAL RESPONSE PROCESSING
# =====================================================================
if st.button("🔍 search!", use_container_width=True):
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
        
        matched_google_types = [
            g_type for g_type, vibe_string in GOOGLE_TYPE_TRANSLATOR.items() 
            if vibe_string == target_vibe
        ]
        
        or_joined_types = " OR ".join(matched_google_types)
        base_location = starting_point if starting_point else "funan mall"
        search_string = f"{or_joined_types} food near {base_location.lower()}"
        
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
                address = p.get("formattedAddress", "unlisted location")
                rating = p.get("rating", "N/A")
                
                spot_loc = p.get("location", {})
                spot_lat = spot_loc.get("latitude")
                spot_lng = spot_loc.get("longitude")
                
                meters_away = calculate_haversine_distance(target_lat, target_lng, spot_lat, spot_lng)
                
                raw_price_level = p.get("priceLevel", "PRICE_LEVEL_UNSPECIFIED")
                price_display = "price not listed"
                
                if "INEXPENSIVE" in raw_price_level:
                    price_display = "$"
                elif "MODERATE" in raw_price_level:
                    price_display = "$$"
                elif "EXPENSIVE" in raw_price_level:
                    price_display = "$$$"
                elif "VERY_EXPENSIVE" in raw_price_level:
                    price_display = "$$$$"
                
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
                    "price_tier": price_display,
                    "address": address,
                    "status": status,
                    "tags": list(tags),
                    "distance": meters_away
                })
            
            filtered_list = []
            for item in processed_list:
                if target_vibe not in item["tags"]:
                    continue
                if item["distance"] > 4000:
                    continue
                    
                filtered_list.append(item)
                
            filtered_list = sorted(filtered_list, key=lambda x: x["distance"])
            st.session_state.radar_matches = filtered_list
            
            st.markdown(
                f'<div style="text-align: center; width: 100%; margin-top: -8px; margin-bottom: 12px; clear: both;">'
                f'<p style="color: #c97a8e; font-size: 14px; font-weight: 600; margin: 0; display: inline-block; letter-spacing: 0.3px;">'
                f'{len(filtered_list)} options below 👇'
                f'</p>'
                f'</div>', 
                unsafe_allow_html=True
            )
        else:
            st.error(f"API Engine Error: {response.text}")

# =====================================================================
# 6. MOBILE RENDERING LAYER (CARDS & RANDOMISER)
# =====================================================================
if st.session_state.radar_matches is not None:
    
    if len(st.session_state.radar_matches) == 0:
        st.warning(f"no spots matching '{st.session_state.executed_vibe}' found within parameters")
    else:
        if st.button("🎲 roll random selection", use_container_width=True):
            winner = random.choice(st.session_state.radar_matches)
            tag_pills = "".join([f'<span class="tag-pill">{t}</span>' for t in winner["tags"]])
            walk_time = get_walking_time_string(winner['distance'])
            
            encoded_winner_query = requests.utils.quote(f"{winner['name']} {winner['address']}")
            winner_maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_winner_query}"
            
            st.markdown(f"""
                <div class="winner-box">
                    <p style="color: #c97a8e; font-weight: 700; font-size: 14px; margin: 0 0 4px 0; letter-spacing: 1px; text-transform: lowercase;">✨ chosen option!</p>
                    <p class="restaurant-name" style="font-size: 24px !important; color: #5c4d50; font-weight:700;">{winner['name'].lower()}</p>
                    <p style="margin: 8px 0;">{tag_pills}</p>
                    <p style="font-size: 14px; color: #ca948a; margin: 0;"><b>dist:</b> {winner['distance']}m ({walk_time}) | <b>rating:</b> {winner['rating']} ⭐ | <b>price:</b> {winner['price_tier']}</p>
                    <p style="font-size: 12px; color: #ca948a; margin-top: 5px;"><b>status:</b> {winner['status']}</p>
                    <div style="background-color: #fffafb; border: 1px dashed #ffccd5; padding: 10px; border-radius: 6px; margin-top: 10px; position: relative;">
                        <p style="font-size: 11px; color: #c97a8e; margin: 0 0 4px 0; font-family: monospace;">📍 {winner['address'].lower()}</p>
                        <a href="{winner_maps_url}" target="_blank" style="font-size: 11px; color: #ca948a; font-weight: 600; text-decoration: underline; display: inline-block; margin-top: 2px;">
                            🗺️ view on google maps
                        </a>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown(f'<h3 style="font-size: 20px; font-weight: bold; margin-bottom: 15px; color: #c97a8e;">📋 {st.session_state.executed_vibe} results ({len(st.session_state.radar_matches)})</h3>', unsafe_allow_html=True)
        
        for spot in st.session_state.radar_matches:
            pills_html = "".join([f'<span class="tag-pill">{tag}</span>' for tag in spot["tags"]])
            walk_time = get_walking_time_string(spot['distance'])
            
            expander_title = (
                f"📍 {spot['name'].lower()}\n"
                f"🚶 {spot['distance']}m ({walk_time})  |  {spot['rating']} ⭐  |  {spot['price_tier']}"
            )
            
            with st.expander(expander_title):
                encoded_query = requests.utils.quote(f"{spot['name']} {spot['address']}")
                maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_query}"
                
                st.markdown(f"""
                    <div style="padding: 5px 0px;">
                        <p style="font-size: 13px; color: #ca948a; margin-bottom: 8px;">
                            <b>budget:</b> {spot['price_tier']} | <b>status:</b> {spot['status']}
                        </p>
                        <div style="margin-bottom: 12px;">
                            {pills_html}
                        </div>
                        <div style="background-color: #fffafb; border-left: 3px solid #ffccd5; padding: 10px; border-radius: 6px; position: relative;">
                            <p style="font-size: 12px; color: #c97a8e; margin: 0 0 4px 0; font-family: monospace;">
                                📍 {spot['address'].lower()}
                            </p>
                            <a href="{maps_url}" target="_blank" style="font-size: 12px; color: #ca948a; font-weight: 600; text-decoration: underline; display: inline-block; margin-top: 2px;">
                                🗺️ view on google maps
                            </a>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

# =====================================================================
# 7. SIDEBAR FEATURE: MORNING TOPIC GENERATOR
# =====================================================================
with st.sidebar:
    st.markdown("<h2 style='color: #c97a8e;'>☕ morning discussion</h2>", unsafe_allow_html=True)
    
    if "current_topic" not in st.session_state:
        st.session_state.current_topic = "click the button below for a random topic!"
        
    if st.button("☕ brew morning topic", use_container_width=True):
        st.session_state.current_topic = generate_discussion_topic()
        
    st.markdown(
        f"""
        <div style="background-color: #ffffff; border: 1px solid #ffccd5; border-left: 4px solid #c97a8e; padding: 14px; border-radius: 8px; margin-top: 15px; box-shadow: 0 2px 6px rgba(255, 204, 213, 0.15); font-size: 13px; color: #5c4d50; white-space: pre-line; line-height: 1.6; font-family: -apple-system, sans-serif;">
            {st.session_state.current_topic}
        </div>
        """, 
        unsafe_allow_html=True
    )
