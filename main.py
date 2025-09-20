import asyncio
import logging
import json
import time
from fastapi import BackgroundTasks, FastAPI, WebSocket, status, Body, HTTPException, Response, Request, APIRouter, Depends
from pathlib import Path
from chat_processor import ChatProcessor
from models.chat_models import ChatMessage, BatteryMessage, TextMessage
from websocket_processor import process_websocket

Path("./logs").mkdir(parents=True, exist_ok=True)

logging.basicConfig(filename="./logs/chat-processor.log",
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
async def handle_chat_endpoint(chat_message: ChatMessage, background_tasks: BackgroundTasks):
    async def task(chat_message: ChatMessage):
        await chat_processor.process_chat(chat_message)

    background_tasks.add_task(task, chat_message)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/chatter")
async def get_chatters_endpoint():
    return Response(content=json.dumps({
        'chatters': chat_processor.chatters,
        'total': chat_processor.chat_total_count,
        'chat_pole_fill_amount': chat_processor.chat_pole_fill_amount},
        indent=2))

@app.get("/start")
async def start_endpoint(background_tasks: BackgroundTasks):
    async def task():
        chat_processor.start_time = time.time()
        while True:
            seconds = int(time.time() - chat_processor.start_time)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            remaining_seconds = seconds % 60
            payload = TextMessage(text="{:02d}:{:02d}:{:02d}".format(hours, minutes, remaining_seconds))
            chat_processor.set_clock(payload)

            battery_remaining = str(round(4.20 - (seconds / (1.5*60*60)), 2))
            payload = BatteryMessage(volts=battery_remaining)
            chat_processor.set_battery(payload)
            await asyncio.sleep(1)

    chat_processor.start()
    background_tasks.add_task(task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/reset")
async def reset_endpoint(background_tasks: BackgroundTasks):
    async def task():
        chat_processor.reset()
    background_tasks.add_task(task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.post("/battery")
async def set_battery(battery_message: BatteryMessage, background_tasks: BackgroundTasks):
    async def task(battery_message: BatteryMessage):
        chat_processor.set_battery(battery_message)

    background_tasks.add_task(task, battery_message)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.post("/clock")
async def set_clock(text_message: TextMessage, background_tasks: BackgroundTasks):
    async def task(text_message: TextMessage):
        chat_processor.set_clock(text_message)
    
    background_tasks.add_task(task, text_message)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.post("/text")
async def set_text(text_message: TextMessage, background_tasks: BackgroundTasks):
    async def task(text_message: TextMessage):
        chat_processor.set_text(text_message)

    background_tasks.add_task(task, text_message)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
