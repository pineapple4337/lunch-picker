import streamlit as st
import googlemaps
import pandas as pd

# 1. Setup App Layout & Title
st.set_page_config(page_title="Funan Food Picker", page_icon="🍔", layout="centered")
st.title("🍔 Funan Food Picker")
st.write("Find where to eat with your office crew!")

# 2. Initialize Google Maps Client
# Securely fetch API key from Streamlit secrets
try:
    gmaps = googlemaps.Client(key=st.secrets["GOOGLE_API_KEY"])
except Exception:
    st.error("Please configure your Google API Key in secrets.")
    st.stop()

# Funan Coordinates
FUNAN_LAT = 1.2913
FUNAN_LNG = 103.8499

# 3. Sidebar Filters
st.sidebar.header("Filters")

cuisine = st.sidebar.text_input("Cuisine Type (e.g., Japanese, Mexican, Cafe)", value="")
max_distance = st.sidebar.slider("Max Walking Distance (meters)", min_value=100, max_value=2000, value=500, step=100)
price_tier = st.sidebar.select_slider(
    "Price Range",
    options=["$", "$$", "$$$", "$$$$"],
    value=("$", "$$")
)

# Convert price characters to Google API price levels (0 to 4)
price_map = {"$": 1, "$$": 2, "$$$": 3, "$$$$": 4}
min_price_num = price_map[price_tier[0]]
max_price_num = price_map[price_tier[1]]

# 4. Fetch Data Trigger
if st.button("Find Food Options 🎯"):
    with st.spinner("Searching for options near Funan..."):
        # Construct search query
        search_query = f"{cuisine} food restaurant" if cuisine else "food restaurant"
        
        # Call Google Places API
        try:
            places_result = gmaps.places_nearby(
                location=(FUNAN_LAT, FUNAN_LNG),
                radius=max_distance,
                keyword=search_query,
                type="restaurant",
                min_price=min_price_num,
                max_price=max_price_num
            )
        except googlemaps.exceptions.ApiError as e:
            st.error(f"Google API Error: {e}")
            st.stop()
            
        results = places_result.get("results", [])
        
        if not results:
            st.warning("No places found matching those specific filters. Try expanding your search!")
        else:
            # Process and format results
            food_places = []
            for place in results:
                # Calculate simple rough distance (or let Google handle sorting by distance)
                name = place.get("name")
                address = place.get("vicinity")
                rating = place.get("rating", "N/A")
                price_level = place.get("price_level", 0)
                status = "Open Now" if place.get("opening_hours", {}).get("open_now") else "Closed/Unknown"
                
                food_places.append({
                    "name": name.lower(),
                    "rating": rating,
                    "price": "$" * price_level if price_level else "n/a",
                    "address": address.lower(),
                    "status": status.lower()
                })
            
            # Convert to DataFrame for neat display
            df = pd.DataFrame(food_places)
            
            # Highlight a random choice for indecisive days
            st.success("### 🎲 Random Suggestion For Today:")
            random_pick = df.sample(n=1).iloc[0]
            st.markdown(f"**{random_pick['name'].title()}** — Rating: {random_pick['rating']} ⭐ ({random_pick['price']})")
            st.caption(f"📍 {random_pick['address']}")
            
            st.write("---")
            
            # Show all options in a clean table
            st.subheader("All Nearby Options")
            st.dataframe(
                df,
                column_config={
                    "name": "Restaurant Name",
                    "rating": "Rating ⭐",
                    "price": "Price Tier",
                    "address": "Location / Address",
                    "status": "Status"
                },
                use_container_width=True,
                hide_index=True
            )
