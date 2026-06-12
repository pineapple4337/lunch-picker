import streamlit as st
import requests
import pandas as pd

# =====================================================================
# 1. SETUP APP LAYOUT & TITLE
# =====================================================================

st.set_page_config(
    page_title="Funan Crew Food Radar",
    page_icon="🍔",
    layout="centered"
)

st.title("🍔 Funan Crew Food Radar")
st.write(
    "Scan the building, filter out the noise, and lock down your crew's lunch pick."
)

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

# The Definitive Google API V1 to SG-Crew Tag Translation Matrix
GOOGLE_TYPE_TRANSLATOR = {
    # Japanese
    "japanese_restaurant": "Japanese",
    "sushi_restaurant": "Japanese",
    "ramen_restaurant": "Japanese",
    "tonkatsu_restaurant": "Japanese",
    "japanese_curry_restaurant": "Japanese",
    "japanese_izakaya_restaurant": "Japanese",
    "yakiniku_restaurant": "Japanese",
    "yakitori_restaurant": "Japanese",

    # Korean
    "korean_restaurant": "Korean",
    "korean_barbecue_restaurant": "Korean",

    # Thai & Vietnamese
    "thai_restaurant": "Thai / SE Asian",
    "vietnamese_restaurant": "Thai / SE Asian",
    "cambodian_restaurant": "Thai / SE Asian",

    # Chinese & Noodles
    "chinese_restaurant": "Chinese & HK Mains",
    "cantonese_restaurant": "Chinese & HK Mains",
    "dim_sum_restaurant": "Chinese & HK Mains",
    "dumpling_restaurant": "Chinese & HK Mains",
    "chinese_noodle_restaurant": "Chinese & HK Mains",
    "noodle_shop": "Chinese & HK Mains",
    "hot_pot_restaurant": "Chinese & HK Mains",
    "taiwanese_restaurant": "Chinese & HK Mains",

    # Fast Food & Quick Bites
    "fast_food_restaurant": "Fast Food",
    "meal_takeaway": "Fast Food",
    "hamburger_restaurant": "Fast Food",
    "chicken_restaurant": "Fast Food",
    "chicken_wings_restaurant": "Fast Food",
    "hot_dog_restaurant": "Fast Food",

    # Western, Grills & Cafes
    "western_restaurant": "Western & Grills",
    "steak_house": "Western & Grills",
    "pizza_restaurant": "Western & Grills",
    "bar_and_grill": "Western & Grills",
    "american_restaurant": "Western & Grills",
    "italian_restaurant": "Western & Grills",

    # Healthy & Wraps
    "mexican_restaurant": "Healthy Bowls & Wraps",
    "burrito_restaurant": "Healthy Bowls & Wraps",
    "taco_restaurant": "Healthy Bowls & Wraps",
    "tex_mex_restaurant": "Healthy Bowls & Wraps",
    "salad_shop": "Healthy Bowls & Wraps",
    "sandwich_shop": "Healthy Bowls & Wraps",

    # Cafes & Coffee Shops
    "cafe": "Cafe & Coffee",
    "coffee_shop": "Cafe & Coffee",
    "coffee_roastery": "Cafe & Coffee",
    "tea_house": "Cafe & Coffee",
    "juice_shop": "Cafe & Coffee",
    "acai_shop": "Cafe & Coffee",

    # Bakeries & Desserts
    "bakery": "Bakery & Dessert",
    "cake_shop": "Bakery & Dessert",
    "pastry_shop": "Bakery & Dessert",
    "dessert_restaurant": "Bakery & Dessert",
    "dessert_shop": "Bakery & Dessert",
    "ice_cream_shop": "Bakery & Dessert",
    "donut_shop": "Bakery & Dessert",

    # Dietary Specific
    "vegan_restaurant": "Vegetarian / Vegan",
    "vegetarian_restaurant": "Vegetarian / Vegan"
}

# Price Icon Conversion Map
PRICE_ICON_MAP = {
    "PRICE_LEVEL_INEXPENSIVE": "$",
    "PRICE_LEVEL_MODERATE": "$$",
    "PRICE_LEVEL_EXPENSIVE": "$$$",
    "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$"
}

# =====================================================================
# 3. INTERACTIVE SEARCH FILTERS (MAIN SCREEN & SIDEBAR)
# =====================================================================

st.sidebar.header("Radar Configuration")

max_distance = st.sidebar.slider(
    "Scan Radius (meters)",
    min_value=50,
    max_value=1000,
    value=300,
    step=50
)

price_tier = st.sidebar.select_slider(
    "Max Budget Tier",
    options=["$", "$$", "$$$", "$$$$"],
    value=("$", "$$")
)

selected_prices = [
    key
    for key in PRICE_ICON_MAP
    if PRICE_ICON_MAP[key] in [
        t
        for t in PRICE_ICON_MAP
        if price_tier[0] <= PRICE_ICON_MAP[t] <= price_tier[1]
    ]
]

allowed_google_tiers = selected_prices + ["PRICE_LEVEL_UNSPECIFIED"]

# UI STEP 1: Choose Cuisines BEFORE Searching to prevent the 20-result bottleneck

st.subheader("🎯 Step 1: Select Your Crew's Cravings")

available_cuisines = sorted(
    list(set(GOOGLE_TYPE_TRANSLATOR.values()))
)

