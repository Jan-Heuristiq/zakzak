import streamlit as st
import requests
import logging
from datetime import datetime
import random
from dataclasses import dataclass
from typing import List
import pytz
from functools import lru_cache

# [Previous code until WeatherService class remains the same]

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
            'gasienicowa_chair': Lift(
                name='Gąsienicowa Sessellift',
                type='Sessellift',
                capacity=2400,
                length=1600,
                vertical=300,
                duration=8,
                base_altitude=1375,
                top_altitude=1675
            ),
            'goryczkowa_chair': Lift(
                name='Goryczkowa Sessellift',
                type='Sessellift',
                capacity=2400,
                length=1800,
                vertical=320,
                duration=9,
                base_altitude=1350,
                top_altitude=1670
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
            ),
            'harenda_chair': Lift(
                name='Harenda Sessellift',
                type='Sessellift',
                capacity=2000,
                length=1600,
                vertical=320,
                duration=8,
                base_altitude=750,
                top_altitude=1070
            ),
            'nosal_lift': Lift(
                name='Nosal Schlepplift',
                type='Schlepplift',
                capacity=1200,
                length=650,
                vertical=172,
                duration=5,
                base_altitude=1002,
                top_altitude=1174
            )
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
            'kasprowy_goryczkowa': Slope(
                name='Kasprowy - Goryczkowa',
                difficulty='Schwer',
                length=3300,
                vertical=850,
                area='Kasprowy Wierch',
                connects_to=['kasprowy_gasienicowa', 'goryczkowa_nizna'],
                access_lifts=['kasprowy_cable_car'],
                night_skiing=False
            ),
            'gasienicowa_nizna': Slope(
                name='Gąsienicowa Niżna',
                difficulty='Mittel',
                length=1200,
                vertical=250,
                area='Kasprowy Wierch',
                connects_to=['kasprowy_gasienicowa'],
                access_lifts=['gasienicowa_chair'],
                night_skiing=False
            ),
            'goryczkowa_nizna': Slope(
                name='Goryczkowa Niżna',
                difficulty='Mittel',
                length=1400,
                vertical=280,
                area='Kasprowy Wierch',
                connects_to=['kasprowy_goryczkowa'],
                access_lifts=['goryczkowa_chair'],
                night_skiing=False
            ),
            'szymoszkowa_1': Slope(
                name='Szymoszkowa Hauptpiste',
                difficulty='Mittel',
                length=1300,
                vertical=160,
                area='Szymoszkowa',
                connects_to=['szymoszkowa_2'],
                access_lifts=['szymoszkowa_chair'],
                night_skiing=True
            ),
            'szymoszkowa_2': Slope(
                name='Szymoszkowa Familienpiste',
                difficulty='Leicht',
                length=1100,
                vertical=140,
                area='Szymoszkowa',
                connects_to=['szymoszkowa_1'],
                access_lifts=['szymoszkowa_chair'],
                night_skiing=True
            ),
            'nosal_main': Slope(
                name='Nosal Hauptabfahrt',
                difficulty='Mittel',
                length=650,
                vertical=172,
                area='Nosal',
                connects_to=[],
                access_lifts=['nosal_lift'],
                night_skiing=True
            ),
            'harenda_family': Slope(
                name='Harenda Familienpiste',
                difficulty='Leicht',
                length=2000,
                vertical=300,
                area='Harenda',
                connects_to=['harenda_main'],
                access_lifts=['harenda_chair'],
                night_skiing=True
            ),
            'harenda_main': Slope(
                name='Harenda Hauptpiste',
                difficulty='Mittel',
                length=2500,
                vertical=320,
                area='Harenda',
                connects_to=['harenda_family'],
                access_lifts=['harenda_chair'],
                night_skiing=True
            )
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
            if current_slope not in self.data.slopes:
                break
                
            slope = self.data.slopes[current_slope]
            lifts = [self.data.lifts[lift_id] for lift_id in slope.access_lifts]
            
            route_entry = {
                'id': current_slope,
                'slope': slope,
                'lifts': lifts
            }
            route.append(route_entry)
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

