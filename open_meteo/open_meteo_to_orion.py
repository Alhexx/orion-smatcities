import requests
import datetime
import json
import os
import time

# --- Configurações (Melhor usar variáveis de ambiente no Docker) ---
ORION_HOST = os.getenv("ORION_HOST", "http://localhost:1026")
ORION_URL = f"{ORION_HOST}/v2/entities"

CITY_NAME = os.getenv("CITY_NAME", "Natal")
LAT = float(os.getenv("LATITUDE", "-5.795"))
LON = float(os.getenv("LONGITUDE", "-35.195"))

REFRESH_INTERVAL_SECONDS = int(os.getenv("REFRESH_INTERVAL_SECONDS", 30))

HEADERS = {
    "Content-Type": "application/json",
    "Fiware-Service": os.getenv("FIWARE_SERVICE", "openmeteo_service"),
    "Fiware-ServicePath": os.getenv("FIWARE_SERVICE_PATH", "/weather")
}

ENTITY_ID = os.getenv("ENTITY_ID", "WeatherObserved:Natal")
ENTITY_TYPE = "WeatherObserved"

# --- Funções ---
def get_weather():
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LAT}&longitude={LON}"
        f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_120m"
        f"&wind_speed_unit=ms"
        f"&timezone=America%2FSao_Paulo"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"Dados da Open-Meteo recebidos: {json.dumps(data['current'], indent=2)}")
        return data["current"]
    except requests.exceptions.Timeout:
        print(f"Erro: Tempo limite excedido ao conectar à Open-Meteo API.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar à Open-Meteo API: {e}")
        return None
    except KeyError as e:
        print(f"Erro ao processar dados da Open-Meteo (chave ausente): {e}")
        return None

def send_to_orion(weather_data):
    if weather_data is None:
        print("Nenhum dado de clima para enviar.")
        return

    current_time_utc = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')

    entity_attributes_payload = {
        "temperature": {
            "value": weather_data["temperature_2m"],
            "type": "Number",
            "metadata": {
                "unit": { "value": "celsius", "type": "Text" }
            }
        },
        "humidity": {
            "value": weather_data["relative_humidity_2m"],
            "type": "Number",
            "metadata": {
                "unit": { "value": "percent", "type": "Text" }
            }
        },
        "weatherCode": {
            "value": weather_data["weather_code"],
            "type": "Number"
        },
        "windSpeed120": {
            "value": weather_data["wind_speed_120m"],
            "type": "Number",
            "metadata": {
                "unit": { "value": "m/s", "type": "Text" }
            }
        },
        "location": {
            "type": "geo:point",
            "value": f"{LAT},{LON}"
        },
        "dateObserved": {
            "type": "DateTime",
            "value": current_time_utc
        }
    }

    entity_update_url = f"{ORION_HOST}/v2/entities/{ENTITY_ID}/attrs"
    try:
        patch_response = requests.patch(entity_update_url, headers=HEADERS, data=json.dumps(entity_attributes_payload), timeout=5)
        patch_response.raise_for_status()
        print(f"[{current_time_utc}] Entidade '{ENTITY_ID}' atualizada com sucesso via PATCH. Status: {patch_response.status_code}")
        return
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"[{current_time_utc}] Entidade '{ENTITY_ID}' não encontrada. Tentando criar com POST.")
            full_entity_payload = {
                "id": ENTITY_ID,
                "type": ENTITY_TYPE,
                **entity_attributes_payload
            }
            try:
                post_response = requests.post(ORION_URL, headers=HEADERS, data=json.dumps(full_entity_payload), timeout=5)
                post_response.raise_for_status()
                print(f"[{current_time_utc}] Entidade '{ENTITY_ID}' criada com sucesso via POST. Status: {post_response.status_code}")
            except requests.exceptions.RequestException as post_e:
                print(f"[{current_time_utc}] Erro ao criar entidade '{ENTITY_ID}' via POST: {post_e}")
        else:
            print(f"[{current_time_utc}] Erro HTTP inesperado durante PATCH (status {e.response.status_code}): {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"[{current_time_utc}] Erro de conexão ao enviar PATCH para Orion: {e}")

if __name__ == "__main__":
    print(f"Adaptador Open-Meteo iniciado para '{CITY_NAME}' ({LAT}, {LON}).")
    print(f"Enviando dados para Orion em '{ORION_HOST}' com serviço '{HEADERS['Fiware-Service']}' a cada {REFRESH_INTERVAL_SECONDS} segundos.")
    print(f"Entidade a ser criada/atualizada: ID='{ENTITY_ID}', Tipo='{ENTITY_TYPE}'")

    while True:
        weather_data = get_weather()
        send_to_orion(weather_data)
        print(f"Aguardando {REFRESH_INTERVAL_SECONDS} segundos para a próxima atualização...")
        time.sleep(REFRESH_INTERVAL_SECONDS)
