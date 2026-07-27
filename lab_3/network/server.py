import socket
import threading
import time

from .protocol import decode_messages, encode_message

class PongServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self.server_socket = None
        self.running = False

        self.clients = {}
        self.client_buffers = {}

        self.inputs = {
            "left": "stop",
            "right": "stop",
        }

        self.state = {
            "ball": {
                "x": 500.0,
                "y": 300.0,
                "vx": 5.0,
                "vy": 5.0,
                "size": 18,
            },
            "left_paddle": {
                "y": 245.0,
                "height": 110,
                "speed": 7.0,
            },
            "right_paddle": {
                "y": 245.0,
                "height": 110,
                "speed": 7.0,
            },
            "score": {
                "left": 0,
                "right": 0,
            },
            "field": {
                "width": 1000,
                "height": 600,
            },
            "status": "waiting",
        }

        self.lock = threading.Lock()

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#cоздаётся серверный сокет, привязывается к адресу и начинает слушать подключения.
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(2)
        self.server_socket.settimeout(0.5)

        self.running = True
        #первый потом принимает клиентов, второй обновляет игру
        accept_thread = threading.Thread(target=self.accept_clients, daemon=True)
        accept_thread.start()

        game_thread = threading.Thread(target=self.game_loop, daemon=True)
        game_thread.start()

        print(f"Server started on {self.host}:{self.port}")

        try:
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.running = False

        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except OSError:
                pass

        for client_socket in list(self.clients.values()):
            try:
                client_socket.close()
            except OSError:
                pass

        print("Server stopped")

    def accept_clients(self):
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            role = self.assign_role()
            if role is None:
                try:
                    client_socket.sendall(
                        encode_message({
                            "type": "error",
                            "message": "Server is full"
                        })
                    )
                    client_socket.close()
                except OSError:
                    pass
                continue

            with self.lock:
                self.clients[role] = client_socket
                self.client_buffers[role] = ""

            print(f"Client connected: {address}, role={role}")

            try:
                client_socket.sendall(
                    encode_message({
                        "type": "welcome",
                        "role": role,
                    })
                )
            except OSError:
                continue

            self.update_status()

            client_thread = threading.Thread(
                target=self.handle_client,
                args=(role, client_socket),
                daemon=True,
            )
            client_thread.start()

    def assign_role(self):
        with self.lock:
            if "left" not in self.clients:
                return "left"
            if "right" not in self.clients:
                return "right"
        return None

    def update_status(self):
        with self.lock:
            if "left" in self.clients and "right" in self.clients:
                self.state["status"] = "playing"
            else:
                self.state["status"] = "waiting"

    def handle_client(self, role: str, client_socket: socket.socket):#метод получает сообщение от конкретного клиента
        while self.running:
            try:
                data = client_socket.recv(4096)
            except OSError:
                break

            if not data:
                break

            with self.lock:
                text = data.decode("utf-8")
                self.client_buffers[role] += text

                messages, rest = decode_messages(self.client_buffers[role])
                self.client_buffers[role] = rest

            for message in messages:
                self.process_message(role, message)

        print(f"Client disconnected: role={role}")
        self.remove_client(role)

    def remove_client(self, role: str):
        with self.lock:
            client_socket = self.clients.pop(role, None)
            self.client_buffers.pop(role, None)
            self.inputs[role] = "stop"

        if client_socket is not None:
            try:
                client_socket.close()
            except OSError:
                pass

        self.update_status()

    def process_message(self, role: str, message: dict):
        message_type = message.get("type")

        if message_type == "input":
            action = message.get("action")
            if action in ("up", "down", "stop"):
                with self.lock:
                    self.inputs[role] = action

    def game_loop(self):
        fps = 60
        delay = 1 / fps

        while self.running:
            with self.lock:
                if self.state["status"] == "playing":
                    self.update_paddles()
                    self.update_ball()

                snapshot = self.build_snapshot()

            self.broadcast(snapshot)
            time.sleep(delay)

    def update_paddles(self):
        left = self.state["left_paddle"]
        right = self.state["right_paddle"]
        field_height = self.state["field"]["height"]

        self.apply_input(left, self.inputs["left"], field_height)
        self.apply_input(right, self.inputs["right"], field_height)

    def apply_input(self, paddle: dict, action: str, field_height: int):
        if action == "up":
            paddle["y"] -= paddle["speed"]
        elif action == "down":
            paddle["y"] += paddle["speed"]

        if paddle["y"] < 0:
            paddle["y"] = 0

        max_y = field_height - paddle["height"]
        if paddle["y"] > max_y:
            paddle["y"] = max_y

    def update_ball(self):
        ball = self.state["ball"]
        field = self.state["field"]

        ball["x"] += ball["vx"]
        ball["y"] += ball["vy"]

        if ball["y"] <= 0:
            ball["y"] = 0
            ball["vy"] *= -1

        if ball["y"] + ball["size"] >= field["height"]:
            ball["y"] = field["height"] - ball["size"]
            ball["vy"] *= -1

        self.handle_paddle_collision("left")
        self.handle_paddle_collision("right")

        if ball["x"] + ball["size"] < 0:
            self.state["score"]["right"] += 1
            self.reset_ball(direction=1)

        if ball["x"] > field["width"]:
            self.state["score"]["left"] += 1
            self.reset_ball(direction=-1)

    def handle_paddle_collision(self, side: str):
        ball = self.state["ball"]

        if side == "left":
            paddle_x = 40
            paddle = self.state["left_paddle"]

            intersects_x = ball["x"] <= paddle_x + 20 and ball["x"] + ball["size"] >= paddle_x
            intersects_y = (
                ball["y"] + ball["size"] >= paddle["y"]
                and ball["y"] <= paddle["y"] + paddle["height"]
            )

            if intersects_x and intersects_y and ball["vx"] < 0:
                ball["x"] = paddle_x + 20
                ball["vx"] *= -1

        elif side == "right":
            field_width = self.state["field"]["width"]
            paddle_x = field_width - 40 - 20
            paddle = self.state["right_paddle"]

            intersects_x = ball["x"] + ball["size"] >= paddle_x and ball["x"] <= paddle_x + 20
            intersects_y = (
                ball["y"] + ball["size"] >= paddle["y"]
                and ball["y"] <= paddle["y"] + paddle["height"]
            )

            if intersects_x and intersects_y and ball["vx"] > 0:
                ball["x"] = paddle_x - ball["size"]
                ball["vx"] *= -1

    def reset_ball(self, direction: int):
        ball = self.state["ball"]
        field = self.state["field"]

        ball["x"] = field["width"] / 2 - ball["size"] / 2
        ball["y"] = field["height"] / 2 - ball["size"] / 2
        ball["vx"] = abs(ball["vx"]) * direction
        ball["vy"] = 5.0

    def build_snapshot(self):
        return {
            "type": "state",
            "state": self.state,
        }

    def broadcast(self, message: dict):
        encoded = encode_message(message)

        disconnected_roles = []

        with self.lock:
            for role, client_socket in self.clients.items():
                try:
                    client_socket.sendall(encoded)
                except OSError:
                    disconnected_roles.append(role)

        for role in disconnected_roles:
            self.remove_client(role)


if __name__ == "__main__":
    server = PongServer(host="0.0.0.0", port=5000)
    server.start()