selected_tags = st.multiselect(
    "Select target styles (Leave blank to scan for general meals):",
    options=available_cuisines,
    placeholder="e.g., Fast Food, Japanese, Thai / SE Asian"
)

# Reverse map user-friendly tags to Google types

target_google_types = []

if selected_tags:
    for g_type, crew_tag in GOOGLE_TYPE_TRANSLATOR.items():
        if crew_tag in selected_tags:
            target_google_types.append(g_type)
else:
    target_google_types = [
        "restaurant",
        "fast_food_restaurant",
        "cafe",
        "bakery",
        "meal_takeaway"
    ]

# Session state

if "raw_food_df" not in st.session_state:
    st.session_state.raw_food_df = None

# =====================================================================
# 4. STEP 2: SCAN THE PERIMETER WITH FILTERS APPLIED
# =====================================================================

if st.button("📡 Scan Perimeter Using Selected Filters"):

    with st.spinner(
        "Hunting down specific matching spots up to 1km out..."
    ):

        url = "https://places.googleapis.com/v1/places:searchNearby"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": (
                "places.displayName,"
                "places.formattedAddress,"
                "places.rating,"
                "places.priceLevel,"
                "places.regularOpeningHours,"
                "places.types"
            )
        }

        # Split target types into manageable batches

        batch_size = 3

        type_batches = [
            target_google_types[i:i + batch_size]
            for i in range(
                0,
                len(target_google_types),
                batch_size
            )
        ]

        raw_results = []

        for batch in type_batches:

            payload = {
                "includedTypes": batch,
                "locationRestriction": {
                    "circle": {
                        "center": {
                            "latitude": FUNAN_LAT,
                            "longitude": FUNAN_LNG
                        },
                        "radius": float(max_distance)
                    }
                },
                "maxResultCount": 20,
                "rankPreference": "DISTANCE"
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                raw_results.extend(
                    response.json().get("places", [])
                )

        # Wingstop fallback

        if (
            not selected_tags
            or any(
                t in selected_tags
                for t in ["Fast Food", "Western & Grills"]
            )
        ):

            text_url = (
                "https://places.googleapis.com/v1/places:searchText"
            )

            text_payload = {
                "textQuery": "wingstop funan",
                "locationRestriction": {
                    "circle": {
                        "center": {
                            "latitude": FUNAN_LAT,
                            "longitude": FUNAN_LNG
                        },
                        "radius": 300.0
                    }
                }
            }

            text_resp = requests.post(
                text_url,
                json=text_payload,
                headers=headers
            )

            if text_resp.status_code == 200:
                raw_results.extend(
                    text_resp.json().get("places", [])
                )

        if not raw_results:

            st.warning(
                "No spots caught on radar with those filters. "
                "Try widening your radius slider!"
            )

            st.session_state.raw_food_df = None

        else:

            food_places = []

            for place in raw_results:

                name = (
                    place.get("displayName", {})
                    .get("text", "unknown")
                    .lower()
                )

                address = (
                    place.get("formattedAddress", "unknown")
                    .lower()
                )

                rating = place.get("rating", "n/a")

                is_open = (
                    place.get("regularOpeningHours", {})
                    .get("openNow", None)
                )

                status = (
                    "open now"
                    if is_open
                    else "closed/unknown"
                )

                raw_price = place.get(
                    "priceLevel",
                    "PRICE_LEVEL_UNSPECIFIED"
                )

                tags = set()

                google_types = place.get("types", [])

                for g_type in google_types:
                    if g_type in GOOGLE_TYPE_TRANSLATOR:
                        tags.add(
                            GOOGLE_TYPE_TRANSLATOR[g_type]
                        )

                if not tags:
                    tags.add("Other Casual Meals")

                food_places.append(
                    {
                        "name": name,
                        "rating": rating,
                        "price_tier": PRICE_ICON_MAP.get(
                            raw_price,
                            "unspecified"
                        ),
                        "raw_price_level": raw_price,
                        "address": address,
                        "status": status,
                        "tags": list(tags)
                    }
                )

            df = (
                pd.DataFrame(food_places)
                .drop_duplicates(subset=["name"])
            )

            df = df[
                df["raw_price_level"].isin(
                    allowed_google_tiers
                )
            ]

            st.session_state.raw_food_df = df.drop(
                columns=["raw_price_level"]
            )

# =====================================================================
# 5. STEP 3: RENDER FILTERED RESULTS
# =====================================================================

if st.session_state.raw_food_df is not None:

    display_df = st.session_state.raw_food_df.copy()

    display_df["tags"] = display_df["tags"].apply(
        lambda x: ", ".join(x)
    )

    # =================================================================
    # 6. STEP 3: THE SELECTION RANDOMIZER
    # =================================================================

    st.write("---")

    if st.button("🎲 Choose For Us! (Roll Randomizer)"):

        random_pick = display_df.sample(n=1).iloc[0]

        st.success(
            f"### 🎰 Crew Pick: "
            f"{random_pick['name'].title()}"
        )

        st.markdown(
            f"**Rating:** {random_pick['rating']} ⭐ | "
            f"**Budget:** {random_pick['price_tier']} | "
            f"**Style:** `{random_pick['tags']}`"
        )

        st.caption(
            f"📍 Location Info: "
            f"{random_pick['address']}"
        )

    st.subheader(
        f"Available Options ({len(display_df)} found)"
    )

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
