import pygame
from settings import *
from player import Player, Bullet
from enemies import Enemy

class Scene1:
    def __init__(self):

        self.bg = pygame.image.load(r"scene1_assets/scene1_background.png").convert_alpha()
        bgWidth, bgHeight = self.bg.get_size()
        scale = SCREEN_HEIGHT / bgHeight
        self.bg = pygame.transform.scale(self.bg,(int(bgWidth * scale),SCREEN_HEIGHT) )
        self.bgWidth = self.bg.get_width()

        self.cameraX = 0        
        self.maxCameraX = self.bgWidth - SCREEN_WIDTH

        self.enemies = pygame.sprite.Group()

        self.bullets = pygame.sprite.Group()

        self.player = Player(self.bullets, self.bgWidth)
        self.player.bgWidth = self.bgWidth

        self.groundY = 500
        self.player.rect.x = 100
        self.player.rect.bottom = self.groundY

        self.enemies.add(
            Enemy(500, self.groundY),
            Enemy(800, self.groundY),
            Enemy(1200, self.groundY),
            # Enemy(1500, self.groundY)
        )

    def update(self):
        self.cameraX = self.player.rect.centerx - SCREEN_WIDTH // 2
        self.cameraX = max(0,min(self.cameraX, self.bgWidth - SCREEN_WIDTH))
       
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
        screen.blit(self.bg, (-self.cameraX, 0))        
        for enemy in self.enemies:
            screen.blit(enemy.image,(enemy.rect.x - self.cameraX, enemy.rect.y))
        screen.blit(self.player.image,(self.player.rect.x - self.cameraX,self.player.rect.y))
        for bullet in self.bullets:
            screen.blit(bullet.image,(bullet.rect.x - self.cameraX,bullet.rect.y))
        self.player.drawAmmo(screen)
        self.player.drawHP(screen)

        for enemy in self.enemies:
            enemy.drawHP(screen)