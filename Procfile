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
notification_service: uvicorn notification_service.app:app --port 5400 --host 0.0.0.0 --reload
webhook_dispatcher: python3 workers/webhook_dispatcher.py
mail_dispatcher: python3 workers/mail_dispatcher.py
smtp_server: python3 -m aiosmtpd -n -d -l 0.0.0.0       # Default Port = 8025