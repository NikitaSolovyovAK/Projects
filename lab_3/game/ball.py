import random
import pygame


DEFAULT_BALL_COLOR = (255, 255, 255)
TRAIL_COLOR = (120, 120, 120)


class Ball:
    def __init__(
        self,
        x: int,
        y: int,
        size: int,
        speed_x: float,
        speed_y: float,
        screen_width: int,
        screen_height: int,
    ):
        self.rect = pygame.Rect(x, y, size, size)

        self.x = float(x)
        self.y = float(y)

        self.base_speed_x = speed_x
        self.base_speed_y = speed_y

        self.vx = speed_x
        self.vy = speed_y

        self.screen_width = screen_width
        self.screen_height = screen_height

        # История позиций нужна для простой анимации следа за мячом.
        self.trail_points = []
        self.max_trail_length = 10

    def reset(self, direction_x: int | None = None):
        self.x = self.screen_width / 2 - self.rect.width / 2
        self.y = self.screen_height / 2 - self.rect.height / 2

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        # При новом розыгрыше старый след очищается.
        self.trail_points.clear()

        if direction_x is None:
            direction_x = random.choice([-1, 1])

        direction_y = random.choice([-1, 1])

        self.vx = self.base_speed_x * direction_x
        self.vy = self.base_speed_y * direction_y

    def update(self):
        # Перед перемещением сохраняем старую позицию для анимации следа.
        self.trail_points.append(self.rect.center)
        if len(self.trail_points) > self.max_trail_length:
            self.trail_points.pop(0)

        self.x += self.vx
        self.y += self.vy

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def bounce_vertical(self):
        self.vy *= -1

    def draw_trail(self, screen: pygame.Surface):
        # Чем старее позиция, тем меньше прямоугольник следа.
        for index, point in enumerate(self.trail_points):
            ratio = (index + 1) / max(1, len(self.trail_points))
            size = max(3, int(self.rect.width * ratio * 0.8))
            trail_rect = pygame.Rect(0, 0, size, size)
            trail_rect.center = point
            pygame.draw.rect(screen, TRAIL_COLOR, trail_rect, border_radius=3)

    def draw(
        self,
        screen: pygame.Surface,
        color: tuple[int, int, int] = DEFAULT_BALL_COLOR,
    ):
        pygame.draw.rect(screen, color, self.rect, border_radius=4)
