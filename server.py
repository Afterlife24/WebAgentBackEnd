import os
import uuid
import asyncio
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from livekit import api
from livekit.api import LiveKitAPI, ListRoomsRequest
from mangum import Mangum  # For AWS Lambda

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# -------------------------------
# Helper functions
# -------------------------------
async def generate_room_name():
    name = "room-" + str(uuid.uuid4())[:8]
    rooms = await get_rooms()
    while name in rooms:
        name = "room-" + str(uuid.uuid4())[:8]
    return name

async def get_rooms():
    client = LiveKitAPI()
    rooms = await client.room.list_rooms(ListRoomsRequest())
    await client.aclose()
    return [room.name for room in rooms.rooms]

# -------------------------------
# Routes
# -------------------------------
@app.route("/getToken", methods=["GET"])
def get_token():
    """
    Synchronous Flask route, wraps async LiveKit calls inside asyncio.run()
    so it works both locally and in Lambda.
    """
    name = request.args.get("name", "my name")
    room = request.args.get("room", None)

    if not room:
        room = asyncio.run(generate_room_name())

    token = api.AccessToken(
        os.getenv("LIVEKIT_API_KEY"),
        os.getenv("LIVEKIT_API_SECRET"),
    ).with_identity(name).with_name(name).with_grants(
        api.VideoGrants(room_join=True, room=room)
    )

    return jsonify({"token": token.to_jwt(), "room": room})

# -------------------------------
# Lambda handler
# -------------------------------
handler = Mangum(app)

# -------------------------------
# Local run
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
