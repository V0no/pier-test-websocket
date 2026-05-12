from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from collections import deque
import base64
import json
import os

app = FastAPI(title="Pier Drone Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Buffer simples para guardar os últimos frames recebidos
FRAME_BUFFER_SIZE = 100
frames_buffer = deque(maxlen=FRAME_BUFFER_SIZE)

# Mock simples de placas com sinistro aberto
MOCK_SINISTROS = {
    "ABC1D23": {
        "status": "roubado",
        "modelo": "Honda Civic",
        "cor": "preto"
    },
    "XYZ9A87": {
        "status": "furtado",
        "modelo": "Toyota Corolla",
        "cor": "prata"
    }
}


@app.get("/")
def root():
    return {
        "message": "Pier Drone Backend online",
        "status": "ok"
    }


@app.get("/health")
def health():
    return {
        "status": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "buffer_size": len(frames_buffer)
    }


@app.get("/frames/latest")
def get_latest_frames():
    """
    Retorna metadados dos últimos frames recebidos.
    Não retorna a imagem completa para evitar resposta pesada.
    """
    return {
        "total": len(frames_buffer),
        "frames": [
            {
                "frame_id": frame["frame_id"],
                "timestamp": frame["timestamp"],
                "latitude": frame.get("latitude"),
                "longitude": frame.get("longitude"),
                "received_at": frame["received_at"]
            }
            for frame in list(frames_buffer)[-10:]
        ]
    }


@app.get("/sinistros/{placa}")
def consultar_sinistro(placa: str):
    """
    Consulta mock de sinistros.
    No futuro, isso pode ser substituído pela API/banco da Pier.
    """
    placa = placa.upper()

    if placa in MOCK_SINISTROS:
        return {
            "match": True,
            "placa": placa,
            "dados": MOCK_SINISTROS[placa]
        }

    return {
        "match": False,
        "placa": placa,
        "dados": None
    }


@app.websocket("/ws/frames")
async def websocket_frames(websocket: WebSocket):
    await websocket.accept()
    print("Cliente conectado ao WebSocket")

    try:
        while True:
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)

                frame_id = payload.get("frame_id")
                timestamp = payload.get("timestamp")
                latitude = payload.get("latitude")
                longitude = payload.get("longitude")
                image_base64 = payload.get("image")

                if not frame_id or not timestamp or not image_base64:
                    await websocket.send_json({
                        "status": "error",
                        "message": "frame_id, timestamp e image são obrigatórios"
                    })
                    continue

                frame_data = {
                    "frame_id": frame_id,
                    "timestamp": timestamp,
                    "latitude": latitude,
                    "longitude": longitude,
                    "image": image_base64,
                    "received_at": datetime.utcnow().isoformat()
                }

                frames_buffer.append(frame_data)

                # Aqui futuramente entra YOLO + OCR
                # Por enquanto, apenas simulamos o recebimento do frame

                await websocket.send_json({
                    "status": "ok",
                    "message": "frame recebido",
                    "frame_id": frame_id,
                    "buffer_size": len(frames_buffer)
                })

                print(f"Frame recebido: {frame_id} | Buffer: {len(frames_buffer)}")

            except json.JSONDecodeError:
                await websocket.send_json({
                    "status": "error",
                    "message": "JSON inválido"
                })

            except Exception as e:
                await websocket.send_json({
                    "status": "error",
                    "message": str(e)
                })

    except WebSocketDisconnect:
        print("Cliente desconectado do WebSocket")