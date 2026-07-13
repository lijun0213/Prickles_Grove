import pygame
from settings import *
from player import Player, Bullet

class Scene1:
    def __init__(self):

        self.bg = pygame.image.load(r"scene1_assets/scene1_background.png").convert_alpha()
        self.bg = pygame.transform.scale(self.bg,(SCREEN_WIDTH, SCREEN_HEIGHT * 3 // 4))
        
        self.bullets = pygame.sprite.Group()

        self.player = Player(self.bullets)

        self.groundY = 500
        self.player.rect.x = 100

    def update(self):
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        self.bullets.update()

    def draw(self, screen):
        screen.blit(self.bg, (0, 0))
        screen.blit(self.player.image, self.player.rect)
        self.bullets.draw(screen)
        self.drawAmmo(screen)

