import asyncio
import json
import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import uvicorn
import argparse

# Config
DEFAULT_METRICS_PATH = "results/multi_agent_complex_maze_checkpoints/metrics.json"

# Setup FastAPI + SocketIO
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
socket_app = socketio.ASGIApp(sio, app)

# Global State
last_mtime = 0
CACHE = []

async def load_historical_data():
    global CACHE
    if os.path.exists(DEFAULT_METRICS_PATH):
        try:
             with open(DEFAULT_METRICS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    CACHE = data
                    print(f"📂 Loaded {len(CACHE)} historical records.")
        except Exception as e:
            print(f"Error loading history: {e}")

async def watch_file(file_path):
    global last_mtime, CACHE
    print(f"👀 Watching file: {file_path}")
    
    while True:
        try:
            if os.path.exists(file_path):
                mtime = os.path.getmtime(file_path)
                if mtime > last_mtime:
                    last_mtime = mtime
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)
                            if data and isinstance(data, list):
                                # Update Cache
                                CACHE = data
                                
                                # Send ONLY the last item as update
                                last_entry = data[-1]
                                await sio.emit('new_metric', last_entry)
                                print(f"📡 Broadcasted Episode {last_entry.get('episode', '?')}")
                        except json.JSONDecodeError:
                            pass
            else:
                # print(f"⚠️ File not found: {file_path}")
                pass
                
        except Exception as e:
            print(f"Error watching file: {e}")
            
        await asyncio.sleep(1.0)

@sio.on('connect')
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    # Send history immediately
    if CACHE:
        # Send last 50 points
        history = CACHE[-50:]
        await sio.emit('history', history, to=sid)
        print(f"📜 Sent history ({len(history)} items) to {sid}")

@app.on_event("startup")
async def startup_event():
    await load_historical_data()
    asyncio.create_task(watch_file(DEFAULT_METRICS_PATH))

@app.get("/")
def read_root():
    return {"status": "Dashboard Backend Running", "records": len(CACHE)}
