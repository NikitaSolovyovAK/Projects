import pygame


DEFAULT_PADDLE_COLOR = (255, 255, 255)


class Paddle:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        speed: float,
        screen_height: int,
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.y = float(y)
        self.speed = speed
        self.screen_height = screen_height

    def move_up(self):
        self.y -= self.speed
        self._clamp()

    def move_down(self):
        self.y += self.speed
        self._clamp()

    def _clamp(self):#ограничение движения ракетки границами экрана
        if self.y < 0:
            self.y = 0

        max_y = self.screen_height - self.rect.height
        if self.y > max_y:
            self.y = float(max_y)

        self.rect.y = int(self.y)

    def reset_to_center(self):
        self.y = (self.screen_height - self.rect.height) / 2
        self.rect.y = int(self.y)

    def draw(
        self,
        screen: pygame.Surface,
        color: tuple[int, int, int] = DEFAULT_PADDLE_COLOR,
    ):
        pygame.draw.rect(screen, color, self.rect, border_radius=6)