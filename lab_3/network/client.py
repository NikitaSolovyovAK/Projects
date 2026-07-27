import socket
import threading

from .protocol import decode_messages, encode_message
"""Данный код реализует сетевого клиента для игры в Pong, работающего по протоколу TCP. 
Он подключается к серверу, получает от него назначенную роль (левый или правый игрок),
 принимает обновления игрового состояния и отправляет команды управления (вверх/вниз/стоп)."""

class PongClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self.socket = None
        self.running = False

        self.buffer = ""
        self.receiver_thread = None # поток-приёмник

        self.role = None
        self.latest_state = None
        self.last_error = None

        self.lock = threading.Lock()

    def connect(self):
        if self.running:
            return True

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.running = True

            self.receiver_thread = threading.Thread(
                target=self.receive_loop,
                daemon=True,
            )
            self.receiver_thread.start()
            return True

        except OSError as error:
            self.last_error = str(error)
            self.running = False
            self.socket = None
            return False

    def disconnect(self):
        self.running = False

        if self.socket is not None:
            try:
                self.socket.close()
            except OSError:
                pass

        self.socket = None

    def receive_loop(self):
        while self.running:
            try:
                data = self.socket.recv(4096)
            except OSError:
                break

            if not data:
                break

            text = data.decode("utf-8")

            with self.lock:
                self.buffer += text
                messages, rest = decode_messages(self.buffer)
                self.buffer = rest

            for message in messages:
                self.process_message(message)

        self.running = False

        if self.socket is not None:
            try:
                self.socket.close()
            except OSError:
                pass

        self.socket = None

    def process_message(self, message: dict):
        message_type = message.get("type")

        if message_type == "welcome":
            with self.lock:
                self.role = message.get("role")

        elif message_type == "state":
            with self.lock:
                self.latest_state = message.get("state")

        elif message_type == "error":
            with self.lock:
                self.last_error = message.get("message", "Unknown server error")

    def send_input(self, action: str):#метод отправляет действие игрока на сервер
        if not self.running or self.socket is None:
            return

        if action not in ("up", "down", "stop"):
            return

        message = {
            "type": "input",
            "action": action,
        }

        try:
            self.socket.sendall(encode_message(message))
        except OSError as error:
            self.last_error = str(error)
            self.disconnect()

    def get_role(self):
        with self.lock:
            return self.role

    def get_state(self):
        with self.lock:
            return self.latest_state

    def get_error(self):
        with self.lock:
            return self.last_error

    def is_connected(self):
        return self.running

if __name__ == "__main__":
    client = PongClient(host="127.0.0.1", port=5000)

    if not client.connect():
        print("Connection failed:", client.get_error())
    else:
        print("Connected to server")

        import time

        for _ in range(20):
            print("Role:", client.get_role())
            print("State:", client.get_state())
            time.sleep(0.5)

        client.disconnect()