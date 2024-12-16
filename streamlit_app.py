import React, { useState, useEffect } from 'react';
import { Cloud, Snowflake, Mountain, Wind, Info } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const ZakopaneDashboard = () => {
  // Initialize all state variables
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [weather, setWeather] = useState({
    temperature: -2,
    conditions: "Schneefall",
    snowfall: 15,
    windSpeed: 8
  });

  const [skiRoute, setSkiRoute] = useState({
    name: "Kasprowy Wierch",
    difficulty: "Fortgeschritten",
    conditions: "Ausgezeichnet"
  });

  const funFacts = [
    "Zakopane ist die höchstgelegene Stadt Polens",
    "Sie ist bekannt als die 'Winterhauptstadt Polens'",
    "Der Name bedeutet auf Polnisch 'vergraben'",
    "Die typische Zakopane-Architektur wurde von Stanisław Witkiewicz entwickelt",
    "Die Skisprungschanze Wielka Krokiew ist eines der Wahrzeichen der Stadt"
  ];

  const [currentFact, setCurrentFact] = useState(funFacts[0]);

  // Update data every 24 hours
  useEffect(() => {
    const updateData = () => {
      setLastUpdate(new Date());
      setCurrentFact(funFacts[Math.floor(Math.random() * funFacts.length)]);
      
      // Here you would typically fetch new weather data and ski conditions
      // For now, we'll just simulate it with random changes
      setWeather(prev => ({
        ...prev,
        temperature: prev.temperature + (Math.random() * 2 - 1),
        snowfall: Math.max(0, prev.snowfall + (Math.random() * 5 - 2.5)),
        windSpeed: Math.max(0, prev.windSpeed + (Math.random() * 4 - 2))
      }));
    };

    // Initial update
    updateData();

    // Set up interval for updates
    const interval = setInterval(updateData, 86400000); // 24 hours

    // Cleanup on component unmount
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-white via-red-50 to-red-100 p-4">
      <div className="max-w-4xl mx-auto space-y-4">
        {/* Header with dark blue text */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-blue-900 mb-2">ZakZak Daily ⛷️</h1>
          <p className="text-blue-600">
            Letztes Update: {lastUpdate.toLocaleString('de-DE')}
          </p>
        </div>

        {/* Weather Card with blue icons */}
        <Card className="bg-white/90 backdrop-blur">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cloud className="text-blue-600" />
              Wetterbedingungen
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-2">
              <Snowflake className="text-blue-500" />
              <span>Temperatur: {weather.temperature.toFixed(1)}°C</span>
            </div>
            <div className="flex items-center gap-2">
              <Cloud className="text-blue-500" />
              <span>Bedingungen: {weather.conditions}</span>
            </div>
            <div className="flex items-center gap-2">
              <Snowflake className="text-blue-500" />
              <span>Neuschnee: {weather.snowfall.toFixed(1)}cm</span>
            </div>
            <div className="flex items-center gap-2">
              <Wind className="text-blue-500" />
              <span>Windgeschwindigkeit: {weather.windSpeed.toFixed(1)}km/h</span>
            </div>
          </CardContent>
        </Card>

        {/* Ski Route Card with blue icon */}
        <Card className="bg-white/90 backdrop-blur">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mountain className="text-blue-600" />
              Empfohlene Route heute
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className="text-lg font-semibold">{skiRoute.name}</p>
              <p>Schwierigkeitsgrad: {skiRoute.difficulty}</p>
              <p>Bedingungen: {skiRoute.conditions}</p>
            </div>
          </CardContent>
        </Card>

        {/* Fun Fact Card with blue icon */}
        <Card className="bg-white/90 backdrop-blur">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="text-blue-600" />
              Täglicher Fun Fact
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg">{currentFact}</p>
          </CardContent>
        </Card>

        {/* WhatsApp Message Preview */}
        <Card className="bg-green-50/90 backdrop-blur">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12.012 2c-5.506 0-9.989 4.478-9.99 9.984a9.964 9.964 0 001.333 4.993L2 22l5.233-1.237a10.065 10.065 0 004.779 1.225h.004c5.505 0 9.988-4.478 9.988-9.984 0-2.669-1.037-5.176-2.922-7.062A9.944 9.944 0 0012.012 2z"/>
              </svg>
              WhatsApp Nachricht Vorschau
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap font-mono text-sm bg-white p-4 rounded">
{`🏔 ZakZak Daily Update ⛷️

🌨 Wetter:
• Temperatur: ${weather.temperature.toFixed(1)}°C
• Bedingungen: ${weather.conditions}
• Neuschnee: ${weather.snowfall.toFixed(1)}cm
• Wind: ${weather.windSpeed.toFixed(1)}km/h

🎿 Heute empfohlen:
${skiRoute.name} - ${skiRoute.conditions}
Schwierigkeitsgrad: ${skiRoute.difficulty}

💡 Fun Fact:
${currentFact}

Einen schönen Tag auf der Piste! ⛷️`}
            </pre>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ZakopaneDashboard;
