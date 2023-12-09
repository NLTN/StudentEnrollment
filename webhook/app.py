import logging
from fastapi import FastAPI, Body

# Create the main FastAPI application instance
app = FastAPI()

# Logger
logging.basicConfig(filename=f'{__name__}.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

@app.post("/webhook")
async def receive_webhook(payload: dict = Body(...)):
    logging.info(payload)
    return {"message": "Webhook received successfully"}