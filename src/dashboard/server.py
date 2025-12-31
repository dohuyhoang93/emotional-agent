import asyncio
import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

# Config
import argparse
import glob

# Config - Dynamic Resolution
def resolve_metrics_path():
    # 1. Check CLI args (if run directly)
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Path to metrics.jsonl file", default=None)
    # Ignore unknown args (FastAPI/Uvicorn might pass others)
    args, _ = parser.parse_known_args()
    
    if args.file and os.path.exists(args.file):
        return args.file
        
    # 2. Env Var
    if os.environ.get("METRICS_FILE"):
        return os.environ.get("METRICS_FILE")

    # 3. Auto-discover latest in results/
    base_results = "results"
    if os.path.exists(base_results):
        # Look for all metrics.jsonl recursively
        candidates = glob.glob(os.path.join(base_results, "**", "metrics.jsonl"), recursive=True)
        if candidates:
            # Sort by modification time (newest first)
            latest = max(candidates, key=os.path.getmtime)
            print(f"🔍 Auto-detected latest experiment: {latest}")
            return latest
    
    return "metrics.jsonl" # Fallback

METRICS_PATH = resolve_metrics_path()
print(f"🚀 Dashboard monitoring: {METRICS_PATH}")

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
last_size = 0  # Track file size for append-only reading
CACHE = []

def parse_jsonl(file_path):
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        # Ensure compatibility with frontend
                        # Frontend expects entry.metrics to exist or keys to be flat
                        # Our new format is {episode, timestamp, metrics: {...}}
                        # This works out of the box with the frontend logic:
                        # if (d.metrics.global) ... else if (d.metrics.avg_reward)
                        data.append(entry)
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        print(f"Error reading JSONL: {e}")
    return data

async def load_historical_data():
    global CACHE, last_size
    if os.path.exists(METRICS_PATH):
        CACHE = parse_jsonl(METRICS_PATH)
        last_size = os.path.getsize(METRICS_PATH)
        print(f"📂 Loaded {len(CACHE)} historical records.")

async def watch_file(file_path):
    global last_mtime, CACHE, last_size
    print(f"👀 Watching file: {file_path}")
    
    while True:
        try:
            if os.path.exists(file_path):
                current_size = os.path.getsize(file_path)
                mtime = os.path.getmtime(file_path)
                
                if current_size > last_size:
                    # Append mode: Read only new data
                    # For simplicity, we can just re-read all if small, but let's try to be smart
                    # Actually, re-reading is safer for now to avoid complexity with line boundaries
                    
                    new_data = parse_jsonl(file_path)
                    
                    if len(new_data) > len(CACHE):
                        # Identify new items
                        added_items = new_data[len(CACHE):]
                        CACHE = new_data
                        last_size = current_size
                        last_mtime = mtime
                        
                        for item in added_items:
                            await sio.emit('new_metric', item)
                            print(f"📡 Broadcasted Episode {item.get('episode', '?')}")
                
        except Exception as e:
            print(f"Error watching file: {e}")
            
        await asyncio.sleep(1.0)

@sio.on('connect')
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    
    # Send configuration/meta info
    await sio.emit('experiment_info', {
        'path': METRICS_PATH,
        'filename': os.path.basename(METRICS_PATH),
        'records': len(CACHE)
    }, to=sid)
    
    # Send history immediately
    if CACHE:
        # Send last 50 points
        history = CACHE[-50:]
        await sio.emit('history', history, to=sid)
        print(f"📜 Sent history ({len(history)} items) to {sid}")

@app.on_event("startup")
async def startup_event():
    await load_historical_data()
    asyncio.create_task(watch_file(METRICS_PATH))

@app.get("/")
def read_root():
    return {
        "status": "Dashboard Backend Running", 
        "records": len(CACHE),
        "monitored_file": METRICS_PATH
    }
