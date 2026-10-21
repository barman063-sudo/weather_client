import requests
import json
from pathlib import Path

HISTORY_FILE = Path("weather_history.json")

def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        print("Файл истории повреждён. Начнём с пустой истории.")
        return []

def save_history(history):
    with HISTORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def find_city(city_name):
    """Ищет город через два разных сервиса. Возвращает (lat, lon, name) или (None, None, None)."""

    
    def search_open_meteo(name):
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": name, "count": 1, "language": "ru", "format": "json"}
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("results"):
                r = data["results"][0]
                return r["latitude"], r["longitude"], r["name"]
        except:
            pass
        return None, None, None

    
    def search_open_meteo_en(name):
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": name, "count": 1, "language": "en", "format": "json"}
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("results"):
                r = data["results"][0]
                return r["latitude"], r["longitude"], r["name"]
        except:
            pass
        return None, None, None

    
    def search_nominatim(name):
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": name, "format": "json", "limit": 1}
        headers = {"User-Agent": "WeatherClient/1.0"}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"]), data[0]["display_name"].split(",")[0]
        except:
            pass
        return None, None, None

    
    for search_func in [search_open_meteo, search_open_meteo_en, search_nominatim]:
        lat, lon, name = search_func(city_name)
        if lat is not None:
            return lat, lon, name

    return None, None, None

def get_weather(lat, lon, name):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code",
        "timezone": "auto"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return None, "Сервер погоды долго не отвечал."
    except requests.exceptions.ConnectionError:
        return None, "Нет интернета или сервер недоступен."
    except Exception as e:
        return None, f"Ошибка: {e}"

    current = data["current"]
    temp = current["temperature_2m"]
    code = current["weather_code"]

    conditions = {
        0: "Ясно", 1: "Ясно", 2: "Переменная облачность", 3: "Облачно",
        45: "Туман", 51: "Лёгкий дождь", 61: "Дождь", 71: "Снег"
    }
    condition = conditions.get(code, "Неизвестно")

    return {"city": name, "temp": temp, "condition": condition}, None

def main():
    history = load_history()
    print("🌤 Погода по любому городу мира!")
    print("Вводи название города (например: Самара, London, Tokyo, Париж).")
    print("Введите 0 для выхода.\n")

    while True:
        city_input = input("Город: ").strip()
        print(f"[Отладка] Программа получила: '{city_input}'")

        if city_input == "0":
            print("Пока! История сохранена в weather_history.json.")
            break

        if not city_input:
            print("⚠️ Введи название города.")
            continue

        
        print(f"🔍 Ищем город «{city_input}»...")
        lat, lon, found_name = find_city(city_input)

        if lat is None:
            print(f"Город «{city_input}» не найден. Проверь написание.")
            continue

        print(f"📍 Найден: {found_name}")

        
        print(f"Запрашиваем погоду...")
        data, error = get_weather(lat, lon, found_name)

        if error:
            print(error)
            continue

        print(f"Погода в {data['city']}: {data['temp']}°C, {data['condition']}")

        history.append(data)
        save_history(history)
        print("Запрос сохранён в историю (weather_history.json).")

if __name__ == "__main__":
    main()