import pygame
from settings import *
from player import Player, Bullet
from enemies import Enemy

class Scene1:
    def __init__(self):

        self.bg = pygame.image.load(r"scene1_assets/scene1_background.png").convert_alpha()
        self.bg = pygame.transform.scale(self.bg,(SCREEN_WIDTH, SCREEN_HEIGHT))
        
        self.enemies = pygame.sprite.Group()

        self.bullets = pygame.sprite.Group()

        self.player = Player(self.bullets)

        self.groundY = 500
        self.player.rect.x = 100

        self.enemies.add(
            Enemy(500, self.groundY),
            # Enemy(800, self.groundY),
            # Enemy(1200, self.groundY),
            # Enemy(1500, self.groundY)
        )

    def update(self):
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        self.bullets.update()
        self.enemies.update(self.player)
        for bullet in self.bullets:
            hitEnemies = pygame.sprite.spritecollide(bullet,self.enemies,False)

            for enemy in hitEnemies:
                enemy.takeDamage(1)
                bullet.kill()

    def draw(self, screen):
        screen.blit(self.bg, (0, 0))
        self.enemies.draw(screen)    
        screen.blit(self.player.image, self.player.rect)
        self.bullets.draw(screen)
        self.player.drawAmmo(screen)
        self.player.drawHP(screen)

        for enemy in self.enemies:
            enemy.drawHP(screen)