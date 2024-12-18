import streamlit as st
import requests
import logging
from datetime import datetime
import random
from dataclasses import dataclass
from typing import List
import pytz
from functools import lru_cache

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

@dataclass
class Lift:
    name: str
    type: str
    capacity: int
    length: int
    vertical: int
    duration: int
    base_altitude: int
    top_altitude: int

@dataclass
class Slope:
    name: str
    difficulty: str
    length: int
    vertical: int
    area: str
    connects_to: List[str]
    access_lifts: List[str]
    night_skiing: bool

# Facts dictionary
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

class WeatherService:
    def __init__(self):
        self.valley_coords = (49.299, 19.949)
        self.mountain_coords = (49.232, 19.982)

    @lru_cache(maxsize=1)
    def get_weather(self):
        """Fetch weather with caching"""
        try:
            valley_weather = self._get_dummy_weather()["valley"]
            mountain_weather = self._get_dummy_weather()["mountain"]
            
            return {
                "valley": valley_weather,
                "mountain": mountain_weather
            }
        except Exception as e:
            logger.error(f"Weather fetch error: {e}")
            return self._get_dummy_weather()

    def _get_dummy_weather(self):
        """Fallback weather data"""
        return {
            "valley": {
                "temperature": 0,
                "conditions": "Schneefall",
                "wind_speed": 5,
                "snow": 10,
                "altitude": 850
            },
            "mountain": {
                "temperature": -5,
                "conditions": "Schneefall",
                "wind_speed": 15,
                "snow": 30,
                "altitude": 1987
            }
        }

class ZakopaneData:
    def __init__(self):
        self.lifts = {
            'kasprowy_cable_car': Lift(
                name='Kasprowy Wierch Seilbahn',
                type='Seilbahn',
                capacity=180,
                length=4300,
                vertical=936,
                duration=12,
                base_altitude=1027,
                top_altitude=1959
            ),
            'szymoszkowa_chair': Lift(
                name='Szymoszkowa Sessellift',
                type='Sessellift',
                capacity=2200,
                length=1300,
                vertical=160,
                duration=7,
                base_altitude=900,
                top_altitude=1060
            )
        }
        
        self.slopes = {
            'kasprowy_main': Slope(
                name='Kasprowy Hauptabfahrt',
                difficulty='Schwer',
                length=3200,
                vertical=900,
                area='Kasprowy Wierch',
                connects_to=[],
                access_lifts=['kasprowy_cable_car'],
                night_skiing=False
            ),
            'szymoszkowa_1': Slope(
                name='Szymoszkowa Hauptpiste',
                difficulty='Mittel',
                length=1300,
                vertical=160,
                area='Szymoszkowa',
                connects_to=[],
                access_lifts=['szymoszkowa_chair'],
                night_skiing=True
            )
        }

class RouteGenerator:
    def __init__(self, zakopane_data):
        self.data = zakopane_data

    def generate_daily_route(self, weather):
        """Generate daily route based on conditions"""
        start_slope = 'szymoszkowa_1' if weather['mountain']['temperature'] > -10 else 'kasprowy_main'
        return self._build_route(start_slope)

    def _build_route(self, start_slope):
        slope = self.data.slopes[start_slope]
        lifts = [self.data.lifts[lift_id] for lift_id in slope.access_lifts]
        
        total_length = slope.length
        total_vertical = slope.vertical
        total_time = sum(l.duration for l in lifts) + (slope.length / 200)  # Rough time estimate
        
        description = f"""🎿 Heute empfohlene Route:

📊 Routenübersicht:
• Gesamtlänge: {total_length}m
• Höhenmeter: {total_vertical}m
• Geschätzte Dauer: {int(total_time)} Minuten

🗺️ Routenverlauf:

1. {slope.name}
   • Schwierigkeit: {slope.difficulty}
   • Länge: {slope.length}m
   • Höhenmeter: {slope.vertical}m

   Aufstieg mit:"""
        
        for lift in lifts:
            description += f"""
   ⚡ {lift.name}
      - Typ: {lift.type}
      - Fahrzeit: {lift.duration} Min.
      - Höhenmeter: {lift.vertical}m"""
        
        return description

