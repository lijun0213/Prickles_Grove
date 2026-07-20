import pygame
from settings import *
from player import Player
from dialogue import Dialogue

class Scene0:
    def __init__(self):
        # Background 
        self.bg = pygame.image.load(r"scene0_assets/scene 0 & 1.png").convert_alpha()
        bgWidth, bgHeight = self.bg.get_size()
        scale = SCREEN_HEIGHT / bgHeight
        self.bg = pygame.transform.scale(self.bg, (int(bgWidth * scale), SCREEN_HEIGHT))
        self.bgWidth = self.bg.get_width()

        # Camera restrictions
        self.cameraX = 0
        self.maxCameraX = max(0, self.bgWidth - SCREEN_WIDTH)
 
        self.quillGroup = pygame.sprite.Group()

        # Instantiate Player, spawned on the left side of the screen.
        self.player = Player(self.quillGroup, self.bgWidth)
        self.player.bgWidth = self.bgWidth

        self.groundY = SCREEN_HEIGHT - 95
        self.player.rect.x = 60
        self.player.rect.bottom = self.groundY
        self.player.groundY = self.groundY

        # Where Prickle respawns if he falls in the pond below.
        self.spawnPos = self.player.rect.bottomleft

        # Pond location and sound effect 
        self.pondLeft = 625
        self.pondRight = 850
        self.splash_sound = pygame.mixer.Sound(r"scene0_assets/Splash sound.mp3")

        # Tutorial callouts 
        self.dialogue = Dialogue()
        self.moveTipShown = False
        self.sprintTipShown = False
        self.jumpTipShown = False
        self.pondTipShown = False

        # Prickle house door or Exit
        self.exitX = 1200
        self.nearExit = False
        self.levelComplete = False

        # Background music 
        pygame.mixer.music.load(r"scene0_assets/Inorimichite, Chika V2.mp3")
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(loops=-1)

    def update(self):
        keys = pygame.key.get_pressed()

        if self.dialogue.active:
            self.dialogue.update(keys)
            return

        self.player.update(keys)
        self.quillGroup.update()
        self.handlePond()
        self.checkTutorialCallouts()
        self.checkExit(keys)
        self.updateCamera()

    def checkExit(self, keys):
        if self.levelComplete:
            return

        self.nearExit = abs(self.player.rect.centerx - self.exitX) < 60

        if self.nearExit and keys[pygame.K_r]:
            self.levelComplete = True

    def checkTutorialCallouts(self):
        x = self.player.rect.centerx
        if not self.moveTipShown:
            self.moveTipShown = True
            self.dialogue.show(["Press A/D to move!"], style="callout")
            return
        if not self.sprintTipShown and x >= 275:
            self.sprintTipShown = True
            self.dialogue.show(["Hold LSHIFT to sprint!"], style="callout")
            return
        if not self.jumpTipShown and x >= 475:
            self.jumpTipShown = True
            self.dialogue.show(["Hold SPACE to jump!"], style="callout")
            return
        if not self.pondTipShown and x >= 500:
            self.pondTipShown = True
            self.dialogue.show(["Sprint and Jump past this pond!"], style="callout")
            return

    def handlePond(self):
        if not self.player.onGround:
            return
        if self.pondLeft < self.player.rect.centerx < self.pondRight:
            self.splash_sound.play()
            self.player.rect.bottomleft = self.spawnPos
            self.player.velocityX = 0
            self.player.velocityY = 0

    def updateCamera(self):
        self.cameraX = self.player.rect.centerx - SCREEN_WIDTH // 2
        self.cameraX = max(0, min(self.cameraX, self.maxCameraX))
        self.player.cameraX = self.cameraX

    def draw(self, screen):
        screen.blit(self.bg, (-self.cameraX, 0))

        screen.blit(self.player.image, (self.player.rect.x - self.cameraX, self.player.rect.y))
        for quill in self.quillGroup:
            screen.blit(quill.image, (quill.rect.x - self.cameraX, quill.rect.y))

        self.player.drawAmmo(screen)
        self.player.drawHP(screen)

        if self.nearExit and not self.levelComplete:
            font = pygame.font.SysFont("Arial", 18)
            text = font.render("Press R to Enter", True, YELLOW)
            textX = self.player.rect.centerx - self.cameraX - text.get_width() // 2
            textY = self.player.rect.top - 30
            screen.blit(text, (textX, textY))

        self.dialogue.draw(screen)
