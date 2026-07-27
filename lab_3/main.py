import json
import os
import sys
import pygame

from game.ball import Ball
from game.bot import BotController
from game.leaderboard import Leaderboard
from game.paddle import Paddle
from game.sound_manager import SoundManager
from game.states import (
    GAME_OVER,
    HELP,
    LEADERBOARD,
    MENU,
    NAME_INPUT,
    ONLINE_CONNECT,
    ONLINE_PLAYING,
    PLAYING,
)
from game.ui import GameUI
from network.client import PongClient


def load_config():
    default_config = {
        "window_width": 1000,
        "window_height": 600,
        "fps": 60,
        "paddle_width": 20,
        "paddle_height": 110,
        "player_speed": 7.0,
        "bot_speed": 6.0,
        "paddle_margin": 40,
        "ball_size": 18,
        "ball_speed_x": 5.0,
        "ball_speed_y": 5.0,
        "max_ball_speed_x": 11.0,
        "winning_score": 5,
        "bot_tolerance": 18,
        "sounds": {
            "hit": "assets/sounds/hit.wav",
            "goal": "assets/sounds/goal.wav"
        },
        "music": {
            "background": "assets/music/background.mp3",
            "volume": 0.4
        }
    }

    config_path = os.path.join("config", "config.json")

    if not os.path.exists(config_path):
        return default_config

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return default_config

        merged_config = default_config.copy()
        merged_config.update(data)
        return merged_config

    except (json.JSONDecodeError, OSError):
        return default_config


