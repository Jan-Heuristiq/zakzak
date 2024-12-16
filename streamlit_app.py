import streamlit as st
import requests
import datetime
import random
from datetime import datetime

# Page config
st.set_page_config(
    page_title="ZakZak Daily",
    page_icon="⛷️",
    layout="wide"
)

# Custom CSS for styling
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
    .icon-blue {
        color: #2563eb;
    }
    </style>
""", unsafe_allow_html=True)

class ZakZakBot:
    def __init__(self):
        # Zakopane coordinates
        self.latitude = 49.299
        self.longitude = 19.949
        self.webhook_url = st.secrets.get("PIPEDREAM_WEBHOOK", "YOUR_WEBHOOK_URL")
        
    def get_weather_description(self, wmo_code):
        """Convert WMO weather code to description in German"""
        wmo_codes = {
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
        return wmo_codes.get(wmo_code, "Unbekannt")
        
    def get_weather(self):
        """Fetch weather data from OpenMeteo"""
        try:
            url = f"https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "current": ["temperature_2m", "wind_speed_10m", "weather_code"],
                "hourly": "snow_depth",
                "timezone": "Europe/Warsaw"
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            # Get current conditions
            current = data["current"]
            
            # Get snow depth (take the most recent value)
            snow = data["hourly"]["snow_depth"][0]
            
            return {
                "temperature": round(current["temperature_2m"]),
                "conditions": self.get_weather_description(current["weather_code"]),
                "wind_speed": round(current["wind_speed_10m"]),
                "snow": round(snow * 100)  # Convert meters to cm
            }
        except Exception as e:
            st.error(f"Fehler beim Abrufen der Wetterdaten: {e}")
            return self.get_dummy_weather()
    
    def get_dummy_weather(self):
        """Fallback weather data"""
        return {
            "temperature": -2,
            "conditions": "Schneefall",
            "wind_speed": 8,
            "snow": 15
        }
    
    def get_ski_route(self, weather):
        """Get ski route recommendation based on weather"""
        routes = {
            'excellent': [
                {"name": "Kasprowy Wierch", "difficulty": "Fortgeschritten", "conditions": "Ausgezeichnet"},
                {"name": "Nosal", "difficulty": "Mittel", "conditions": "Perfekt"},
            ],
            'good': [
                {"name": "Kasprowy Wierch", "difficulty": "Fortgeschritten", "conditions": "Gut"},
                {"name": "Harenda", "difficulty": "Anfänger", "conditions": "Sehr gut"},
            ],
            'moderate': [
                {"name": "Nosal", "difficulty": "Mittel", "conditions": "Akzeptabel"},
                {"name": "Harenda", "difficulty": "Anfänger", "conditions": "Gut"},
            ],
            'poor': [
                {"name": "Harenda", "difficulty": "Anfänger", "conditions": "Mäßig"},
                {"name": "Szymoszkowa", "difficulty": "Anfänger", "conditions": "Befahrbar"},
            ]
        }
        
        # Determine conditions based on weather
        if weather['snow'] > 10 and -5 <= weather['temperature'] <= 2:
            condition = 'excellent'
        elif weather['snow'] > 5 and -10 <= weather['temperature'] <= 4:
            condition = 'good'
        elif weather['snow'] > 0 and -15 <= weather['temperature'] <= 5:
            condition = 'moderate'
        else:
            condition = 'poor'
            
        return random.choice(routes[condition])
    
    def get_fun_fact(self):
        """Get random fun fact about Zakopane"""
        facts = [
            "Zakopane ist die höchstgelegene Stadt Polens",
            "Sie ist bekannt als die 'Winterhauptstadt Polens'",
            "Der Name bedeutet auf Polnisch 'vergraben'",
            "Die typische Zakopane-Architektur wurde von Stanisław Witkiewicz entwickelt",
            "Die Skisprungschanze Wielka Krokiew ist eines der Wahrzeichen der Stadt",
            "Zakopane liegt am Fuße der Tatra, dem höchsten Gebirgszug der Karpaten",
            "Die Stadt hat etwa 27.000 Einwohner, empfängt aber jährlich über 2,5 Millionen Touristen",
            "Der höchste Berg in der Nähe ist der Kasprowy Wierch mit 1.987 Metern"
        ]
        return random.choice(facts)
    
    def compose_message(self, weather, route, fact):
        """Compose WhatsApp message"""
        return f"""🏔 ZakZak Daily Update ⛷️

🌨 Wetter:
• Temperatur: {weather["temperature"]}°C
• Bedingungen: {weather["conditions"]}
• Schneehöhe: {weather["snow"]}cm
• Wind: {weather["wind_speed"]}km/h

🎿 Heute empfohlen:
{route["name"]} - {route["conditions"]}
Schwierigkeitsgrad: {route["difficulty"]}

💡 Fun Fact:
{fact}

Einen schönen Tag auf der Piste! ⛷️"""
    
    def send_whatsapp_update(self):
        """Send update to WhatsApp via Pipedream webhook"""
        weather = self.get_weather()
        route = self.get_ski_route(weather)
        fact = self.get_fun_fact()
        message = self.compose_message(weather, route, fact)
        
        try:
            response = requests.post(
                self.webhook_url,
                json={"message": message}
            )
            return message if response.status_code == 200 else None
        except Exception as e:
            st.error(f"Fehler beim Senden der Nachricht: {e}")
            return None

def main():
    bot = ZakZakBot()
    
    # Header
    st.title("ZakZak Daily ⛷️")
    st.write(f"Letztes Update: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    # Get data
    weather = bot.get_weather()
    route = bot.get_ski_route(weather)
    fact = bot.get_fun_fact()
    
    # Create three columns
    col1, col2, col3 = st.columns(3)
    
    # Weather Card
    with col1:
        st.markdown("### ❄️ Wetterbedingungen")
        st.write(f"🌡️ Temperatur: {weather['temperature']}°C")
        st.write(f"☁️ Bedingungen: {weather['conditions']}")
        st.write(f"❄️ Schneehöhe: {weather['snow']}cm")
        st.write(f"💨 Wind: {weather['wind_speed']}km/h")
    
    # Ski Route Card
    with col2:
        st.markdown("### 🎿 Empfohlene Route")
        st.write(f"**{route['name']}**")
        st.write(f"Schwierigkeitsgrad: {route['difficulty']}")
        st.write(f"Bedingungen: {route['conditions']}")
    
    # Fun Fact Card
    with col3:
        st.markdown("### 💡 Fun Fact")
        st.write(fact)
    
    # WhatsApp message preview
    st.markdown("### 📱 WhatsApp Nachricht Vorschau")
    message = bot.compose_message(weather, route, fact)
    st.code(message, language="")
    
    # Manual trigger button
    if st.button("Update jetzt senden"):
        sent_message = bot.send_whatsapp_update()
        if sent_message:
            st.success("Nachricht erfolgreich gesendet!")
        else:
            st.error("Fehler beim Senden der Nachricht")

if __name__ == "__main__":
    main()
