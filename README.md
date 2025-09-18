In one terminal:
```bash
source venv/scripts/activate
fastapi dev
```

In another:
```bash
source venv/scripts/activate
python chat_watcher.py
```

YT-Chat <-> FastAPI <-> OBS

YT-Chat listener intercepts all chat messages.
Evaluates rules on each message.
Rules trigger OBS events via WebSockets.

Rules need a queue and a cooldown.

Clock should reset after the pre-show, upon 1st joining the lounge
Send a message to the chat_watcher or websocket_processor that resets
the chat count and the clock.

