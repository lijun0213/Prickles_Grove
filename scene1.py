import pygame
from settings import *
from player import Player

class Scene1:
    def __init__(self):

        self.bg_colour = (WHITE)

        self.player = Player()
        self.player.rect.x = 100
        self.player.rect.y = 300

    def update(self):
        keys = pygame.key.get_pressed()
        self.player.update(keys)

    def draw(self, screen):
        screen.fill(self.bg_colour)
        screen.blit(self.player.image, self.player.rect)
