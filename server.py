# Backend (server.py)
import os
import requests
import json
import re
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/", StaticFiles(directory="static", html=True), name="static")

RECALL_API_KEY = os.getenv("RECALL_API_KEY")
BASE_URL = "https://us-west-2.recall.ai/api/v1/bot/"

class MeetingRequest(BaseModel):
    meeting_url: str

def is_valid_meeting_url(meeting_url):
    pattern = r"https://meet\.google\.com/[a-zA-Z0-9]+"
    return re.match(pattern, meeting_url) is not None

def create_bot(meeting_url):
    # Data payload for bot creation
    data = {
        "meeting_url": meeting_url,
        "recording_config": {
        "realtime_endpoints": [
        {
            "type": "webhook",
            "url": "http://127.0.0.1:8000/api/webhook/recall/transcript",
            "events": ["transcript.data", "transcript.partial_data"]
        }
        ]
        }
    }

    # Headers for the request
    headers = {
        "Authorization": RECALL_API_KEY,
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.post(BASE_URL, headers=headers, data=json.dumps(data))
    print("Status Code:", response.status_code)
    print("Response Body:", response.json())

    if response.status_code != 200:
        print("Error:", response.json())
        raise Exception(f"Failed to create bot: {response.json()}")

    # Return response JSON
    return response.json()

@app.post("/start_bot")
async def start_bot(request: MeetingRequest):
    if not is_valid_meeting_url(request.meeting_url):
        return {"error": "Invalid Google Meet URL"}
    bot_response = create_bot(request.meeting_url)
    return {"bot_id": bot_response.get("bot_id")}

@app.post("/api/webhook/recall/transcript")
async def recall_webhook(data: dict):
    print("Webhook Data Received:", data)  # Debugging
    return {"status": "ok"}

@app.websocket("/transcript/{bot_id}")
async def transcript_feed(websocket: WebSocket, bot_id: str):
    await websocket.accept()
    # Simulate streaming transcript data
    for i in range(10):  # Example loop to send mock data
        await websocket.send_text(f"Transcript line {i+1}: This is a test transcript for bot {bot_id}")