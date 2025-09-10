In one terminal:
```bash
fastapi dev
```

In another:
```bash
python chat_watcher.py
```

YT-Chat <-> FastAPI <-> OBS

YT-Chat listener intercepts all chat messages.
Evaluates rules on each message.
Rules trigger OBS events via WebSockets.

Rules need a queue and a cooldown.
