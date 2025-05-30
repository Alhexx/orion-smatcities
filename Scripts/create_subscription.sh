#!/bin/bash

ORION_HOST="http://localhost:1026"
QL_HOST="http://localhost:8668" # Não usa pq ta dentro do container do orion ai tem que ser o nome do container do quantumleap
FIWARE_SERVICE="openmeteo_service"
FIWARE_SERVICE_PATH="/weather"

curl -iX POST "$ORION_HOST/v2/subscriptions" \
  -H "Content-Type: application/json" \
  -H "Fiware-Service: $FIWARE_SERVICE" \
  -H "Fiware-ServicePath: $FIWARE_SERVICE_PATH" \
  -d '{
    "description": "Subscription for weather data to QuantumLeap",
    "subject": {
      "entities": [
        {
          "id": "WeatherObserved:Natal",
          "type": "WeatherObserved"
        }
      ]
    },
    "notification": {
      "http": {
        "url": "http://quantumleap:8668/v2/notify" 
      },
      "attrs": ["temperature", "humidity", "weatherCode", "location", "dateObserved"],
      "metadata": ["dateCreated", "dateModified"]
    },
    "throttling": 5
  }'