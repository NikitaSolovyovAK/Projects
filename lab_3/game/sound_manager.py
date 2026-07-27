import os
import pygame


class SoundManager:
    def __init__(self, config: dict):
        self.enabled = False
        self.sounds = {}

        try:
            pygame.mixer.init()#модуль работающий со звуком, если звука нет то программа не падает а работает без звука
            self.enabled = True
        except pygame.error:
            return

        sounds_config = config.get("sounds", {})
        for sound_name, sound_path in sounds_config.items():
            if os.path.exists(sound_path):
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(sound_path)
                except pygame.error:
                    pass

        music_config = config.get("music", {})
        music_path = music_config.get("background")

        if music_path and os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(music_config.get("volume", 0.4))
                pygame.mixer.music.play(-1)
            except pygame.error:
                pass

    def play(self, sound_name: str):
        if not self.enabled:
            return

        sound = self.sounds.get(sound_name)
        if sound is not None:
            sound.play()