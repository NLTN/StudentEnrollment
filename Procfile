gateway: echo ./etc/krakend.json | entr -nrz krakend run --config etc/krakend.json --port $PORT
enrollment_service: uvicorn enrollment_service.app:app --port $PORT --host 0.0.0.0 --reload

# User service WITH database replications
user_service_primary: ./bin/litefs mount -config etc/primary.yml
user_service_secondary: ./bin/litefs mount -config etc/secondary.yml
user_service_tertiary: ./bin/litefs mount -config etc/tertiary.yml

# User service WITHOUT database replication
user_service: uvicorn user_service.app:app --port 5200 --host 0.0.0.0 --reload

dynamodb: sh ./bin/start-dynamodb.sh
redis: sh ./bin/start-redis-server.sh
rabbitmq: sh ./bin/start-rabbitmq.sh
webhook: uvicorn webhook.app:app --port 5500 --host 0.0.0.0 --reload