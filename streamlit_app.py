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

# Custom CSS with improved readability and performance
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
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
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

class WeatherService:
    def __init__(self):
        self.valley_coords = (49.299, 19.949)  # Zakopane center
        self.mountain_coords = (49.232, 19.982)  # Kasprowy Wierch
    
    @lru_cache(maxsize=1)
    def get_weather(self):
        """Fetch weather with caching to improve performance"""
        try:
            valley_weather = self._fetch_weather(*self.valley_coords, 850)
            mountain_weather = self._fetch_weather(*self.mountain_coords, 1987)
            
            return {
                "valley": valley_weather,
                "mountain": mountain_weather
            }
        except Exception as e:
            logger.error(f"Weather fetch error: {e}")
            return self._get_dummy_weather()
    
    def _fetch_weather(self, lat, lon, altitude):
        """Fetch weather for specific location"""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "weather_code", "wind_speed_10m"],
            "hourly": "snow_depth",
            "timezone": "Europe/Warsaw"
        }
        
        try:
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
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            raise

    def _get_weather_description(self, code):
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

# Initialize data classes (ZakopaneData and RouteGenerator) same as before
# [Previous code for these classes remains unchanged]

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
        fact = self.get_random_fact()
        
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

    @staticmethod
    def get_random_fact():
        """Get random fun fact about Zakopane"""
        # [Previous facts dictionary remains unchanged]
        return random.choice(facts["general"] + facts["culture"] + 
                           facts["sports"] + facts["nature"] + facts["cuisine"])

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