facts = {
    "general": [
        "Zakopane ist die höchstgelegene Stadt Polens",
        "Sie ist bekannt als die 'Winterhauptstadt Polens'",
        "Der Name bedeutet auf Polnisch 'vergraben'",
        "Die Stadt liegt auf einer Höhe von 800-1000 Metern über dem Meeresspiegel",
        "Zakopane wurde erst 1933 offiziell zur Stadt ernannt",
        "Im 19. Jahrhundert war Zakopane ein kleines Hirtendorf mit nur 43 Häusern",
        "Die Stadt hat etwa 27.000 Einwohner, empfängt aber jährlich über 2,5 Millionen Touristen",
        "Die ersten Skifahrer kamen bereits in den 1890er Jahren nach Zakopane"
    ],
    "culture": [
        "Die typische Zakopane-Architektur wurde von Stanisław Witkiewicz entwickelt",
        "Der Zakopane-Stil kombiniert lokale Górale-Traditionen mit Art Nouveau",
        "Die Villa Koliba war das erste im Zakopane-Stil erbaute Haus",
        "Die lokale Górale-Kultur ist für ihre charakteristische Musik und Tracht bekannt",
        "Das Tatra-Museum wurde 1889 gegründet und zeigt die reiche Kulturgeschichte der Region",
        "Die Krupówki ist die berühmte Fußgängerzone und das Herz der Stadt",
        "In der Stadt gibt es über 500 denkmalgeschützte Holzhäuser",
        "Die lokale Sprache 'Gwara Góralska' ist ein einzigartiger polnischer Dialekt"
    ],
    "sports": [
        "Die Skisprungschanze Wielka Krokiew ist eines der Wahrzeichen der Stadt",
        "Auf der Wielka Krokiew finden regelmäßig Weltcup-Springen statt",
        "Der erste Skiclub Polens wurde 1907 in Zakopane gegründet",
        "1929 fand hier die erste FIS-Weltmeisterschaft außerhalb Mitteleuropas statt",
        "Zakopane war zweimal Kandidat für die Olympischen Winterspiele",
        "Die Stadt war Austragungsort der Nordischen Junioren-WM 2008",
        "Im Sommer ist Zakopane ein beliebtes Ziel für Wanderer und Bergsteiger",
        "Es gibt über 275 Kilometer markierte Wanderwege in der Region"
    ],
    "nature": [
        "Die Stadt liegt am Fuß der Tatra, dem höchsten Gebirgszug der Karpaten",
        "Der Kasprowy Wierch (1.987 m) ist der bekannteste Skiberg Zakopanes",
        "Im Winter können die Temperaturen auf bis zu -30°C fallen",
        "Die Tatra-Region beherbergt seltene Tierarten wie Braunbären und Gämsen",
        "Der Tatra-Nationalpark wurde 1954 gegründet",
        "Die Bergkette Giewont sieht aus wie ein 'schlafender Ritter'",
        "In den Tatra-Bergen gibt es über 30 Bergseen",
        "Der höchste Berg Polens, Rysy (2.499 m), liegt in der Nähe von Zakopane"
    ],
    "cuisine": [
        "Oscypek, der lokale Räucherkäse, hat EU-geschützte Herkunftsbezeichnung",
        "Żurek po Góralsku ist eine spezielle Variante der traditionellen polnischen Suppe",
        "Kwaśnica, eine säuerliche Krautsuppe, ist ein typisches Góralen-Gericht",
        "Moskole sind traditionelle Kartoffelpuffer der Region",
        "Der lokale Tee 'Herbata po Góralsku' wird mit Wodka serviert",
        "Bundz ist ein spezieller Schafskäse, der nur im Sommer hergestellt wird",
        "Die traditionelle Góralen-Küche basiert auf Lamm- und Schaffleisch",
        "Im Winter werden oft 'Grzaniec' (Glühwein) und heißer Met serviert"
    ]
}

# [Rest of the code (ZakZakBot, add_copy_button, main) remains the same]

if __name__ == "__main__":
    main()