class ZakZakBot:
    def __init__(self):
        self.weather_service = WeatherService()
        self.zakopane_data = ZakopaneData()
        self.route_generator = RouteGenerator(self.zakopane_data)
        self.last_update = None

    def compose_daily_message(self):
        """Compose complete daily update message"""
        weather = self.weather_service.get_weather()
        route = self.route_generator.generate_daily_route(weather)
        
        # Get random fact
        all_facts = []
        for category in FACTS.values():
            all_facts.extend(category)
        fact = random.choice(all_facts)
        
        message = f"""🏔 ZakZak Daily Update ⛷️

🌨 Wetter:

📍 Tal ({weather['valley']['altitude']}m):
• Temperatur: {weather['valley']['temperature']}°C
• Bedingungen: {weather['valley']['conditions']}
• Schneehöhe: {weather['valley']['snow']}cm
• Wind: {weather['valley']['wind_speed']}km/h

🏔 Berg ({weather['mountain']['altitude']}m):
• Temperatur: {weather['mountain']['temperature']}°C
• Bedingungen: {weather['mountain']['conditions']}
• Schneehöhe: {weather['mountain']['snow']}cm
• Wind: {weather['mountain']['wind_speed']}km/h

{route}

💡 Fun Fact:
{fact}

Einen schönen Tag auf der Piste! ⛷️"""
        
        self.last_update = datetime.now(pytz.timezone('Europe/Warsaw'))
        return message

def add_copy_button(text):
    """Add a copy button for the message"""
    st.markdown(
        f"""
        <div class="preview-box">{text}</div>
        <button class="copy-button" onclick="
            navigator.clipboard.writeText(`{text}`);
            this.textContent='Kopiert!';
            setTimeout(() => this.textContent='In Zwischenablage kopieren', 2000);
        ">In Zwischenablage kopieren</button>
        """,
        unsafe_allow_html=True
    )

def main():
    st.title("ZakZak Daily ⛷️")
    
    # Initialize bot in session state if not exists
    if 'bot' not in st.session_state:
        st.session_state.bot = ZakZakBot()
    
    # Current conditions
    st.header("Aktuelle Bedingungen")
    
    try:
        weather = st.session_state.bot.weather_service.get_weather()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📍 Tal")
            st.write(f"Höhe: {weather['valley']['altitude']}m")
            st.write(f"🌡️ Temperatur: {weather['valley']['temperature']}°C")
            st.write(f"☁️ Bedingungen: {weather['valley']['conditions']}")
            st.write(f"❄️ Schneehöhe: {weather['valley']['snow']}cm")
            st.write(f"💨 Wind: {weather['valley']['wind_speed']}km/h")
        
        with col2:
            st.markdown("### 🏔 Berg")
            st.write(f"Höhe: {weather['mountain']['altitude']}m")
            st.write(f"🌡️ Temperatur: {weather['mountain']['temperature']}°C")
            st.write(f"☁️ Bedingungen: {weather['mountain']['conditions']}")
            st.write(f"❄️ Schneehöhe: {weather['mountain']['snow']}cm")
            st.write(f"💨 Wind: {weather['mountain']['wind_speed']}km/h")
        
    except Exception as e:
        st.error(f"Fehler beim Laden der Wetterdaten: {str(e)}")
    
    # Route and message preview
    st.header("Tages-Update")
    
    if st.button("Update generieren"):
        try:
            message = st.session_state.bot.compose_daily_message()
            st.session_state.preview_message = message
            st.session_state.last_update = datetime.now(pytz.timezone('Europe/Warsaw'))
        except Exception as e:
            st.error(f"Fehler beim Generieren des Updates: {str(e)}")
    
    # Display preview if available
    if 'preview_message' in st.session_state:
        add_copy_button(st.session_state.preview_message)
    
    # Sidebar information
    st.sidebar.header("Information")
    if 'last_update' in st.session_state:
        st.sidebar.write(f"Letztes Update: {st.session_state.last_update.strftime('%d.%m.%Y %H:%M')}")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
        ### Über ZakZak Daily
        Tägliche Updates über:
        - Wetterbedingungen
        - Empfohlene Skirouten
        - Interessante Fakten
    """)
    
    # Footer
    st.markdown("---")
    st.markdown("Made with ❄️ for Zakopane")

if __name__ == "__main__":
    main()
