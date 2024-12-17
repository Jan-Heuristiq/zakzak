import streamlit as st
import requests
import json
import logging
from datetime import datetime
import random
import schedule
import time
from dataclasses import dataclass
from typing import List, Dict
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class ZakopaneData:
    def __init__(self):
        # Initialize lifts
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
            # Add other lifts here...
        }
        
        # Initialize slopes
        self.slopes = {
            'kasprowy_gasienicowa': Slope(
                name='Kasprowy - Gąsienicowa',
                difficulty='Schwer',
                length=3200,
                vertical=900,
                area='Kasprowy Wierch',
                connects_to=['kasprowy_goryczkowa', 'gasienicowa_nizna'],
                access_lifts=['kasprowy_cable_car'],
                night_skiing=False
            ),
            # Add other slopes here...
        }

class WeatherService:
    def __init__(self):
        self.valley_coords = (49.299, 19.949)  # Zakopane center
        self.mountain_coords = (49.232, 19.982)  # Kasprowy Wierch
        
    def get_weather(self):
        """Fetch weather for both valley and mountain locations"""
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
        
        response = requests.get(url, params=params)
        data = response.json()
        
        return {
            "temperature": round(data["current"]["temperature_2m"]),
            "conditions": self._get_weather_description(data["current"]["weather_code"]),
            "wind_speed": round(data["current"]["wind_speed_10m"]),
            "snow": round(data["hourly"]["snow_depth"][0] * 100),
            "altitude": altitude
        }
    
    def _get_weather_description(self, code):
        """Convert weather code to German description"""
        descriptions = {
            0: "Klar",
            1: "Überwiegend klar",
            2: "Teilweise bewölkt",
            3: "Bedeckt",
            45: "Neblig",
            71: "Leichter Schneefall",
            73: "Mäßiger Schneefall",
            75: "Starker Schneefall"
        }
        return descriptions.get(code, "Unbekannt")
    
    def _get_dummy_weather(self):
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

class RouteGenerator:
    def __init__(self, zakopane_data):
        self.data = zakopane_data
    
    def generate_daily_route(self, weather):
        """Generate daily route based on conditions"""
        mountain_conditions = weather['mountain']
        
        # Select starting point based on conditions
        if (mountain_conditions['temperature'] > -5 and 
            mountain_conditions['temperature'] < 2 and 
            mountain_conditions['snow'] > 10):
            possible_starts = ['kasprowy_gasienicowa', 'kasprowy_goryczkowa']
        else:
            possible_starts = ['harenda_family', 'szymoszkowa_2']
        
        start_slope = random.choice(possible_starts)
        return self._build_route(start_slope)
    
    def _build_route(self, start_slope):
        route = []
        used_slopes = set()
        current_slope = start_slope
        
        while len(route) < 8:  # Maximum 8 slopes
            slope = self.data.slopes[current_slope]
            lifts = [self.data.lifts[lift_id] for lift_id in slope.access_lifts]
            
            route.append({
                'slope': slope,
                'lifts': lifts
            })
            
            used_slopes.add(current_slope)
            
            # Find next slope
            next_slopes = [s for s in slope.connects_to if s not in used_slopes]
            if not next_slopes or (len(route) >= 5 and random.random() < 0.3):
                break
                
            current_slope = random.choice(next_slopes)
        
        return self._format_route(route)
    
    def _format_route(self, route):
        total_length = sum(r['slope'].length for r in route)
        total_vertical = sum(r['slope'].vertical for r in route)
        total_time = sum(sum(l.duration for l in r['lifts']) for r in route)
        ski_time = total_length / 200  # Rough estimate
        
        description = f"""🎿 Heute empfohlene Route:

📊 Routenübersicht:
• Gesamtlänge: {total_length}m
• Höhenmeter: {total_vertical}m
• Anzahl Pisten: {len(route)}
• Geschätzte Dauer: {int(total_time + ski_time)} Minuten

🗺️ Routenverlauf:"""

        for i, r in enumerate(route, 1):
            description += f"""

{i}. {r['slope'].name}
   • Schwierigkeit: {r['slope'].difficulty}
   • Länge: {r['slope'].length}m
   • Höhenmeter: {r['slope'].vertical}m

   Aufstieg mit:"""
            
            for lift in r['lifts']:
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
    
    def get_fun_fact(self):
        facts = [
            "Zakopane ist die höchstgelegene Stadt Polens",
            "Die Stadt wird auch 'Winterhauptstadt Polens' genannt",
            "Der Name bedeutet auf Polnisch 'vergraben'",
            "Die typische Zakopane-Architektur wurde von Stanisław Witkiewicz entwickelt",
            "Die Skisprungschanze Wielka Krokiew ist eines der Wahrzeichen der Stadt"
        ]
        return random.choice(facts)
    
    def compose_daily_message(self):
        """Compose complete daily update message"""
        weather = self.weather_service.get_weather()
        route = self.route_generator.generate_daily_route(weather)
        fact = self.get_fun_fact()
        
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

def main():
    st.set_page_config(page_title="ZakZak Daily", page_icon="⛷️", layout="wide")
    
    # Initialize bot in session state
    if 'bot' not in st.session_state:
        st.session_state.bot = ZakZakBot()
    
    # Main interface
    st.title("ZakZak Daily ⛷️")
    
    # Current conditions
    st.header("Aktuelle Bedingungen")
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
    
    # Message preview
    st.header("Tägliche Update Vorschau")
    if st.button("Vorschau generieren"):
        message = st.session_state.bot.compose_daily_message()
        st.session_state.preview_message = message
    
    if 'preview_message' in st.session_state:
        st.markdown("""
            <style>
            .preview-box {
                background-color: #DCF8C6;
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
                font-family: 'Helvetica Neue', sans-serif;
                white-space: pre-wrap;
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<div class="preview-box">{st.session_state.preview_message}</div>', 
                   unsafe_allow_html=True)
    
    # Status information
    st.sidebar.header("Status")
    if st.session_state.bot.last_update:
        st.sidebar.write(f"Letztes Update: {st.session_state.bot.last_update.strftime('%d.%m.%Y %H:%M')}")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("Made with ❄️ for Zakopane")

if __name__ == "__main__":
    main()
