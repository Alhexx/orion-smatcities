import requests
import json
import os

# --- Configurações da Assinatura ---
# As mesmas variáveis de ambiente usadas pelo adaptador, ou padrões para rodar localmente
ORION_HOST = os.getenv("ORION_HOST", "http://localhost:1026")
QUANTUMLEAP_HOST = os.getenv("QUANTUMLEAP_HOST", "http://localhost:8668") # Para testes locais
# Se rodando via docker-compose, QuantumLeap será acessado por seu nome de serviço
# QUANTUMLEAP_HOST = os.getenv("QUANTUMLEAP_HOST_DOCKER", "http://quantumleap:8668")

FIWARE_SERVICE = os.getenv("FIWARE_SERVICE", "openmeteo_service")
FIWARE_SERVICE_PATH = os.getenv("FIWARE_SERVICE_PATH", "/weather")
ENTITY_ID = os.getenv("ENTITY_ID", "WeatherObserved:Natal")
ENTITY_TYPE = "WeatherObserved"

ORION_SUBSCRIPTION_URL = f"{ORION_HOST}/v2/subscriptions"
QUANTUMLEAP_NOTIFY_URL = f"{QUANTUMLEAP_HOST}/v2/notify"

HEADERS = {
    "Content-Type": "application/json",
    "Fiware-Service": FIWARE_SERVICE,
    "Fiware-ServicePath": FIWARE_SERVICE_PATH
}

# --- Corpo da Assinatura ---
subscription_payload = {
    "description": "Notificar o QuantumLeap sobre atualizações do clima de Natal",
    "subject": {
        "entities": [
            {
                "id": ENTITY_ID,
                "type": ENTITY_TYPE
            }
        ],
        "condition": {
            "attrs": [
                "temperature", "humidity", "weatherCode", "dateObserved"
            ]
        }
    },
    "notification": {
        "http": {
            "url": QUANTUMLEAP_NOTIFY_URL # A URL do QuantumLeap
        },
        "attrs": [
            "temperature", "humidity", "weatherCode", "location", "dateObserved" # Corrigido o typo aqui!
        ],
        "attrsFormat": "normalized"
    },
    "throttling": 1
}

# --- Função para Criar a Assinatura ---
def create_subscription():
    print(f"Tentando criar/verificar assinatura para a entidade '{ENTITY_ID}'...")
    print(f"Orion URL: {ORION_SUBSCRIPTION_URL}")
    print(f"QuantumLeap Notify URL (no payload para Orion): {subscription_payload['notification']['http']['url']}") # Mostra a URL interna

    # Headers para requisições GET (sem Content-Type)
    get_headers = {
        "Fiware-Service": FIWARE_SERVICE,
        "Fiware-ServicePath": FIWARE_SERVICE_PATH
    }

    try:
        # Primeiro, tenta listar assinaturas para ver se já existe e evitar recriar
        # Usando get_headers aqui!
        response = requests.get(ORION_SUBSCRIPTION_URL, headers=get_headers, timeout=5)
        response.raise_for_status() # Lança exceção para 4xx/5xx
        subscriptions = response.json()
        
        found_subscription = False
        for sub in subscriptions:
            # Uma verificação simples se a URL de notificação e as entidades são as mesmas
            if sub.get('notification', {}).get('http', {}).get('url') == subscription_payload["notification"]["http"]["url"] and \
               any(e.get('id') == ENTITY_ID for e in sub.get('subject', {}).get('entities', [])):
                print(f"Assinatura já existe com ID: {sub.get('id')}.")
                found_subscription = True
                break

        if found_subscription:
            return

        # Se não encontrou, cria
        print("Assinatura não encontrada. Criando nova assinatura...")
        # Usando o dicionário HEADERS original (com Content-Type) para o POST
        response = requests.post(ORION_SUBSCRIPTION_URL, headers=HEADERS, data=json.dumps(subscription_payload), timeout=5)
        response.raise_for_status() # Lança exceção para 4xx/5xx erros

        if response.status_code == 201:
            print(f"Assinatura criada com sucesso! Status: {response.status_code}")
        else:
            print(f"Assinatura criada, mas status inesperado: {response.status_code}. Resposta: {response.text}")

    except requests.exceptions.HTTPError as e:
        print(f"Erro HTTP ao criar assinatura: Status {e.response.status_code} - {e.response.text}")
        if "Already Exists" in e.response.text or e.response.status_code == 409:
            print("Pode ser que a assinatura já exista, mas a verificação inicial falhou.")
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão ao Orion ao tentar criar/verificar assinatura: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    # IMPORTANTE: Use a URL do QuantumLeap para Docker Compose se estiver rodando com Docker Compose
    # Altere aqui para usar o nome do serviço 'quantumleap'
    # Ao executar este script localmente, a variável de ambiente QUANTUMLEAP_HOST não estará definida para 'quantumleap'
    # O Python tentaria 'localhost' que não consegue ver 'quantumleap'
    # Então, se você está rodando esse script LOCALMENTE, e o quantumleap está no DOCKER:
    # Mude QUANTUMLEAP_NOTIFY_URL para 'http://localhost:8668/v2/notify'
    # Mas se você for rodar ESTE script DENTRO de um container Docker (o que não é o plano agora), aí seria 'http://quantumleap:8668/v2/notify'
    # Para o seu caso, que o QuantumLeap está no Docker e você roda o script no seu terminal, a URL externa é localhost
    QUANTUMLEAP_NOTIFY_URL = f"{QUANTUMLEAP_HOST}/v2/notify" 
    
    # Mas se este script fosse rodar DENTRO de um container da mesma rede docker-compose que o quantumleap:
    # QUANTUMLEAP_NOTIFY_URL = "http://quantumleap:8668/v2/notify"

    # No seu caso, rodando o script no PowerShell, enquanto o QuantumLeap está no Docker:
    # QuantumLeap precisa ser acessível via localhost no seu host
    if ORION_HOST == "http://localhost:1026" and QUANTUMLEAP_HOST == "http://localhost:8668":
        print("Atenção: Rodando em modo local. Certifique-se de que o Orion e QuantumLeap estão acessíveis via localhost.")
        print("Se o QuantumLeap estiver em um contêiner Docker na rede 'fiware', ele pode não ser acessível via 'localhost:8668' diretamente do seu host, a menos que a porta 8668 esteja mapeada corretamente no docker-compose.yml.")
        # No seu docker-compose.yml, a porta 8668 está mapeada: 8668:8668. Então, localhost está OK.
        # Mas a URL no notification.http.url para o Orion precisa ser a interna (quantumleap:8668)
        # Vamos manter o QuantumLeap Notify URL como quantumleap:8668 no payload, que é o que o Orion usará INTERNAMENTE.
        # Mas para testar, podemos mudar a variável QUANTUMLEAP_HOST aqui para simular o comportamento dentro do compose
        
        # O QuantumLeap_NOTIFY_URL no payload para o Orion deve ser o nome do serviço no Docker Compose!
        # Isso significa que a linha: QUANTUMLEAP_NOTIFY_URL = f"{QUANTUMLEAP_HOST}/v2/notify"
        # Precisa ser revisada para que no payload ela seja "http://quantumleap:8668/v2/notify"
        # O script local está usando QUANTUMLEAP_HOST=http://localhost:8668, então vamos sobrescrever para o payload
        
        subscription_payload["notification"]["http"]["url"] = "http://quantumleap:8668/v2/notify"


    create_subscription()