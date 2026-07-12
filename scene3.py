import pygame
from settings import *
from player import Player
from obstacles import Platform

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

        self.player = Player()

        self.groundY = SCREEN_HEIGHT
        self.player.rect.x = 100
        self.player.rect.bottom = self.groundY
        self.player.groundY = self.groundY

        # Obstacles — climbing platforms. Starting with one branch jutting out
        # from the tree on the right; Prickle jumps onto it to start climbing.
        self.platforms = [
            Platform(r"scene3_assets/branch_right.png", x=580, y=400),
        ]

    def update(self):
        keys = pygame.key.get_pressed()
        prevBottom = self.player.rect.bottom
        self.player.update(keys)
        self.handlePlatformCollisions(prevBottom)

        # TODO: once more climbing obstacles (vines/thorned branches) are in, drive
        # self.scrollY off the player's vertical progress instead of leaving it
        # at 0, and clamp with self.maxScrollY.

    def handlePlatformCollisions(self, prevBottom):
        # Only land on a platform when falling onto it from above — ignores
        # jumping up into it from below or brushing it from the side.
        if self.player.velocityY < 0:
            return

        for platform in self.platforms:
            if not self.player.rect.colliderect(platform.rect):
                continue

            # Use the branch's actual pixel shape under Prickle's feet, not
            # its full rectangular image bounds.
            surfaceY = platform.topAt(self.player.rect.centerx)
            if surfaceY is None:
                continue

            if prevBottom <= surfaceY and self.player.rect.bottom >= surfaceY:
                self.player.rect.bottom = surfaceY
                self.player.velocityY = 0
                self.player.onGround = True

    def draw(self, screen):
        # Anchor the bottom of the background to the bottom of the screen,
        # then shift up by scrollY as Prickle climbs.
        bgY = SCREEN_HEIGHT - self.bgHeight + self.scrollY
        screen.blit(self.bg, (0, bgY))

        for platform in self.platforms:
            platform.draw(screen)

        screen.blit(self.player.image, self.player.rect)
