import pygame
from settings import *
from player import Player
from obstacles import Platform, Wall

class Scene3:
    def __init__(self):

        # Background — the canopy image is taller than the screen on purpose,
        # since the fight climbs upward through the trees. We scale it to the
        # screen width and keep its full height so it can be scrolled later.
        self.bg = pygame.image.load(r"scene3_assets/scene 3 background.jpg").convert()
        bgWidth, bgHeight = self.bg.get_size()
        scale = SCREEN_WIDTH / bgWidth
        self.bg = pygame.transform.scale(self.bg, (SCREEN_WIDTH, int(bgHeight * scale)))
        self.bgHeight = self.bg.get_height()

        # scrollY = how far the camera has climbed up from the bottom of the canopy.
        # 0 = start of the climb (bottom of the image lines up with the bottom of
        # the screen). Increasing it reveals higher parts of the canopy.
        self.scrollY = 0
        self.maxScrollY = max(0, self.bgHeight - SCREEN_HEIGHT)
        
        self.bullets = pygame.sprite.Group()
        self.player = Player(self.bullets)

        self.groundY = SCREEN_HEIGHT
        self.player.rect.x = 100
        self.player.rect.bottom = self.groundY
        self.player.groundY = self.groundY

        # Obstacles — climbing platforms. Starting with one branch jutting out
        # from the tree on the right; Prickle jumps onto it to start climbing.
        self.platforms = [
            Platform(r"scene3_assets/branch_right.png", x=240, y=300, angle=22, scale = (2.2, 1.3)),
            Platform(r"scene3_assets/bridge.png", x=92, y=190, scale = (1.23, 1.1)),
        ]

        # Invisible vertical barrier — blocks Prickle from walking past x=615
        # in either direction. Spans the full screen height by default.
        self.walls = [
            Wall(x=635, top=0, bottom=SCREEN_HEIGHT),
            Wall(x=99, top=0, bottom=290),
        ]
        

    def update(self):
        keys = pygame.key.get_pressed()
        prevRect = self.player.rect.copy()

        # Platform sticking, walking-along-surface, and "S" drop-through are
        # now handled generically inside Player — just hand it this scene's
        # platforms each frame.
        self.player.update(keys, platforms=self.platforms)

        self.handleWallCollisions(prevRect)
        self.bullets.update()

        # TODO: once more climbing obstacles (vines/thorned branches) are in, drive
        # self.scrollY off the player's vertical progress instead of leaving it
        # at 0, and clamp with self.maxScrollY.

    def handleWallCollisions(self, prevRect):
        for wall in self.walls:
            if not self.player.rect.colliderect(wall.rect):
                continue

            # Use last frame's position to tell which side Prickle approached
            # from, then clamp him back to that side of the wall.
            if prevRect.right <= wall.x:
                self.player.rect.right = wall.x
            elif prevRect.left >= wall.x:
                self.player.rect.left = wall.x

    def draw(self, screen):
        # Anchor the bottom of the background to the bottom of the screen,
        # then shift up by scrollY as Prickle climbs.
        bgY = SCREEN_HEIGHT - self.bgHeight + self.scrollY
        screen.blit(self.bg, (0, bgY))

        for platform in self.platforms:
            platform.draw(screen)

        screen.blit(self.player.image, self.player.rect)
        self.bullets.draw(screen)
        self.player.drawAmmo(screen)