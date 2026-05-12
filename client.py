import asyncio
import websockets
import json
import base64
from datetime import datetime


async def send_test_frame():
    uri = "wss://pier-test-websocket.onrender.com/ws/frames"

    print(f"Conectando em: {uri}")

    async with websockets.connect(uri, open_timeout=60) as websocket:
        fake_image_bytes = b"imagem_teste_render"
        fake_image_base64 = base64.b64encode(fake_image_bytes).decode("utf-8")

        payload = {
            "frame_id": 1,
            "timestamp": datetime.utcnow().isoformat(),
            "latitude": -22.9099,
            "longitude": -47.0626,
            "image": fake_image_base64
        }

        await websocket.send(json.dumps(payload))

        response = await websocket.recv()
        print("Resposta do servidor:")
        print(response)


asyncio.run(send_test_frame())