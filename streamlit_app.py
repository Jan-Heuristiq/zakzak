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

# Custom CSS
st.markdown("""
    <style>
    .main {
        background: linear-gradient(180deg, #FFFFFF 0%, #FFE5E5 50%, #FF9999 100%);
    }
    .stApp {
        background: linear-gradient(180deg, #FFFFFF 0%, #FFE5E5 50%, #FF9999 100%);
    }
    h1 {
        color: #1e3a8a !important;
    }
    .preview-box {
        background-color: #DCF8C6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        white-space: pre-wrap;
    }
    .copy-button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        margin-top: 10px;
    }
    .copy-button:hover {
        background-color: #45a049;
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
        
        return (route_message, detailed_route, {
            "total_length": total_length,
            "total_vertical": total_vertical,
            "estimated_time": estimated_time
        })

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
    """Display the message section with copy functionality"""
    message, detailed_route = st.session_state.composer.compose_message()
    
    st.code(message, language="text")
    
    if st.button("In Zwischenablage kopieren"):
        st.write("Nachricht in die Zwischenablage kopiert!", unsafe_allow_html=True)
    
    return detailed_route

def display_route_details(detailed_route: List[Dict]):
    """Display detailed route information"""
    st.markdown("### Vollständige Informationen zur Route")
    for i, route in enumerate(detailed_route, 1):
        with st.expander(f"{i}. {route['name']}"):
            st.write(f"Schwierigkeit: {route['difficulty']}")
            st.write(f"Länge: {route['length']}m")
            st.write(f"Höhenmeter: {route['vertical']}m")
            st.write("Aufstieg mit:")
            for lift in route['lifts']:
                st.write(f"• {lift}")

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
