import streamlit as st
import pandas as pd
import folium
from streamlit.components.v1 import html as components_html
import base64
import requests
import polyline

# 1. Page Config
st.set_page_config(page_title="Route Details", page_icon="🗺️", layout="centered")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stSidebar"] {display: none;}

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

    h1, h2, h3 {text-align: center !important; color: white !important; margin-top: 1rem;}
    p, div, span {color: white !important;}

    .main-content {padding: 0rem 1rem; max-width: 800px; margin: 0 auto; text-align: center;}

    /* Petronas Teal Links */
    a {color: #00D2BE !important; text-decoration: none; font-weight: bold;}
    a:hover {text-decoration: underline; color: #A0F0E6 !important;}

    /* Petronas Teal Buttons */
    div.stButton > button {
        display: block; 
        margin: 0 auto; 
        background-color: #00D2BE !important; 
        color: black !important; 
        width: 100%;
        border: none;
    }

    table {margin-left: auto !important; margin-right: auto !important;}
    </style>
""", unsafe_allow_html=True)

# --- HERO BANNER ---
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""

banner_b64 = get_base64_image("banner.jpg")
if not banner_b64:
    banner_b64 = get_base64_image("../banner.jpg")

if banner_b64:
    banner_html = f'<img src="data:image/jpg;base64,{banner_b64}">'
else:
    banner_html = '<img src="https://media.formula1.com/image/upload/f_auto,c_limit,w_1440,q_auto/f_auto/q_auto/content/dam/fom-website/2018-redesign-assets/team%20logos/mercedes%202024.png">'

st.markdown(f"""<div class="banner-container">{banner_html}</div>""", unsafe_allow_html=True)

# --- MAIN CONTENT ---
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# --- ROUTE LOGIC ---
if "view_route_num" not in st.session_state:
    st.warning("⚠️ No route selected.")
    if st.button("⬅️ Back"):
        st.switch_page("app.py")
    st.stop()

route_num = st.session_state.view_route_num
filename = f"route{route_num}.csv"

st.title(f"Route {route_num} Details")

@st.cache_data
def get_osrm_route(coordinates):
    locs = [f"{lon},{lat}" for lat, lon in coordinates]
    loc_string = ";".join(locs)
    url = f"http://router.project-osrm.org/route/v1/driving/{loc_string}?overview=full&geometries=polyline"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            res = r.json()
            return polyline.decode(res['routes'][0]['geometry'])
    except:
        return None
    return None

try:
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        df = pd.read_csv(f"../{filename}")
    
    st.subheader("Route Map")
    
    if 'Lat' in df.columns and 'Lon' in df.columns:
        avg_lat = df['Lat'].mean()
        avg_lon = df['Lon'].mean()
        
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=10)
        
        points = []
        for _, row in df.iterrows():
            coords = [row['Lat'], row['Lon']]
            points.append(coords)
            folium.Marker(
                coords,
                popup=f"{row['Stop Name']}<br>{row['Time']}",
                tooltip=row['Stop Name'],
                icon=folium.Icon(color="cadetblue", icon="info-sign")
            ).add_to(m)
        
        if len(points) > 1:
            route_path = get_osrm_route(points)
            if route_path:
                # Use Petronas Teal for the line
                folium.PolyLine(route_path, color="#00D2BE", weight=5, opacity=0.8).add_to(m)
            else:
                folium.PolyLine(points, color="#00D2BE", weight=5, opacity=0.8, dash_array='5').add_to(m)

            m.fit_bounds(points)

        map_html = m._repr_html_()
        components_html(
            f"""
            <div style="display:flex; justify-content:center; width:100%;">
                <div style="width:700px;">
                    {map_html}
                </div>
            </div>
            """,
            height=450
        )
        
    else:
        st.warning("Map coordinates missing.")

    # --- TIMETABLE ---
    st.divider()
    st.subheader(f"Timetable")
    
    display_df = df[['Stop Name', 'Time']].copy()
    if 'W3W' in df.columns:
        display_df['Location'] = df['W3W'].apply(
            lambda x: f"<a href='https://w3w.co/{str(x).replace('///', '')}' target='_blank'>{x}</a>"
        )
    
    table_html = display_df.to_html(escape=False, index=False)
    st.markdown(f"""<div style="display: flex; justify-content: center; width: 100%;">{table_html}</div>""", unsafe_allow_html=True)

except FileNotFoundError:
    st.info(f"Route data for Route {route_num} is coming soon.")

st.divider()

if st.button("⬅️ Back to Ticket Search"):
    st.switch_page("app.py")

st.markdown('</div>', unsafe_allow_html=True)