import streamlit as st
import logging
from datetime import datetime
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple
import pytz
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="ZakZak Daily",
    page_icon="⛷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern UI styling
st.markdown("""
    <style>
    /* Modern color scheme */
    :root {
        --primary-color: #005A94;
        --accent-color: #E63946;
        --light-bg: #F8F9FA;
        --dark-text: #2B2D42;
    }
    
    /* Base styles */
    .main {
        background-color: white;
        padding: 2rem;
    }
    
    .stApp {
        background-color: white;
    }
    
    /* Typography */
    h1 {
        color: var(--primary-color) !important;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        letter-spacing: -0.02em;
        margin-bottom: 2rem !important;
    }
    
    h3 {
        color: var(--dark-text) !important;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 600 !important;
        font-size: 1.5rem !important;
        margin-top: 2rem !important;
    }
    
    /* Card styling */
    .stMarkdown {
        background: var(--light-bg);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background-color: var(--primary-color) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #004A7C !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Code block styling */
    .stCodeBlock {
        background-color: white !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: white !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        font-weight: 500 !important;
        color: var(--dark-text) !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--light-bg) !important;
        padding: 2rem 1rem;
    }
    
    /* Stats cards */
    .stat-card {
        background-color: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #E5E7EB;
        margin-bottom: 1rem;
    }
    
    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--primary-color);
    }
    
    .stat-label {
        font-size: 0.875rem;
        color: #6B7280;
        margin-top: 0.25rem;
    }
    </style>
""", unsafe_allow_html=True)

# Constants
FACTS = {
    "general": [
        "Zakopane ist die höchstgelegene Stadt Polens",
        "Sie ist bekannt als die 'Winterhauptstadt Polens'",
        "Der Name bedeutet auf Polnisch 'vergraben'",
        "Die Stadt liegt auf einer Höhe von 800-1000 Metern"
    ],
    "sports": [
        "Die Skisprungschanze Wielka Krokiew ist eines der Wahrzeichen",
        "Der erste Skiclub Polens wurde 1907 in Zakopane gegründet"
    ],
    "nature": [
        "Die Stadt liegt am Fuß der Tatra",
        "Der Kasprowy Wierch (1.987 m) ist der bekannteste Skiberg"
    ]
}

SLOPES_DATA = [
    {"name": "Kasprowy Hauptabfahrt", "difficulty": "Schwer", "length": 3200, "vertical": 900},
    {"name": "Gąsienicowa Route", "difficulty": "Mittel", "length": 2800, "vertical": 700},
    {"name": "Goryczkowa Abfahrt", "difficulty": "Schwer", "length": 3000, "vertical": 850},
    {"name": "Szymoszkowa Hauptpiste", "difficulty": "Mittel", "length": 1300, "vertical": 160},
    {"name": "Harenda Family", "difficulty": "Leicht", "length": 2000, "vertical": 300},
    {"name": "Nosal Classic", "difficulty": "Mittel", "length": 650, "vertical": 172},
    {"name": "Goryczkowa West", "difficulty": "Schwer", "length": 2900, "vertical": 800},
    {"name": "Gąsienicowa Süd", "difficulty": "Mittel", "length": 2500, "vertical": 600},
    {"name": "Kasprowy Nord", "difficulty": "Schwer", "length": 3100, "vertical": 880},
    {"name": "Szymoszkowa Sport", "difficulty": "Mittel", "length": 1400, "vertical": 180}
]

LIFTS_DATA = [
    "Kasprowy Seilbahn",
    "Gąsienicowa Sessellift",
    "Goryczkowa Sessellift",
    "Szymoszkowa Sessellift",
    "Harenda Sessellift",
    "Nosal Schlepplift"
]

class WeatherService:
    def __init__(self):
        self.valley_coords = (49.299, 19.949)  # Zakopane center
        self.mountain_coords = (49.232, 19.982)  # Kasprowy Wierch
        self._valley_altitude = 850
        self._mountain_altitude = 1987

    def get_weather(self) -> Dict:
        """Get real weather data from Open-Meteo API"""
        try:
            valley_weather = self._fetch_weather(*self.valley_coords, self._valley_altitude)
            mountain_weather = self._fetch_weather(*self.mountain_coords, self._mountain_altitude)
            
            return {
                "valley": valley_weather,
                "mountain": mountain_weather
            }
        except Exception as e:
            logger.error(f"Weather fetch error: {e}")
            return self._get_fallback_weather()

    def _fetch_weather(self, lat: float, lon: float, altitude: int) -> Dict:
        """Fetch weather from Open-Meteo API"""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "weather_code", "wind_speed_10m"],
            "hourly": "snow_depth",
            "timezone": "Europe/Warsaw"
        }
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        return {
            "temperature": round(data["current"]["temperature_2m"]),
            "conditions": self._get_weather_description(data["current"]["weather_code"]),
            "wind_speed": round(data["current"]["wind_speed_10m"]),
            "snow": round(data.get("hourly", {}).get("snow_depth", [0])[0] * 100),
            "altitude": altitude
        }

    def _get_weather_description(self, code: int) -> str:
        """Convert weather code to German description"""
        descriptions = {
            0: "Klar",
            1: "Überwiegend klar",
            2: "Teilweise bewölkt",
            3: "Bedeckt",
            45: "Neblig",
            48: "Neblig mit Reif",
            51: "Leichter Nieselregen",
            53: "Mäßiger Nieselregen",
            55: "Starker Nieselregen",
            61: "Leichter Regen",
            63: "Mäßiger Regen",
            65: "Starker Regen",
            71: "Leichter Schneefall",
            73: "Mäßiger Schneefall",
            75: "Starker Schneefall",
            77: "Schneegriesel",
            85: "Leichte Schneeschauer",
            86: "Starke Schneeschauer",
            95: "Gewitter"
        }
        return descriptions.get(code, "Unbekannt")

    def _get_fallback_weather(self) -> Dict:
        """Fallback weather data if API fails"""
        return {
            "valley": {
                "temperature": 0,
                "conditions": "Schneefall",
                "wind_speed": 5,
                "snow": 10,
                "altitude": self._valley_altitude
            },
            "mountain": {
                "temperature": -5,
                "conditions": "Schneefall",
                "wind_speed": 15,
                "snow": 30,
                "altitude": self._mountain_altitude
            }
        }

