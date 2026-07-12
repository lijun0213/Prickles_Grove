import pygame
from settings import *
from player import Player

class Scene1:
    def __init__(self):

        self.bg = pygame.image.load(r"C:\Users\Asus\OneDrive - Asia Pacific University of Technology And Innovation (APU)\Documents\APU Y2S2\scene1bg.png").convert_alpha()
        self.bg = pygame.transform.scale(self.bg,(SCREEN_WIDTH, SCREEN_HEIGHT * 3 // 4))
        
        self.player = Player()

        self.groundY = 500
        self.player.rect.x = 100
        self.player.rect.bottom = self.groundY
        self.player.groundY = self.groundY

    def update(self):
        keys = pygame.key.get_pressed()
        self.player.update(keys)

    def draw(self, screen):
        screen.blit(self.bg, (0, 0))
        screen.blit(self.player.image, self.player.rect)