class GameApp:
    def __init__(self):
        pygame.init()

        self.config = load_config()

        self.width = self.config["window_width"]
        self.height = self.config["window_height"]
        self.fps = self.config["fps"]

        self.paddle_width = self.config["paddle_width"]
        self.paddle_height = self.config["paddle_height"]
        self.player_speed = self.config["player_speed"]
        self.bot_speed = self.config["bot_speed"]
        self.paddle_margin = self.config["paddle_margin"]

        self.ball_size = self.config["ball_size"]
        self.ball_speed_x = self.config["ball_speed_x"]
        self.ball_speed_y = self.config["ball_speed_y"]

        self.winning_score = self.config["winning_score"]
        self.max_ball_speed_x = self.config["max_ball_speed_x"]
        self.bot_tolerance = self.config["bot_tolerance"]

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Pong")

        self.clock = pygame.time.Clock()
        self.running = True
        self.state = MENU

        self.bg_color = (15, 15, 22)
        self.line_color = (90, 90, 90)
        self.paddle_color = (255, 255, 255)

        self.player = self._create_paddle(
            x=self.paddle_margin,
            speed=self.player_speed,
        )
        self.bot = self._create_paddle(
            x=self.width - self.paddle_margin - self.paddle_width,
            speed=self.bot_speed,
        )
        self.ball = self._create_ball()

        self.bot_controller = BotController(
            paddle=self.bot,
            ball=self.ball,
            tolerance=self.bot_tolerance,
        )

        self.player_score = 0
        self.bot_score = 0

        self.score_font = pygame.font.SysFont("arial", 48, bold=True)
        self.info_font = pygame.font.SysFont("arial", 28)

        self.winner_text = ""
        self.latest_result = 0
        self.name_input = ""

        self.sound_manager = SoundManager(self.config)

        self.goal_text = ""
        self.goal_timer = 0
        self.goal_duration = 45

        self.hit_animation_timer = 0
        self.hit_animation_duration = 12

        self.menu_options = [
            "Начать игру",
            "Онлайн: подключиться",
            "Таблица рекордов",
            "Справка",
            "Выход",
        ]
        self.menu_selected_index = 0

        self.ui = GameUI(#создание объекта интерфейса(Для того чтобы этот файл не занимался напрямую всей отрисовкой)
            screen=self.screen,
            width=self.width,
            height=self.height,
            bg_color=self.bg_color,
            line_color=self.line_color,
            paddle_color=self.paddle_color,
            score_font=self.score_font,
            info_font=self.info_font,
        )

        leaderboard_path = os.path.join("data", "leaderboard.json")
        self.leaderboard = Leaderboard(leaderboard_path)

        self.online_client = None
        self.online_state = None
        self.online_role = None

        self.online_host = "127.0.0.1"
        self.online_port = 5000

        self.online_error = ""
        self.last_online_action = "stop"

    def _create_paddle(self, x: int, speed: float):
        start_y = (self.height - self.paddle_height) // 2

        return Paddle(
            x=x,
            y=start_y,
            width=self.paddle_width,
            height=self.paddle_height,
            speed=speed,
            screen_height=self.height,
        )

    def _create_ball(self):
        start_x = self.width // 2 - self.ball_size // 2
        start_y = self.height // 2 - self.ball_size // 2

        ball = Ball(
            x=start_x,
            y=start_y,
            size=self.ball_size,
            speed_x=self.ball_speed_x,
            speed_y=self.ball_speed_y,
            screen_width=self.width,
            screen_height=self.height,
        )
        ball.reset()
        return ball

    def start_new_match(self):
        self.player_score = 0
        self.bot_score = 0

        self.winner_text = ""
        self.latest_result = 0
        self.name_input = ""

        self.goal_text = ""
        self.goal_timer = 0
        self.hit_animation_timer = 0

        self.player.reset_to_center()
        self.bot.reset_to_center()
        self.ball.reset()

        self.state = PLAYING

    def finish_match(self):
        if self.player_score > self.bot_score:
            self.winner_text = "Вы победили!"
        else:
            self.winner_text = "Победил бот!"

        self.latest_result = self.player_score

        if self.latest_result > self.leaderboard.get_best_score():
            self.name_input = ""
            self.state = NAME_INPUT
        else:
            self.state = GAME_OVER

    def start_online_connection(self):
        self.online_error = ""
        self.online_client = PongClient(self.online_host, self.online_port)#создаёт клиент для подключения к серверу

        if not self.online_client.connect():
            self.online_error = self.online_client.get_error() or "Не удалось подключиться"
            self.state = MENU
            return

        self.state = ONLINE_CONNECT

    def update_online_connection(self):
        if self.online_client is None:
            self.state = MENU
            return

        error = self.online_client.get_error()
        if error:
            self.online_error = error
            self.state = MENU
            return

        role = self.online_client.get_role()#получаем роль от игрока и состояние игры от клиента
        state = self.online_client.get_state()

        if role is not None:
            self.online_role = role

        if state is not None:
            self.online_state = state

        if self.online_role is not None and self.online_state is not None:
            self.state = ONLINE_PLAYING

    def update_online_input(self):
        if self.online_client is None:
            return

        keys = pygame.key.get_pressed()

        action = "stop"
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            action = "up"
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            action = "down"

        if action != self.last_online_action:#команда отправляется если только она изменилась(для уменьшения сетевых сообщений)
            self.online_client.send_input(action)
            self.last_online_action = action

    def disconnect_online(self):
        if self.online_client is not None:
            self.online_client.disconnect()

        self.online_client = None
        self.online_state = None
        self.online_role = None
        self.last_online_action = "stop"

    def handle_events(self):
        for event in pygame.event.get():#Событийно-ориентированное программирование здесь реализовано через цикл обработки событий pygame. Программа не спрашивает пользователя напрямую через input(), а реагирует на события окна и клавиатуры.
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if self.state == MENU:
                    if event.key == pygame.K_UP:
                        self.menu_selected_index -= 1
                        if self.menu_selected_index < 0:
                            self.menu_selected_index = len(self.menu_options) - 1

                    elif event.key == pygame.K_DOWN:
                        self.menu_selected_index += 1
                        if self.menu_selected_index >= len(self.menu_options):
                            self.menu_selected_index = 0

                    elif event.key == pygame.K_RETURN:
                        selected_option = self.menu_options[self.menu_selected_index]

                        if selected_option == "Начать игру":
                            self.start_new_match()

                        elif selected_option == "Онлайн: подключиться":
                            self.start_online_connection()

                        elif selected_option == "Таблица рекордов":
                            self.state = LEADERBOARD

                        elif selected_option == "Справка":
                            self.state = HELP

                        elif selected_option == "Выход":
                            self.running = False

                elif self.state == GAME_OVER:
                    if event.key == pygame.K_RETURN:
                        self.state = MENU

                    elif event.key == pygame.K_ESCAPE:
                        self.running = False

                elif self.state == HELP:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        self.state = MENU

                elif self.state == LEADERBOARD:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        self.state = MENU

                elif self.state == NAME_INPUT:
                    if event.key == pygame.K_RETURN:
                        name = self.name_input.strip()
                        if name:
                            self.leaderboard.add_record(name, self.latest_result)
                            self.state = LEADERBOARD

                    elif event.key == pygame.K_BACKSPACE:
                        self.name_input = self.name_input[:-1]

                    elif event.key == pygame.K_ESCAPE:
                        self.state = GAME_OVER

                    else:
                        if event.unicode.isprintable() and len(self.name_input) < 12:
                            self.name_input += event.unicode

                elif self.state == ONLINE_CONNECT:
                    if event.key == pygame.K_ESCAPE:
                        self.disconnect_online()
                        self.state = MENU

                elif self.state == ONLINE_PLAYING:
                    if event.key == pygame.K_ESCAPE:
                        self.disconnect_online()
                        self.state = MENU

    def update_player(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.player.move_up()

        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.player.move_down()

    def handle_paddle_collision(self, paddle: Paddle, is_left_paddle: bool):
        if not self.ball.rect.colliderect(paddle.rect):
            return

        if is_left_paddle and self.ball.vx < 0:
            self.ball.rect.left = paddle.rect.right
        elif not is_left_paddle and self.ball.vx > 0:
            self.ball.rect.right = paddle.rect.left
        else:
            return

        self.ball.x = float(self.ball.rect.x)

        self.ball.vx *= -1.05

        if self.ball.vx > self.max_ball_speed_x:
            self.ball.vx = self.max_ball_speed_x
        elif self.ball.vx < -self.max_ball_speed_x:
            self.ball.vx = -self.max_ball_speed_x

        offset = (
            self.ball.rect.centery - paddle.rect.centery
        ) / (paddle.rect.height / 2)

        self.ball.vy += offset * 2

        max_vertical_speed = 10
        if self.ball.vy > max_vertical_speed:
            self.ball.vy = max_vertical_speed
        elif self.ball.vy < -max_vertical_speed:
            self.ball.vy = -max_vertical_speed

        self.hit_animation_timer = self.hit_animation_duration
        self.sound_manager.play("hit")

    def register_goal(self, scorer: str):
        if scorer == "player":
            self.player_score += 1
            self.goal_text = "ГОЛ! Очко игрока"
        elif scorer == "bot":
            self.bot_score += 1
            self.goal_text = "ГОЛ! Очко бота"

        self.goal_timer = self.goal_duration
        self.sound_manager.play("goal")

        if self.player_score >= self.winning_score or self.bot_score >= self.winning_score:
            self.finish_match()
        else:
            self.player.reset_to_center()
            self.bot.reset_to_center()

            if scorer == "player":
                self.ball.reset(direction_x=1)
            else:
                self.ball.reset(direction_x=-1)

    def update_ball(self):
        self.ball.update()

        if self.ball.rect.top <= 0:
            self.ball.rect.top = 0
            self.ball.y = float(self.ball.rect.y)
            self.ball.bounce_vertical()

        if self.ball.rect.bottom >= self.height:
            self.ball.rect.bottom = self.height
            self.ball.y = float(self.ball.rect.y)
            self.ball.bounce_vertical()

        self.handle_paddle_collision(self.player, is_left_paddle=True)
        self.handle_paddle_collision(self.bot, is_left_paddle=False)

        if self.ball.rect.right < 0:
            self.register_goal("bot")

        if self.ball.rect.left > self.width:
            self.register_goal("player")

    def update(self):
        if self.goal_timer > 0:
            self.goal_timer -= 1

        if self.hit_animation_timer > 0:
            self.hit_animation_timer -= 1

        if self.state == PLAYING:
            if self.goal_timer > 0:
                return

            self.update_player()
            self.bot_controller.update()
            self.update_ball()

        elif self.state == ONLINE_CONNECT:
            self.update_online_connection()

        elif self.state == ONLINE_PLAYING:
            self.update_online_connection()
            self.update_online_input()

    def draw(self):
        if self.state == MENU:
            self.ui.draw_menu(
                options=self.menu_options,
                selected_index=self.menu_selected_index,
            )

        elif self.state == PLAYING:
            self.ui.draw_playing(
                player=self.player,
                bot=self.bot,
                ball=self.ball,
                player_score=self.player_score,
                bot_score=self.bot_score,
                goal_text=self.goal_text,
                goal_timer=self.goal_timer,
                goal_duration=self.goal_duration,
                hit_animation_timer=self.hit_animation_timer,
                hit_animation_duration=self.hit_animation_duration,
            )

        elif self.state == GAME_OVER:
            self.ui.draw_game_over(
                winner_text=self.winner_text,
                player_score=self.player_score,
                bot_score=self.bot_score,
            )

        elif self.state == HELP:
            self.ui.draw_help()

        elif self.state == LEADERBOARD:
            self.ui.draw_leaderboard(self.leaderboard.records)

        elif self.state == NAME_INPUT:
            self.ui.draw_name_input(
                name_input=self.name_input,
                result_score=self.latest_result,
            )

        elif self.state == ONLINE_CONNECT:
            self.ui.draw_online_connect()

        elif self.state == ONLINE_PLAYING:
            if self.online_state is not None:
                self.ui.draw_online_playing(
                    online_state=self.online_state,
                    role=self.online_role,
                )
            else:
                self.ui.draw_online_connect()

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.fps)

        self.disconnect_online()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    app = GameApp()
    app.run()