class RouteGenerator:
    def generate_route(self) -> Tuple[str, List[Dict], Dict]:
        """Generate a route with message format and detailed information"""
        # Select 10 random slopes
        selected_slopes = random.sample(SLOPES_DATA, 10)
        
        # Calculate totals
        total_length = sum(slope["length"] for slope in selected_slopes)
        total_vertical = sum(slope["vertical"] for slope in selected_slopes)
        estimated_time = int(total_length / 200 + len(selected_slopes) * 5)
        
        # Generate simple route listing for message
        route_message = "\n".join(
            f"{i+1}. {slope['name']}" 
            for i, slope in enumerate(selected_slopes)
        )
        
        # Add random lifts to detailed information
        detailed_route = []
        for slope in selected_slopes:
            slope_info = slope.copy()
            slope_info["lifts"] = [random.choice(LIFTS_DATA)]
            detailed_route.append(slope_info)
        
        return route_message, detailed_route, {
            "total_length": total_length,
            "total_vertical": total_vertical,
            "estimated_time": estimated_time
        }

class MessageComposer:
    def __init__(self):
        self.weather_service = WeatherService()
        self.route_generator = RouteGenerator()
        self.webapp_url = "https://zak-zak-daily.streamlit.app"  # Replace with actual URL

    def compose_message(self) -> Tuple[str, List[Dict]]:
        """Compose the complete message and return with detailed route info"""
        weather = self.weather_service.get_weather()
        route_message, detailed_route, totals = self.route_generator.generate_route()
        
        # Get current date in German format
        current_date = datetime.now(pytz.timezone('Europe/Warsaw')).strftime('%d.%m.%Y')
        
        message = f"""🏔 Zakopane - {current_date} ⛷️

🌨 Wetter:
📍 Tal ({weather['valley']['altitude']}m):
• Temperatur: {weather['valley']['temperature']}°C • Bedingungen: {weather['valley']['conditions']} • Schneehöhe: {weather['valley']['snow']}cm • Wind: {weather['valley']['wind_speed']}km/h
🏔 Berg ({weather['mountain']['altitude']}m):
• Temperatur: {weather['mountain']['temperature']}°C • Bedingungen: {weather['mountain']['conditions']} • Schneehöhe: {weather['mountain']['snow']}cm • Wind: {weather['mountain']['wind_speed']}km/h

🎿 Heute empfohlene Route:
📊 Routenübersicht:
• Gesamtlänge: {totals['total_length']}m • Höhenmeter: {totals['total_vertical']}m • Anzahl Pisten: {len(detailed_route)} • Geschätzte Dauer: {totals['estimated_time']} Minuten

🗺️ Routenverlauf:
{route_message}

💡 Fun Fact:
{random.choice(sum(FACTS.values(), []))}

🔗 Vollständige Route hier: {self.webapp_url}

Lasst es krachen, ihr Skihasen ❄️🐰"""
        
        return message, detailed_route

def display_message_section():
    """Display the message section with modern styling"""
    message, detailed_route = st.session_state.composer.compose_message()
    
    st.markdown("""
        <div style='
            background-color: white;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #E5E7EB;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        '>
        """, 
        unsafe_allow_html=True
    )
    
    st.code(message, language="text")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("In Zwischenablage kopieren"):
            st.write("✓ Kopiert!", unsafe_allow_html=True)
    
    return detailed_route

def display_route_details(detailed_route: List[Dict]):
    """Display detailed route information with modern styling"""
    st.markdown("### Route Details")
    
    for i, route in enumerate(detailed_route, 1):
        with st.expander(f"{i}. {route['name']}", expanded=False):
            cols = st.columns([1, 1, 1])
            with cols[0]:
                st.markdown(f"**Schwierigkeit:** {route['difficulty']}")
            with cols[1]:
                st.markdown(f"**Länge:** {route['length']}m")
            with cols[2]:
                st.markdown(f"**Höhenmeter:** {route['vertical']}m")
            
            st.markdown("**Aufstieg mit:**")
            for lift in route['lifts']:
                st.markdown(f"• {lift}")

def main():
    # Get current date in German format
    current_date = datetime.now(pytz.timezone('Europe/Warsaw')).strftime('%d.%m.%Y')
    
    st.title(f"Zakopane - {current_date}")
    
    # Initialize composer in session state if not exists
    if 'composer' not in st.session_state:
        st.session_state.composer = MessageComposer()
    
    # Display main sections
    detailed_route = display_message_section()
    display_route_details(detailed_route)
    
    # Add refresh button
    if st.button("Neue Route generieren"):
        st.experimental_rerun()
    
    # Sidebar
    st.sidebar.header("Information")
    st.sidebar.markdown("""
        ### Über ZakZak Daily
        Tägliche Updates über:
        - Wetterbedingungen
        - Empfohlene Skirouten
        - Interessante Fakten
    """)

if __name__ == "__main__":
    main()
