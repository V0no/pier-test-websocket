import asyncio
import websockets
import json
import base64
import cv2
import time
from datetime import datetime
import socket


RENDER_WS_URL = "wss://pier-test-websocket.onrender.com/ws/frames"

FPS_ENVIO = 5
JPEG_QUALITY = 75


async def send_webcam_frames():
        
    tello_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tello_address = ('192.168.10.2', 8889)

    print("Despertando o Tello...")
    tello_sock.sendto(b'command', tello_address)
    time.sleep(1)
    tello_sock.sendto(b'streamon', tello_address)
    time.sleep(2)
    
    cap = cv2.VideoCapture('udp://@0.0.0.0:11111')

    if not cap.isOpened():
        print("Erro: não foi possível acessar a webcam.")
        return

    frame_id = 0
    intervalo = 1 / FPS_ENVIO

    print(f"Conectando em: {RENDER_WS_URL}")

    async with websockets.connect(RENDER_WS_URL, open_timeout=60) as websocket:
        print("Conectado ao WebSocket.")

        while True:
            ret, frame = cap.read()

            if not ret:
                print("Erro ao capturar frame da webcam.")
                break

            frame_id += 1

            encode_params = [
                int(cv2.IMWRITE_JPEG_QUALITY),
                JPEG_QUALITY
            ]

            success, buffer = cv2.imencode(".jpg", frame, encode_params)

            if not success:
                print("Erro ao codificar frame em JPEG.")
                continue

            image_base64 = base64.b64encode(buffer).decode("utf-8")

            payload = {
                "frame_id": frame_id,
                "timestamp": datetime.utcnow().isoformat(),
                "latitude": -22.9099,
                "longitude": -47.0626,
                "image": image_base64
            }

            await websocket.send(json.dumps(payload))

            response = await websocket.recv()
            print(f"Frame {frame_id} enviado | Resposta: {response}")

            time.sleep(intervalo)

    cap.release()


asyncio.run(send_webcam_frames())
