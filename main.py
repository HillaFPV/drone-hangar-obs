import logging
import json
from fastapi import FastAPI, WebSocket, status, Body, HTTPException, Response, Request, APIRouter, Depends

from chat_processor import ChatProcessor
from models.chat_models import ChatMessage, BatteryMessage, TextMessage
from websocket_processor import process_websocket
logging.basicConfig(filename="../logs/chat-processor.log",
                    filemode='a',
                    format='%(message)s',
                    level=logging.INFO)

logger = logging.getLogger('chat-processor')
logging.info("Starting chat processor")


app = FastAPI()


@app.get("/health")
def health():
    return {"message": "up"}


@app.websocket("/obs")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("OBS has connected to FastAPI")
    try:
        await websocket.accept()
        while True:
            data = await websocket.receive_text()
            process_websocket(data)
    except Exception as e:
        pass


chat_processor = ChatProcessor()

@app.post("/chat")
async def handle_chat(chat_message: ChatMessage):
    await chat_processor.process_chat(chat_message)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/chatter")
async def get_chatters():
    return Response(content=json.dumps({
        'chatters': chat_processor.chatters,
        'total': chat_processor.chat_total_count,
        'chat_pole_fill_amount': chat_processor.chat_pole_fill_amount},
        indent=2))

@app.get("/reset")
async def get_chatters():
    chat_processor.reset()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/reset-pole")
async def get_chatters():
    chat_processor.reset_pole()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.post("/battery")
async def set_battery(battery_message: BatteryMessage):
    chat_processor.set_battery(battery_message)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.post("/clock")
async def set_clock(text_message: TextMessage):
    chat_processor.set_clock(text_message)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.post("/text")
async def set_text(text_message: TextMessage):
    chat_processor.set_text(text_message)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
