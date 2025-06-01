import socketio
import uuid
import threading
import time

CLIENT_ID = "TEST"

sio = socketio.Client(
    logger=True,
    engineio_logger=True,
    reconnection=True,
    reconnection_attempts=5
)

def send_ping():
    while True:
        time.sleep(600)
        try:
            data = {
                'clientId': CLIENT_ID
            }
            print("Sending ping with data:", data)
            sio.emit('client_ping', data)
            print("Sent ping")
        except Exception as e:
            print(f"Error sending ping: {e}")
            break

@sio.event
def connect():
    print(f'Connected to server as {CLIENT_ID}')
    print(f'Transport: {sio.transport()}')
    print(f'Socket ID: {sio.sid}')
    
    sio.emit('client_init', {
        'clientId': CLIENT_ID,
    })
    print('Sent client_init')

    threading.Thread(target=send_ping, daemon=True).start()

@sio.event
def force_ping():
    print('Received force_ping from server')
    data = {
        'clientId': CLIENT_ID
    }
    sio.emit('client_ping', data)
    print('Sent immediate ping response')

@sio.event
def connect_error(data):
    print(f"Connection error: {data}")

@sio.event
def disconnect():
    print('Disconnected from server')

try:
    sio.connect('http://localhost:3001', wait_timeout=10)
    sio.wait()
except Exception as e:
    print(f"Connection failed: {e}")