from flask import Flask, jsonify, render_template_string
import board
import busio
from adafruit_bmp280 import Adafruit_BMP280_I2C
import requests
from datetime import datetime

# --- konfiguracja ---

OPEN_METEO_LAT = 54.6      # <-- tu wpisz swoją szerokość geogr.
OPEN_METEO_LON = 18.4      # <-- tu wpisz swoją długość geogr.

app = Flask(__name__)

# --- inicjalizacja czujnika BMP280 ---

i2c = busio.I2C(board.SCL, board.SDA)
bmp = Adafruit_BMP280_I2C(i2c)

# --- funkcje pomocnicze ---

def get_local_weather():
    """Odczyt z BMP280"""
    return {
        "temperature_c": round(bmp.temperature, 1),
        "pressure_hpa": round(bmp.pressure, 1),
    }

def get_open_meteo():
    """Prosty odczyt wiatru z Open-Meteo (możesz rozbudować)."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={OPEN_METEO_LAT}&longitude={OPEN_METEO_LON}"
        "&current=temperature_2m,wind_speed_10m,wind_direction_10m"
        "&timezone=auto"
    )
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()["current"]
        return {
            "wind_speed": data["wind_speed_10m"],       # km/h
            "wind_dir": data["wind_direction_10m"],     # °
            "remote_temp": data["temperature_2m"],
            "updated_at": data["time"],
        }
    except Exception:
        # jak coś pójdzie nie tak – zwróć None, UI to ładnie obsłuży
        return None

# --- API JSON ---

@app.route("/api/weather")
def api_weather():
    local = get_local_weather()
    remote = get_open_meteo()
    return jsonify({
        "local": local,
        "open_meteo": remote,
    })

# --- UI HTML w stylu Twojej karty ---

CARD_TEMPLATE = """
<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<title>Stacja pogodowa</title>
<script>
    // Auto-refresh co 30 sekund
    setTimeout(function() {
        window.location.reload();
    }, 30000);
</script>
<style>
    :root {
        --bg: #050816;
        --card: #111827;
        --text-main: #f9fafb;
        --text-muted: #9ca3af;
        --accent: #38bdf8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: radial-gradient(circle at top, #1f2937 0, #020617 60%);
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: var(--text-main);
    }
    .card {
        background: var(--card);
        padding: 24px 28px;
        border-radius: 18px;
        box-shadow: 0 28px 60px rgba(0,0,0,0.6);
        width: 360px;
    }
    .title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .subtitle {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-bottom: 18px;
    }
    .temp-row {
        display: flex;
        align-items: baseline;
        gap: 8px;
        margin-bottom: 18px;
    }
    .temp-value {
        font-size: 2.6rem;
        font-weight: 700;
        color: var(--accent);
    }
    .temp-unit {
        font-size: 1.1rem;
        color: var(--text-muted);
    }
    .grid {
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
        margin-bottom: 16px;
    }
    .label {
        color: var(--text-muted);
        margin-bottom: 4px;
    }
    .value {
        font-weight: 500;
    }
    .footer {
        font-size: 0.75rem;
        color: var(--text-muted);
    }
</style>
</head>
<body>
    <div class="card">
        <div class="title">Stacja pogodowa</div>
        <div class="subtitle">
            Dane lokalne z BMP280{{ " + Open-Meteo" if remote else "" }}
        </div>

        <div class="temp-row">
            <div class="temp-value">{{ local.temperature_c }}°C</div>
            <div class="temp-unit">Rumia</div>
        </div>

        <div class="grid">
            <div>
                <div class="label">Ciśnienie</div>
                <div class="value">{{ local.pressure_hpa }} hPa</div>
            </div>
            <div>
                <div class="label">Wiatr</div>
                {% if remote %}
                    <div class="value">{{ "%.1f"|format(remote.wind_speed) }} km/h</div>
                {% else %}
                    <div class="value">brak danych</div>
                {% endif %}
            </div>
            <div>
                <div class="label">Kierunek</div>
                {% if remote %}
                    <div class="value">{{ remote.wind_dir }}°</div>
                {% else %}
                    <div class="value">–</div>
                {% endif %}
            </div>
        </div>

        <div class="footer">
            Ostatnia aktualizacja:
            {% if remote %}
                {{ remote.updated_at }}
            {% else %}
                {{ now }}
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def card():
    local = get_local_weather()
    remote = get_open_meteo()
    return render_template_string(
        CARD_TEMPLATE,
        local=local,
        remote=remote,
        now=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5080)

