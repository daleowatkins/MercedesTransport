import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import re
import base64
import os

# 1. Page Config
st.set_page_config(page_title="Mercedes-AMG Transport", page_icon="🏎️", layout="centered")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    /* 1. FORCE DARK MODE BACKGROUND */
    .stApp {
        background-color: #0e1117;
    }
    
    /* 2. FORCE FONT FAMILY */
    html, body, [class*="css"] {
        font-family: 'Corporate A BQ Light', 'Corporate A BQ', Arial, sans-serif !important;
    }
    
    /* 3. INPUT BOX FIX (Crucial for visibility) */
    /* Target the container of the input */
    div[data-baseweb="input"] {
        background-color: #262730 !important; /* Dark Grey Background */
        border: 1px solid #444 !important;
    }
    /* Target the text inside the input */
    input[type="text"] {
        color: white !important;
        -webkit-text-fill-color: white !important; /* Fix for some browsers */
        caret-color: #00D2BE; /* Teal cursor */
    }
    /* Target the label above the input */
    label {
        color: white !important;
    }

    /* 4. EXPANDER / PASSENGER NAME FIX */
    .streamlit-expanderHeader {
        background-color: #262730 !important; /* Dark Grey header */
        color: white !important; /* White Text */
        border: 1px solid #444;
        font-family: 'Corporate A BQ Light', sans-serif !important;
    }
    /* Fix hover state for expander */
    .streamlit-expanderHeader:hover {
        color: #00D2BE !important; /* Teal on hover */
    }
    div[data-testid="stExpander"] {
        border: none;
    }
    
    /* 5. GENERAL UI HIDING */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stSidebar"] {display: none;}

    /* 6. BANNER */
    .banner-container {
        width: 100%;
        height: 285px; 
        overflow: hidden;
        margin-bottom: 20px;
        border-radius: 10px;
    }
    .banner-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center;
    }
    
    /* 7. TEXT & COLORS */
    h1, h2, h3, h4, p, div, span {
        color: white !important;
    }
    h1, h3 {
        text-align: center !important;
        margin-top: 1rem;
    }
    
    .route-link {
        color: #00D2BE !important;
        font-weight: bold;
        text-decoration: none !important;
    }
    
    /* 8. BUTTONS */
    div.stButton > button {
        width: 100%;
        background-color: #00D2BE !important;
        color: black !important;
        border: none;
        font-weight: bold;
        font-family: 'Corporate A BQ Light', sans-serif !important;
    }
    div.stButton > button:hover {
        background-color: #A0F0E6 !important;
        color: black !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- MEMORY INITIALIZATION ---
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False
if 'booking_code' not in st.session_state:
    st.session_state.booking_code = ""
if 'navigate_to_route' not in st.session_state:
    st.session_state.navigate_to_route = False
if 'view_route_num' not in st.session_state:
    st.session_state.view_route_num = None

# --- NAVIGATION LOGIC ---
if st.session_state.navigate_to_route:
    st.session_state.navigate_to_route = False 
    st.switch_page("pages/Routes.py")

# 2. Load Data
@st.cache_data
def load_data():
    try:
        data = pd.read_csv("bookings.csv", dtype=str)
        data.columns = data.columns.str.strip()
        data['Code'] = data['Code'].ffill().str.strip().str.upper()
        
        if 'Direction' not in data.columns: data['Direction'] = "Both"
        if 'PickupTime' not in data.columns: data['PickupTime'] = "TBC"

        if 'Lat' in data.columns and 'Lon' in data.columns:
            data['Lat'] = pd.to_numeric(data['Lat'], errors='coerce')
            data['Lon'] = pd.to_numeric(data['Lon'], errors='coerce')
            
        return data
    except FileNotFoundError:
        return None

df = load_data()

# --- 3. HERO BANNER ---
def get_base64_image(image_path):
    if not os.path.exists(image_path):
        return ""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

banner_b64 = get_base64_image("banner.jpg")

if banner_b64:
    banner_html = f'<img src="data:image/jpg;base64,{banner_b64}">'
else:
    banner_html = '<img src="https://media.formula1.com/image/upload/f_auto,c_limit,w_1440,q_auto/f_auto/q_auto/content/dam/fom-website/2018-redesign-assets/team%20logos/mercedes%202024.png">'

st.markdown(f"""
    <div class="banner-container">
        {banner_html}
    </div>
    """, unsafe_allow_html=True)

if df is None:
    st.error("⚠️ System Error: 'bookings.csv' not found.")
    st.stop()

# 4. Login Form
st.markdown("<h3 style='text-align: center;'>Mercedes-AMG Petronas Event Transport</h3>", unsafe_allow_html=True)
st.write("Please enter your booking reference.")

def update_search():
    st.session_state.search_performed = True
    st.session_state.booking_code = st.session_state.widget_input.upper().strip()

with st.form(key='login_form'):
    st.text_input("Booking Code", key="widget_input")
    st.form_submit_button(label='Find My Booking', type="primary", on_click=update_search)

# 5. Results Logic
if st.session_state.search_performed:
    user_code = st.session_state.booking_code
    bookings = df[df['Code'] == user_code]

    if not bookings.empty:
        st.success(f"✅ Found {len(bookings)} passengers")
        
        for index, row in bookings.iterrows():
            # Header of expander (Passenger Name) now fixed by CSS
            unique_expander_key = f"expander_{user_code}_{index}"
            with st.expander(f"🎫 Passenger: {row['Name']}", expanded=True):
                
                # --- TRAVEL BADGE ---
                direction = str(row['Direction']).title()
                label_text = "Pickup:"
                show_time, show_return_msg = False, False
                badge_color, icon, pin_color = "blue", "🚌", "cadetblue"

                if "Both" in direction:
                    label_text, show_time, show_return_msg = "Pickup & Dropoff:", True, True
                    badge_color, icon, pin_color = "green", "🔄", "darkgreen" 
                elif "To" in direction:
                    label_text, show_time, show_return_msg = "Pickup:", True, False
                    badge_color, icon, pin_color = "orange", "➡️", "cadetblue"
                else:
                    label_text, show_time, show_return_msg = "Dropoff:", False, True
                    badge_color, icon, pin_color = "blue", "⬅️", "blue"

                st.markdown(f":{badge_color}[**{icon} Travel Direction: {direction}**]")
                st.divider()

                # --- DETAILS ---
                c1, c2 = st.columns([1.5, 2])
                with c1:
                    route_name = str(row['Route'])
                    match = re.search(r'\d+', route_name)
                    
                    st.write(f"**Route:** {route_name}")
                    
                    if match:
                        r_num = match.group()
                        def go_to_route(route_n=r_num):
                            st.session_state.view_route_num = route_n
                            st.session_state.navigate_to_route = True
                            
                        st.button(f"👉 View Route {r_num} Map", key=f"btn_route_{index}", on_click=go_to_route)
                        
                    st.write(f"**{label_text}** {row['Pickup']}")
                    
                    if show_time:
                        p_time = row.get('PickupTime')
                        if pd.isna(p_time): p_time = "TBC"
                        st.write(f"**⏱️ Time:** {p_time}")
                        
                        st.info("⚠️ Please ensure you are at your pickup point 5 mins before your time.")

                    if show_return_msg:
                        st.info("ℹ️ **Return:** All coaches depart venue at 01:00 AM.")

                    if pd.notna(row['MapLink']):
                        st.link_button("/// What 3 Words Link", row['MapLink'])
                        
                with c2:
                    lat, lon = row.get('Lat'), row.get('Lon')
                    if pd.notna(lat) and pd.notna(lon):
                        m = folium.Map(location=[lat, lon], zoom_start=16, control_scale=False, zoom_control=False)
                        folium.Marker(
                            [lat, lon], 
                            popup=row['Pickup'], 
                            icon=folium.Icon(color=pin_color, icon="bus", prefix="fa")
                        ).add_to(m)
                        
                        folium_static(m, height=200, width=350)
                    else:
                        st.info("🗺️ Map not available")

        # Footer
        st.divider()
        main_contact = bookings.iloc[0]['Name']
        subject = f"Mercedes Event Change Request: {user_code}"
        body = f"Hello Transport Team,%0D%0A%0D%0AI need to request a change for booking {user_code} (Contact: {main_contact})."
        
        st.markdown(
            f'<div style="text-align: center;"><a href="mailto:sambrough@countrylion.co.uk?subject={subject}&body={body}" '
            f'style="text-decoration:none; background-color:#00D2BE; color:black; font-weight:bold; padding:10px 20px; border-radius:5px;">'
            f'✉️ Request Amendment / Cancellation</a></div>', 
            unsafe_allow_html=True
        )

    else:
        st.error("❌ Code not found. Please check your reference.")
        if st.button("Reset Search"):
            st.session_state.search_performed = False
            st.rerun()
