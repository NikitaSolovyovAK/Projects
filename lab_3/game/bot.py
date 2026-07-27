from game.ball import Ball
from game.paddle import Paddle


class BotController:
    def __init__(
        self,
        paddle: Paddle,
        ball: Ball,
        tolerance: int,
    ):
        self.paddle = paddle
        self.ball = ball
        self.tolerance = tolerance

    def update(self):
        if self.ball.vx <= 0:
            return

        if self.paddle.rect.centery < self.ball.rect.centery - self.tolerance:
            self.paddle.move_down()
        elif self.paddle.rect.centery > self.ball.rect.centery + self.tolerance:
            self.paddle.move_up()