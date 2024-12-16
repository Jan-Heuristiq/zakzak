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
        self.weather_api_key = st.secrets.get("OPENWEATHER_API_KEY", "YOUR_API_KEY")
        self.webhook_url = st.secrets.get("PIPEDREAM_WEBHOOK", "YOUR_WEBHOOK_URL")
        
    def get_weather(self):
        """Fetch weather data for Zakopane"""
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q=Zakopane&appid={self.weather_api_key}&units=metric"
            response = requests.get(url)
            data = response.json()
            
            return {
                "temperature": round(data["main"]["temp"]),
                "conditions": data["weather"][0]["description"],
                "wind_speed": round(data["wind"]["speed"] * 3.6),  # Convert to km/h
                "snow": data.get("snow", {}).get("1h", 0)
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
    
    def get_ski_route(self):
        """Get random ski route recommendation"""
        routes = [
            {"name": "Kasprowy Wierch", "difficulty": "Fortgeschritten", "conditions": "Ausgezeichnet"},
            {"name": "Nosal", "difficulty": "Mittel", "conditions": "Gut"},
            {"name": "Harenda", "difficulty": "Anfänger", "conditions": "Sehr gut"}
        ]
        return random.choice(routes)
    
    def get_fun_fact(self):
        """Get random fun fact about Zakopane"""
        facts = [
            "Zakopane ist die höchstgelegene Stadt Polens",
            "Sie ist bekannt als die 'Winterhauptstadt Polens'",
            "Der Name bedeutet auf Polnisch 'vergraben'",
            "Die typische Zakopane-Architektur wurde von Stanisław Witkiewicz entwickelt",
            "Die Skisprungschanze Wielka Krokiew ist eines der Wahrzeichen der Stadt"
        ]
        return random.choice(facts)
    
    def compose_message(self, weather, route, fact):
        """Compose WhatsApp message"""
        return f"""🏔 ZakZak Daily Update ⛷️

🌨 Wetter:
• Temperatur: {weather["temperature"]}°C
• Bedingungen: {weather["conditions"]}
• Neuschnee: {weather["snow"]}cm
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
        route = self.get_ski_route()
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
    
    # Create three columns
    col1, col2, col3 = st.columns(3)
    
    # Get data
    weather = bot.get_weather()
    route = bot.get_ski_route()
    fact = bot.get_fun_fact()
    
    # Weather Card
    with col1:
        st.markdown("### ❄️ Wetterbedingungen")
        st.write(f"🌡️ Temperatur: {weather['temperature']}°C")
        st.write(f"☁️ Bedingungen: {weather['conditions']}")
        st.write(f"❄️ Neuschnee: {weather['snow']}cm")
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
