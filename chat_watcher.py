import asyncio
import time

import pytchat
import requests
from urllib.parse import urlparse

youtube_url = input("Drop the YouTube URL here (ex: https://www.youtube.com/watch?v=XXXXXXXXX)")

url = urlparse(youtube_url)
if url.hostname == "youtu.be" or "live" in url.path:
    stream_id = url.path.split("/")[-1]
elif "youtube.com" in url.hostname:
    stream_id = url.query[url.query.find('=')+1:]
else:
    print("No idea how to handle that URL. Giving up.")
    exit(1)

print()
print(f"streamID: {stream_id}")
print()

def OBS_is_up():
    try:
        response = requests.get("http://127.0.0.1:8000/health")
        if response.status_code != 200:
            print("Got an error health checking FastAPI")
            print(response.status_code, print(response.text))
            return False
        return True
    except requests.exceptions.ConnectionError as ce:
        print("Can't reach FastAPI, is it running?")
        return False

async def clock():
    start_time = time.time()
    while True:
        while True:
            if OBS_is_up():
                break
            else:
                time.sleep(2)

        seconds = int(time.time() - start_time)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        payload = {"text": "{:02d}:{:02d}:{:02d}".format(hours, minutes, remaining_seconds)}
        requests.post("http://127.0.0.1:8000/clock", json=payload)

        battery_remaining = str(round(4.20 - (seconds / (1.5*60*60)), 2))
        requests.post("http://127.0.0.1:8000/battery", json={"volts": battery_remaining})
        await asyncio.sleep(1)


async def watch_chat():
    try:
        while True:
            print("Booting Up")
            while True:
                if OBS_is_up():
                    break
                else:
                    time.sleep(2)
            print("Connected to FastAPI")

            chat = pytchat.create(video_id=stream_id)
            print("Connected to YT-Chat")

            while chat.is_alive():
                await asyncio.sleep(0.1)
                for c in chat.get().sync_items():
                    request_data = {
                        "type": c.type,
                        "id": c.id,
                        "datetime": c.datetime,
                        "author": {
                            "name": c.author.name,
                            "imageUrl": c.author.imageUrl,
                            "isVerified": c.author.isVerified,
                            "isChatOwner": c.author.isChatOwner,
                            "isChatSponsor": c.author.isChatSponsor,
                            "isChatModerator": c.author.isChatModerator
                        },
                        "amountValue": c.amountValue,
                        "amountString": c.amountString,
                        "currency": c.currency,
                        "message": c.message,
                        "messageEx": c.messageEx,
                    }
                    try:
                        response = requests.post("http://127.0.0.1:8000/chat", json=request_data)
                        print(request_data)
                        if 200 >= response.status_code >= 299:
                            print("Got an error sending chat data to FastAPI")
                            print(response.status_code, print(response.text))
                            raise
                    except requests.exceptions.ConnectionError as ce:
                        print("Can't reach FastAPI, is it running?")
                        raise

    except KeyboardInterrupt as kbe:
        exit(1)
    except Exception as e:
        print(type(e), str(e))
        print("Restarting watcher...")
        time.sleep(1)

async def multi_thread_this():
    run_multiple_tasks_at_once = await asyncio.gather(clock(), watch_chat())

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(multi_thread_this())