import pygame


class GameUI:
    def __init__(
        self,
        screen: pygame.Surface,
        width: int,
        height: int,
        bg_color: tuple[int, int, int],
        line_color: tuple[int, int, int],
        paddle_color: tuple[int, int, int],
        score_font: pygame.font.Font,
        info_font: pygame.font.Font,
    ):
        self.screen = screen
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.line_color = line_color
        self.paddle_color = paddle_color
        self.score_font = score_font
        self.info_font = info_font

    def draw_center_line(self):
        dash_height = 18
        gap = 14
        line_width = 4

        x = self.width // 2 - line_width // 2
        y = 0

        while y < self.height:
            pygame.draw.rect(
                self.screen,
                self.line_color,
                (x, y, line_width, dash_height),
            )
            y += dash_height + gap

    def draw_score(self, player_score: int, bot_score: int):
        player_surface = self.score_font.render(str(player_score), True, (255, 255, 255))
        bot_surface = self.score_font.render(str(bot_score), True, (255, 255, 255))

        self.screen.blit(player_surface, (self.width // 2 - 100, 30))
        self.screen.blit(bot_surface, (self.width // 2 + 70, 30))

    def draw_menu(self, options: list[str], selected_index: int):
        self.screen.fill(self.bg_color)

        title_surface = self.score_font.render("PONG", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.width // 2, 120))
        self.screen.blit(title_surface, title_rect)

        start_y = 240
        line_gap = 60

        for index, option in enumerate(options):
            color = (255, 255, 255)
            if index == selected_index:
                color = (240, 240, 120)

            option_surface = self.info_font.render(option, True, color)
            option_rect = option_surface.get_rect(
                center=(self.width // 2, start_y + index * line_gap)
            )
            self.screen.blit(option_surface, option_rect)

        hint_surface = self.info_font.render(
            "Стрелки - выбор, Enter - подтвердить",
            True,
            (180, 180, 180),
        )
        hint_rect = hint_surface.get_rect(center=(self.width // 2, 540))
        self.screen.blit(hint_surface, hint_rect)

    def draw_help(self):
        self.screen.fill(self.bg_color)

        title_surface = self.score_font.render("СПРАВКА", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title_surface, title_rect)

        lines = [
            "Pong - это аркадная игра с двумя ракетками и мячом.",
            "Вы управляете левой ракеткой.",
            "Правая ракетка управляется ботом.",
            "Если мяч вылетает за правую границу - очко игроку.",
            "Если мяч вылетает за левую границу - очко боту.",
            "Матч идет до заданного количества очков.",
            "",
            "Управление:",
            "W / Стрелка вверх - движение вверх",
            "S / Стрелка вниз  - движение вниз",
            "",
            "Esc или Enter - назад в меню",
        ]

        start_y = 180
        line_gap = 34

        for index, line in enumerate(lines):
            text_surface = self.info_font.render(line, True, (220, 220, 220))
            text_rect = text_surface.get_rect(
                center=(self.width // 2, start_y + index * line_gap)
            )
            self.screen.blit(text_surface, text_rect)

    def draw_leaderboard(self, records: list[dict]):
        self.screen.fill(self.bg_color)

        title_surface = self.score_font.render("РЕКОРДЫ", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title_surface, title_rect)

        if not records:
            empty_surface = self.info_font.render("Рекордов пока нет", True, (220, 220, 220))
            empty_rect = empty_surface.get_rect(center=(self.width // 2, 250))
            self.screen.blit(empty_surface, empty_rect)
        else:
            start_y = 180
            line_gap = 42

            for index, record in enumerate(records[:10], start=1):
                name = record.get("name", "Player")
                score = record.get("score", 0)
                text = f"{index}. {name} - {score}"

                text_surface = self.info_font.render(text, True, (220, 220, 220))
                text_rect = text_surface.get_rect(
                    center=(self.width // 2, start_y + (index - 1) * line_gap)
                )
                self.screen.blit(text_surface, text_rect)

        back_surface = self.info_font.render(
            "Esc или Enter - назад в меню",
            True,
            (180, 180, 180),
        )
        back_rect = back_surface.get_rect(center=(self.width // 2, 540))
        self.screen.blit(back_surface, back_rect)

    def draw_playing(
        self,
        player,
        bot,
        ball,
        player_score: int,
        bot_score: int,
        goal_text: str = "",
        goal_timer: int = 0,
        goal_duration: int = 1,
        hit_animation_timer: int = 0,
        hit_animation_duration: int = 1,
    ):
        self.screen.fill(self.bg_color)

        self.draw_center_line()
        self.draw_score(player_score, bot_score)

        # Анимация движения: за мячом остается короткий след.
        ball.draw_trail(self.screen)

        player.draw(self.screen, self.paddle_color)
        bot.draw(self.screen, self.paddle_color)
        ball.draw(self.screen)

        # Анимация удара: вокруг мяча появляется быстро исчезающий круг.
        if hit_animation_timer > 0:
            ratio = hit_animation_timer / hit_animation_duration
            radius = int(ball.rect.width + (1 - ratio) * 28)
            width = max(1, int(4 * ratio))
            pygame.draw.circle(
                self.screen,
                (240, 240, 120),
                ball.rect.center,
                radius,
                width,
            )

        if goal_timer > 0 and goal_text:
            alpha_ratio = goal_timer / goal_duration
            alpha = int(255 * alpha_ratio)

            text_surface = self.score_font.render(goal_text, True, (240, 240, 120))
            text_surface.set_alpha(alpha)

            text_rect = text_surface.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(text_surface, text_rect)

    def draw_game_over(self, winner_text: str, player_score: int, bot_score: int):
        self.screen.fill(self.bg_color)

        title_surface = self.score_font.render("GAME OVER", True, (255, 255, 255))
        winner_surface = self.info_font.render(winner_text, True, (255, 255, 255))

        score_text = f"Счет: {player_score} : {bot_score}"
        score_surface = self.info_font.render(score_text, True, (255, 255, 255))

        restart_surface = self.info_font.render("Enter - в меню", True, (200, 200, 200))
        exit_surface = self.info_font.render("Esc - выход", True, (200, 200, 200))

        title_rect = title_surface.get_rect(center=(self.width // 2, 180))
        winner_rect = winner_surface.get_rect(center=(self.width // 2, 260))
        score_rect = score_surface.get_rect(center=(self.width // 2, 320))
        restart_rect = restart_surface.get_rect(center=(self.width // 2, 420))
        exit_rect = exit_surface.get_rect(center=(self.width // 2, 470))

        self.screen.blit(title_surface, title_rect)
        self.screen.blit(winner_surface, winner_rect)
        self.screen.blit(score_surface, score_rect)
        self.screen.blit(restart_surface, restart_rect)
        self.screen.blit(exit_surface, exit_rect)

    def draw_name_input(self, name_input: str, result_score: int):
        self.screen.fill(self.bg_color)

        title_surface = self.score_font.render("НОВЫЙ РЕКОРД!", True, (240, 240, 120))
        title_rect = title_surface.get_rect(center=(self.width // 2, 140))
        self.screen.blit(title_surface, title_rect)

        result_text = f"Ваш результат: {result_score}"
        result_surface = self.info_font.render(result_text, True, (255, 255, 255))
        result_rect = result_surface.get_rect(center=(self.width // 2, 230))
        self.screen.blit(result_surface, result_rect)

        prompt_surface = self.info_font.render("Введите имя и нажмите Enter", True, (220, 220, 220))
        prompt_rect = prompt_surface.get_rect(center=(self.width // 2, 300))
        self.screen.blit(prompt_surface, prompt_rect)

        box_rect = pygame.Rect(0, 0, 380, 60)
        box_rect.center = (self.width // 2, 380)
        pygame.draw.rect(self.screen, (40, 40, 60), box_rect, border_radius=10)
        pygame.draw.rect(self.screen, (180, 180, 180), box_rect, width=2, border_radius=10)

        shown_name = name_input
        input_surface = self.info_font.render(shown_name, True, (255, 255, 255))
        input_rect = input_surface.get_rect(center=box_rect.center)
        self.screen.blit(input_surface, input_rect)

        hint_surface = self.info_font.render(
            "Backspace - удалить, Esc - отмена, Enter - сохранить",
            True,
            (180, 180, 180),
        )
        hint_rect = hint_surface.get_rect(center=(self.width // 2, 520))
        self.screen.blit(hint_surface, hint_rect)

    def draw_online_connect(self):
        self.screen.fill(self.bg_color)

        title_surface = self.score_font.render("ПОДКЛЮЧЕНИЕ...", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.width // 2, 220))
        self.screen.blit(title_surface, title_rect)

        hint_surface = self.info_font.render(
            "Ожидание состояния от сервера",
            True,
            (200, 200, 200),
        )
        hint_rect = hint_surface.get_rect(center=(self.width // 2, 300))
        self.screen.blit(hint_surface, hint_rect)

        esc_surface = self.info_font.render("Esc - отмена", True, (180, 180, 180))
        esc_rect = esc_surface.get_rect(center=(self.width // 2, 500))
        self.screen.blit(esc_surface, esc_rect)

    def draw_online_playing(self, online_state: dict, role):
        self.screen.fill(self.bg_color)

        field = online_state["field"]
        ball = online_state["ball"]
        left_paddle = online_state["left_paddle"]
        right_paddle = online_state["right_paddle"]
        score = online_state["score"]
        status = online_state["status"]

        self.draw_center_line()
        self.draw_score(score["left"], score["right"])

        left_rect = pygame.Rect(40, int(left_paddle["y"]), 20, left_paddle["height"])
        right_rect = pygame.Rect(
            field["width"] - 40 - 20,
            int(right_paddle["y"]),
            20,
            right_paddle["height"],
        )
        ball_rect = pygame.Rect(
            int(ball["x"]),
            int(ball["y"]),
            ball["size"],
            ball["size"],
        )

        pygame.draw.rect(self.screen, self.paddle_color, left_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.paddle_color, right_rect, border_radius=6)
        pygame.draw.rect(self.screen, (255, 255, 255), ball_rect, border_radius=4)

        role_text = f"Вы играете за: {role}" if role else "Роль ещё не назначена"
        role_surface = self.info_font.render(role_text, True, (200, 200, 200))
        role_rect = role_surface.get_rect(center=(self.width // 2, 560))
        self.screen.blit(role_surface, role_rect)

        if status == "waiting":
            wait_surface = self.info_font.render(
                "Ожидание второго игрока...",
                True,
                (240, 240, 120),
            )
            wait_rect = wait_surface.get_rect(center=(self.width // 2, 120))
            self.screen.blit(wait_surface, wait_rect)