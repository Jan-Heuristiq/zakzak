import streamlit as st
import time
import os
import json
import logging
from datetime import datetime
import requests
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import schedule
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Include the SlopeData class here [Previous code from slope-lift-data artifact]
# Include the fun facts code here [Previous code from zakopane-facts artifact]

class ZakZakBot:
    def __init__(self):
        self.driver = None
        self.is_running = False
        self.last_message_time = None
        self.slope_data = SlopeData()
        
    def setup_driver(self):
        """Initialize Chrome driver with WhatsApp Web"""
        if not self.driver:
            options = webdriver.ChromeOptions()
            options.add_argument('--start-maximized')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument("--disable-notifications")
            self.driver = webdriver.Chrome(options=options)
            
    def get_weather(self):
        """Fetch weather data for Zakopane"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": 49.299,
                "longitude": 19.949,
                "current": ["temperature_2m", "weather_code", "wind_speed_10m"],
                "hourly": "snow_depth",
                "timezone": "Europe/Warsaw"
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            return {
                "temperature": round(data["current"]["temperature_2m"]),
                "conditions": self.get_weather_description(data["current"]["weather_code"]),
                "wind_speed": round(data["current"]["wind_speed_10m"]),
                "snow": round(data["hourly"]["snow_depth"][0] * 100)
            }
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            return self.get_dummy_weather()

    def get_weather_description(self, code):
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
        
    def compose_message(self, weather, route, fact):
        """Compose WhatsApp message"""
        return f"""🏔 ZakZak Daily Update ⛷️

🌨 Wetter:
• Temperatur: {weather['temperature']}°C
• Bedingungen: {weather['conditions']}
• Schneehöhe: {weather['snow']}cm
• Wind: {weather['wind_speed']}km/h

{route}

💡 Fun Fact:
{fact}

Einen schönen Tag auf der Piste! ⛷️"""

    def send_whatsapp_message(self, group_name, message):
        """Send WhatsApp message to specified group"""
        try:
            # Find and click on group
            search_xpath = '//div[@contenteditable="true"][@data-tab="3"]'
            search_box = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, search_xpath))
            )
            search_box.clear()
            search_box.send_keys(group_name)
            
            # Click on the group
            group_title = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, f"//span[@title='{group_name}']"))
            )
            group_title.click()
            
            # Find message input and send message
            message_box = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="6"]'))
            )
            message_box.clear()
            message_box.send_keys(message)
            message_box.send_keys("\n")
            
            self.last_message_time = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False

    def scheduled_update(self, group_name):
        """Send scheduled update"""
        weather = self.get_weather()
        route = self.slope_data.get_route_by_conditions(weather)
        fact = self.get_fun_facts()
        message = self.compose_message(weather, route, fact)
        return self.send_whatsapp_message(group_name, message)

def run_schedule():
    """Run the scheduler"""
    while True:
        schedule.run_pending()
        time.sleep(60)

# Initialize session state
if 'bot' not in st.session_state:
    st.session_state.bot = ZakZakBot()
if 'scheduler_thread' not in st.session_state:
    st.session_state.scheduler_thread = None

# Streamlit UI
st.title("ZakZak Daily")

# Sidebar for configuration
st.sidebar.header("Konfiguration")
group_name = st.sidebar.text_input("WhatsApp Gruppe:", "Meine Ski Gruppe")
schedule_time = st.sidebar.time_input("Tägliche Update-Zeit:", datetime.strptime("06:30", "%H:%M").time())

# Main content area
col1, col2 = st.columns(2)

with col1:
    st.header("WhatsApp Verbindung")
    if st.button("WhatsApp Web verbinden"):
        bot = st.session_state.bot
        bot.setup_driver()
        bot.driver.get("https://web.whatsapp.com")
        st.info("Bitte scannen Sie den QR-Code mit WhatsApp auf Ihrem Handy")

with col2:
    st.header("Bot Status")
    if st.session_state.bot.last_message_time:
        st.write(f"Letzte Nachricht: {st.session_state.bot.last_message_time.strftime('%d.%m.%Y %H:%M')}")
    if st.session_state.scheduler_thread and st.session_state.scheduler_thread.is_alive():
        st.write("Status: Aktiv")
    else:
        st.write("Status: Inaktiv")

# Preview section
st.header("Vorschau")
if st.button("Vorschau generieren"):
    weather = st.session_state.bot.get_weather()
    route = st.session_state.bot.slope_data.get_route_by_conditions(weather)
    fact = st.session_state.bot.get_fun_facts()
    message = st.session_state.bot.compose_message(weather, route, fact)
    st.session_state.preview_message = message

# Display preview in a card-like container
if 'preview_message' in st.session_state and st.session_state.preview_message:
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
    
    st.markdown(f'<div class="preview-box">{st.session_state.preview_message}</div>', unsafe_allow_html=True)

# Control buttons
col3, col4 = st.columns(2)

with col3:
    if st.button("Zeitplan aktivieren"):
        if not st.session_state.bot.driver:
            st.error("Bitte zuerst WhatsApp Web verbinden!")
        else:
            schedule.every().day.at(schedule_time.strftime("%H:%M")).do(
                st.session_state.bot.scheduled_update, group_name
            )
            
            if not st.session_state.scheduler_thread or not st.session_state.scheduler_thread.is_alive():
                st.session_state.scheduler_thread = threading.Thread(target=run_schedule)
                st.session_state.scheduler_thread.start()
                st.success(f"Bot wird täglich um {schedule_time.strftime('%H:%M')} Uhr Nachrichten senden")

with col4:
    if st.button("Jetzt senden"):
        if not st.session_state.bot.driver:
            st.error("Bitte zuerst WhatsApp Web verbinden!")
        else:
            with st.spinner("Sende Nachricht..."):
                weather = st.session_state.bot.get_weather()
                route = st.session_state.bot.slope_data.get_route_by_conditions(weather)
                fact = st.session_state.bot.get_fun_facts()
                message = st.session_state.bot.compose_message(weather, route, fact)
                
                if st.session_state.bot.send_whatsapp_message(group_name, message):
                    st.success("Nachricht erfolgreich gesendet!")
                else:
                    st.error("Fehler beim Senden der Nachricht")

# Footer
st.markdown("---")
st.markdown("Made with ❄️ for Zakopane")
