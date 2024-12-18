import streamlit as st
import logging
from datetime import datetime
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple
import pytz

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

# Constants and configurations
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
        self._valley_altitude = 850
        self._mountain_altitude = 1987

    def get_weather(self) -> Dict:
        """Get weather data for valley and mountain"""
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
    def generate_route(self) -> Tuple[str, List[Dict]]:
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

    def compose_message(self) -> Tuple[str, List[Dict]]:
        """Compose the complete message and return with detailed route info"""
        weather = self.weather_service.get_weather()
        route_message, detailed_route, totals = self.route_generator.generate_route()
        
        message = f"""🏔 ZakZak Daily Update ⛷️
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

Einen schönen Tag auf der Piste! ⛷️"""
        
        return message, detailed_route

def display_message_section():
    """Display the message section with copy functionality"""
    message, detailed_route = st.session_state.composer.compose_message()
    
    st.markdown("### WhatsApp Nachricht")
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
    st.title("ZakZak Daily ⛷️")
    
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
