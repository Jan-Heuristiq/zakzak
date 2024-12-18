import streamlit as st
import requests
import logging
from datetime import datetime
import random
from dataclasses import dataclass
from typing import List
import pytz
from functools import lru_cache

# [Previous imports and basic setup remain the same]

class RouteGenerator:
    def __init__(self, zakopane_data):
        self.data = zakopane_data

    def generate_daily_route(self, weather):
        """Generate a longer route with multiple slopes"""
        possible_routes = [
            ["Kasprowy Hauptabfahrt", "Gąsienicowa Route", "Goryczkowa Abfahrt", 
             "Szymoszkowa Hauptpiste", "Harenda Family", "Nosal Classic", 
             "Goryczkowa West", "Gąsienicowa Süd", "Kasprowy Nord", "Szymoszkowa Sport"],
            ["Szymoszkowa Sport", "Harenda Classic", "Nosal Hauptpiste", 
             "Kasprowy Express", "Gąsienicowa Classic", "Goryczkowa Panorama", 
             "Szymoszkowa Family", "Harenda Sport", "Kasprowy Challenge", "Nosal Family"]
        ]
        
        selected_route = random.choice(possible_routes)
        
        # Simplified message for WhatsApp
        message_route = "\n".join(f"{i+1}. {slope}" for i, slope in enumerate(selected_route))
        
        # Detailed info for website display
        detailed_route = []
        for slope in selected_route:
            detailed_route.append({
                "name": slope,
                "difficulty": random.choice(["Leicht", "Mittel", "Schwer"]),
                "length": random.randint(800, 3500),
                "vertical": random.randint(100, 900),
                "lifts": [random.choice(["Sessellift", "Schlepplift", "Seilbahn"])]
            })
        
        return message_route, detailed_route

class ZakZakBot:
    def __init__(self):
        self.weather_service = WeatherService()
        self.zakopane_data = ZakopaneData()
        self.route_generator = RouteGenerator(self.zakopane_data)

    def compose_daily_message(self):
        """Compose message with optimized spacing"""
        weather = self.weather_service.get_weather()
        route_message, detailed_route = self.route_generator.generate_daily_route(weather)
        
        # Calculate total length and vertical
        total_length = sum(r["length"] for r in detailed_route)
        total_vertical = sum(r["vertical"] for r in detailed_route)
        estimated_time = int(total_length / 200 + len(detailed_route) * 5)  # Rough estimate
        
        message = f"""🏔 ZakZak Daily Update ⛷️
🌨 Wetter:
📍 Tal ({weather['valley']['altitude']}m):
• Temperatur: {weather['valley']['temperature']}°C • Bedingungen: {weather['valley']['conditions']} • Schneehöhe: {weather['valley']['snow']}cm • Wind: {weather['valley']['wind_speed']}km/h
🏔 Berg ({weather['mountain']['altitude']}m):
• Temperatur: {weather['mountain']['temperature']}°C • Bedingungen: {weather['mountain']['conditions']} • Schneehöhe: {weather['mountain']['snow']}cm • Wind: {weather['mountain']['wind_speed']}km/h

🎿 Heute empfohlene Route:
📊 Routenübersicht:
• Gesamtlänge: {total_length}m • Höhenmeter: {total_vertical}m • Anzahl Pisten: {len(detailed_route)} • Geschätzte Dauer: {estimated_time} Minuten

🗺️ Routenverlauf:
{route_message}

💡 Fun Fact:
{random.choice(list(sum(FACTS.values(), [])))}

Einen schönen Tag auf der Piste! ⛷️"""
        
        return message, detailed_route

def main():
    st.title("ZakZak Daily ⛷️")
    
    # Initialize bot in session state if not exists
    if 'bot' not in st.session_state:
        st.session_state.bot = ZakZakBot()
    
    # Generate message immediately
    if 'message' not in st.session_state:
        message, detailed_route = st.session_state.bot.compose_daily_message()
        st.session_state.message = message
        st.session_state.detailed_route = detailed_route
    
    # Display message with copy button
    st.markdown("### WhatsApp Nachricht")
    st.code(st.session_state.message, language="text")
    st.button("In Zwischenablage kopieren", 
             on_click=lambda: st.write("", 
             unsafe_allow_html=True))
    
    # Display detailed route information
    st.markdown("### Vollständige Informationen zur Route")
    for i, route in enumerate(st.session_state.detailed_route, 1):
        with st.expander(f"{i}. {route['name']}"):
            st.write(f"Schwierigkeit: {route['difficulty']}")
            st.write(f"Länge: {route['length']}m")
            st.write(f"Höhenmeter: {route['vertical']}m")
            st.write("Aufstieg mit:")
            for lift in route['lifts']:
                st.write(f"• {lift}")
    
    # Refresh button
    if st.button("Neue Route generieren"):
        message, detailed_route = st.session_state.bot.compose_daily_message()
        st.session_state.message = message
        st.session_state.detailed_route = detailed_route
        st.experimental_rerun()
    
    # Sidebar information
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
