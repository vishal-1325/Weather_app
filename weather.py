import requests
import streamlit as st
import datetime
import json
import os
from collections import defaultdict

# --------------------------
# 1. Setup
# --------------------------
API_KEY = "f863e7541fcd44ae4849b214c7679b52"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
LOG_FILE = "weather_log.json"

WEATHER_ICONS = {
    "clear": "☀️",
    "clouds": "☁️",
    "rain": "🌧️",
    "drizzle": "🌦️",
    "thunderstorm": "🌩️",
    "snow": "❄️",
    "mist": "🌫️",
    "fog": "🌫️",
    "haze": "🌁",
    "smoke": "🌫️",
    "dust": "🌪️",
}

# --------------------------
# 2. Helper Functions
# --------------------------
def get_weather(city):
    params = {"q": city, "appid": API_KEY, "units": "metric"}
    response = requests.get(WEATHER_URL, params=params)
    return response.json() if response.status_code == 200 else None

def get_forecast(city):
    params = {"q": city, "appid": API_KEY, "units": "metric"}
    response = requests.get(FORECAST_URL, params=params)
    return response.json() if response.status_code == 200 else None

def save_log(city, weather_data):
    entry = {
        "city": city.capitalize(),
        "temp": weather_data["main"]["temp"],
        "humidity": weather_data["main"]["humidity"],
        "condition": weather_data["weather"][0]["description"],
        "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    logs = load_logs()
    logs.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

def load_logs():
    return json.load(open(LOG_FILE, "r")) if os.path.exists(LOG_FILE) else []

def get_icon(condition: str) -> str:
    for key, icon in WEATHER_ICONS.items():
        if key in condition.lower():
            return icon
    return "🌍"

def average_daily_forecast(forecast_data):
    daily = defaultdict(list)
    for entry in forecast_data["list"]:
        date = entry["dt_txt"].split(" ")[0]
        daily[date].append(entry["main"]["temp"])
    return {date: sum(temps)/len(temps) for date, temps in daily.items()}

def get_weather_bg(condition, theme):
    """Return background gradient + text color based on weather condition"""
    if "rain" in condition.lower():
        return ("linear-gradient(to right, #4e54c8, #8f94fb)", "white") if theme=="Light 🌞" else ("#31567c", "white")
    if "cloud" in condition.lower():
        return ("linear-gradient(to right, #bdc3c7, #2c3e50)", "black") if theme=="Light 🌞" else ("#131111", "white")
    if "clear" in condition.lower():
        return ("linear-gradient(to right, #fceabb, #f8b500)", "black") if theme=="Light 🌞" else ("#f39c12", "black")
    return ("linear-gradient(to right, #ece9e6, #ffffff)", "black") if theme=="Light 🌞" else ("#34495e", "white")


# --------------------------
# 3. Streamlit UI
# --------------------------
st.set_page_config(page_title="Weather App", page_icon="⛅", layout="wide")

theme = st.sidebar.radio("Choose Theme:", ["Light 🌞", "Dark 🌙"])

# Global background & card style
if theme == "Dark 🌙":
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: #121212 !important;
            color: white !important;
            font-family: 'Arial', sans-serif;
        }}
        .card {{
            padding:20px; 
            margin:10px; 
            border-radius:15px; 
            background: rgba(255,255,255,0.05) !important; 
            color: white !important;
            text-align:center; 
            backdrop-filter: blur(10px);
        }}
        .card h3, .card h4 {{
            color: white !important;
        }}
        .stButton>button {{
            color: white !important;
            background-color: #333 !important;
            border-radius:10px;
        }}
        input[type=text] {{
            color: black;
            border-radius:10px;
        }}
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(to right, #6dd5ed, #2193b0) !important;
            font-family: 'Arial', sans-serif;
        }}
        .card {{
            padding:20px; 
            margin:10px; 
            border-radius:15px; 
            background: rgba(255,255,255,0.3); 
            text-align:center;
            color:#0A1F44;   /* updated text color for light mode */
        }}
        </style>
    """, unsafe_allow_html=True)

st.title("🌦️ Weather App")
st.write("Real-time weather info + 5-day forecast")

city = st.text_input("Enter city name:", "Delhi")

if st.button("Get Weather"):
    data = get_weather(city)
    if data:
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        condition = data["weather"][0]["description"].capitalize()
        icon = get_icon(condition)
        bg = get_weather_bg(condition, theme)
        
        st.markdown(f"<div style='padding:20px; border-radius:15px; background:{bg}; color:white; text-align:center;'>"
                    f"<h2>{city.capitalize()} {icon}</h2>"
                    f"<h3>🌡️ Temperature: {temp} °C</h3>"
                    f"<h3>💧 Humidity: {humidity}%</h3>"
                    f"<h3>☁️ Condition: {condition}</h3></div>", unsafe_allow_html=True)

        save_log(city, data)
        st.success("Weather data saved in logs ✅")

        # 5-Day Forecast
        st.subheader("📅 5-Day Forecast")
        forecast = get_forecast(city)
        if forecast:
            daily_avg = average_daily_forecast(forecast)
            days = list(daily_avg.keys())
            temps = list(daily_avg.values())

            cols = st.columns(len(days))
            for col, d, t in zip(cols, days, temps):
                col.markdown(f"<div class='card'><h4>{d}</h4><p>🌡️ {t:.1f} °C</p></div>", unsafe_allow_html=True)
        else:
            st.error("Could not fetch forecast data ❌")
    else:
        st.error("City not found or API error.")

# Weather Logs Section
if st.checkbox("Show Weather Logs"):
    logs = load_logs()
    if logs:
        cities = sorted(set(log["city"] for log in logs))
        selected_city = st.selectbox("Filter logs by city:", cities)
        filtered_logs = [log for log in logs if log["city"] == selected_city]

        if filtered_logs:
            st.subheader(f"📜 Recent Weather Logs for {selected_city}")
            for log in reversed(filtered_logs[-5:]):
                st.write(f"📍 {log['city']} | {get_icon(log['condition'])} 🌡️ {log['temp']}°C | 💧 {log['humidity']}% | ☁️ {log['condition']} | 🕒 {log['datetime']}")
        else:
            st.info("No logs available for this city.")
    else:
        st.info("No logs available yet.")
