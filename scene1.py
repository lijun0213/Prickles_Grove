import pygame
from settings import *
from player import Player, Quill
from enemies import Raccoon, EscapeEnemy
from obstacles import Platform
from dialogue import Dialogue
import effects

class Scene1:
    def __init__(self):
        # Background handling & scaling
        self.bg = pygame.image.load(r"scene1_assets/scene1_background.png").convert_alpha()
        bgWidth, bgHeight = self.bg.get_size()
        scale = SCREEN_HEIGHT / bgHeight
        self.bg = pygame.transform.scale(self.bg, (int(bgWidth * scale), SCREEN_HEIGHT))
        self.bgWidth = self.bg.get_width()

        # Camera restrictions
        self.cameraX = 0
        self.maxCameraX = self.bgWidth - SCREEN_WIDTH

        # Sprite Groups
        self.enemies = pygame.sprite.Group()
        self.quillGroup = pygame.sprite.Group()
        self.escapeEnemies = pygame.sprite.Group()

        # Instantiate Player
        self.player = Player(self.quillGroup, self.bgWidth)
        self.player.bgWidth = self.bgWidth

        # Ground setting
        self.groundY = 490
        self.player.rect.x = 100
        self.player.rect.bottom = self.groundY
        self.player.groundY = self.groundY

        # Platforms map structure
        self.platforms = [
            Platform(r"scene1_assets/chair.png", x=380, y=380, scale=1.2),
            Platform(r"scene1_assets/chair.png", x=780, y=375, scale=1.2),
            Platform(r"scene1_assets/chair.png", x=975, y=375, scale=1.1),
            Platform(r"scene1_assets/table.png", x=492, y=355, scale=1.1),
            Platform(r"scene1_assets/bed.png", x=1090, y=320, scale=1.1)
        ]

        self.raccoon = Raccoon(500, 0)
        table = self.platforms[3]
        self.raccoon.rect.midbottom = (table.rect.centerx, table.rect.top)
        self.raccoon.platforms = self.platforms
        self.raccoon.bgWidth = self.bgWidth
        self.enemies.add(self.raccoon)

        self.portraits = {
            "prickle": pygame.transform.scale_by(self.player.idleFrames[0], 1.3),
            "raccoon": pygame.transform.scale_by(self.raccoon.idleRFrames[0], 1.0),
        }
        self.speakerNames = {
            "prickle": "Prickle",
            "raccoon": "Nugget",
        }

        windowX, windowY = 900, 200
        self.escapeEnemies.add(
            EscapeEnemy("scene4_assets/wasp_idle.png", 700, 200, windowX, windowY, startDelay=0)
        )

        # State Machine Initialization
        self.state = "INTRO"

        self.escapeStarted = False
        self.escapeFinished = False

        self.raccoonActive = False
        self.raccoonDefeated = False
        self.raccoonDeathDelay = 30

        self.showAmmoTutorial = False
        self.showHP = False

        # Dialogue Initialization
        self.dialogue = Dialogue()
        self.ammoInfoShown = False
        self._showDialogue(
            ["OMG... What happened?", "My treasures!"],
            speaker="prickle",
        )

        # Broken Window
        winX, winY, winScale = 865, 150, 0.42
        self.windowBrokenImage = pygame.image.load(r"scene1_assets/window_broken.png").convert_alpha()
        if winScale != 1.0:
            self.windowBrokenImage = pygame.transform.scale_by(self.windowBrokenImage, winScale)
        self.windowBrokenPos = (winX, winY)
        self.windowBroken = False
        self.windowEffectTimer = 0
        self.windowEffectDuration = 20

        # Collectible: Map item dropped
        mapScale = 0.2
        self.mapImage = pygame.image.load(r"scene1_assets/map.png").convert_alpha()
        if mapScale != 1.0:
            self.mapImage = pygame.transform.scale_by(self.mapImage, mapScale)
        self.mapRect = None
        self.mapCollected = False
        self.nearMap = False

        # Level progression door
        self.doorRect = pygame.Rect(0, self.groundY - 140, 60, 140)
        self.doorGlowTimer = 0
        self.levelComplete = False

        # background music
        pygame.mixer.music.load(r"scene1_assets/scene1_bgmusic.mp3")
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(loops=-1)

        # sound effects
        self.window_broken = pygame.mixer.Sound(r"scene1_assets/window_broken.mp3")
        self.window_broken.set_volume(0.4)
        self.level_complete = pygame.mixer.Sound(r"scene1_assets/scene1_complete.mp3")
        self.level_complete.set_volume(0.4)

    def _showDialogue(self, lines, speaker="prickle", style="center", next=None):
        """Open the shared dialogue box, resolving a speaker key into this
        scene's portrait/name, and wiring `next` up to Dialogue's onDismiss callback."""
        def onDismiss():
            self.player.controllable = True
            if next is not None:
                self.state = next
                if next == "MAP" and self.mapRect is None:
                    self.mapRect = self.mapImage.get_rect(center=self.raccoon.rect.center)

        self.player.controllable = False
        self.dialogue.show(
            lines,
            portrait=self.portraits.get(speaker),
            name=self.speakerNames.get(speaker, speaker),
            style=style,
            onDismiss=onDismiss,
        )

    def update(self):
        keys = pygame.key.get_pressed()

        # If the dialogue box is open, intercept updates to freeze everything else.
        if self.dialogue.active:
            self.dialogue.update(keys)
            self.updateCamera()
            return

        self.player.update(keys, self.platforms)
        self.quillGroup.update()
        self.enemies.update(self.player)
        self.escapeEnemies.update()

        # Game state dispatcher
        if self.state == "INTRO":
            self.updateIntro()
        elif self.state == "ESCAPE":
            self.updateEscape()
        elif self.state == "CHASE":
            self.updateChase(keys)
        elif self.state == "SHOOT":
            self.updateShoot()
        elif self.state == "MAP":
            self.updateMap(keys)
        elif self.state == "EXIT":
            self.updateExit()

        self.updateCamera()

    def updateIntro(self):
        triggerRange = 300
        nearEnemy = any(
            abs(self.player.rect.centerx - enemy.rect.centerx) <= triggerRange
            for enemy in self.escapeEnemies
        )
        if nearEnemy:
            self._showDialogue(["Wait... something's there!"], speaker="prickle", next="ESCAPE")

    def updateEscape(self):
        if not self.escapeStarted:
            self.escapeStarted = True
            for enemy in self.escapeEnemies:
                enemy.startEscape()

        for enemy in self.escapeEnemies:
            if enemy.nearWindow and not self.windowBroken:
                self.windowBroken = True
                self.windowEffectTimer = self.windowEffectDuration
                self.window_broken.play()

        if len(self.escapeEnemies) == 0:
            self._showDialogue(
                ["They escaped!", "But someone left behind..."],
                speaker="prickle", next="CHASE",
            )

    def updateChase(self, keys):
        if self.player.rect.colliderect(self.raccoon.rect.inflate(80, 50)):
            self.raccoon.activate()
            self._showDialogue(
                ["Try shooting your quills!", "Press LEFT CLICK to shoot!"],
                speaker="prickle", next="SHOOT",
            )

    def updateShoot(self):
        for quill in self.quillGroup:
            hits = pygame.sprite.spritecollide(quill, self.enemies, False)
            for enemy in hits:
                enemy.takeDamage(1)
                effects.create_impact_burst(quill.rect.center)
                quill.kill()

        if self.player.hasShot and not self.ammoInfoShown:
            self.ammoInfoShown = True
            self._showDialogue(
                ["Only 3 quills at a time!", "Cool down 2s to reload."],
                speaker="prickle", style="callout",
            )

        if self.raccoon.isDead and not self.raccoonDefeated:
            if self.raccoonDeathDelay > 0:
                self.raccoonDeathDelay -= 1
            else:
                self.raccoonDefeated = True
                effects.create_surrender_sparkle(self.raccoon.rect.midtop)
                self._showDialogue(
                    ["W-wait! I surrender!", "This is the map!"],
                    speaker="raccoon", next="MAP",
                )

    def updateMap(self, keys):
        self.nearMap = False

        if self.mapRect and self.player.rect.colliderect(self.mapRect):
            distance = abs(self.player.rect.centerx - self.mapRect.centerx)
            if distance < 60:
                self.nearMap = True

                if keys[pygame.K_r]:
                    self.mapCollected = True
                    self.player.pickupItem_sound.play()
                    self._showDialogue(
                        ["You found the map!", "Go to Mushroom Meadow!"],
                        speaker="prickle", next="EXIT",
                    )

    def updateExit(self):
        self.doorGlowTimer += 1

        if self.player.rect.colliderect(self.doorRect):
            self.level_complete.play()
            self.levelComplete = True
        if self.player.rect.x <= 10:
            pygame.mixer.music.fadeout(1000)
            self.levelComplete = True

    def updateCamera(self):
        self.cameraX = self.player.rect.centerx - SCREEN_WIDTH // 2
        self.cameraX = max(0, min(self.cameraX, self.bgWidth - SCREEN_WIDTH))
        self.player.cameraX = self.cameraX

    def draw(self, screen):
        screen.blit(self.bg, (-self.cameraX, 0))

        for platform in self.platforms:
            screen.blit(platform.image, (platform.rect.x - self.cameraX, platform.rect.y))

        if self.windowBroken:
            screen.blit(self.windowBrokenImage, (self.windowBrokenPos[0] - self.cameraX, self.windowBrokenPos[1]))
            if self.windowEffectTimer > 0:
                self.drawWindowEffect(screen)
                self.windowEffectTimer -= 1

        if self.state == "EXIT":
            rect = self.doorRect.move(-self.cameraX, 0)
            effects.drawDoorGlow(screen, rect, self.doorGlowTimer)

        for enemy in self.enemies:
            is_dead = getattr(enemy, 'isDead', False) or getattr(enemy, 'raccoonConfessed', False)
            if getattr(enemy, 'flash_timer', 0) > 0 and not is_dead:
                flash_surf = enemy.image.copy()
                flash_surf.fill((255, 50, 50, 255), special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(flash_surf, (enemy.rect.x - self.cameraX, enemy.rect.y))
            else:
                screen.blit(enemy.image, (enemy.rect.x - self.cameraX, enemy.rect.y))
                
        for enemy in self.escapeEnemies:
            screen.blit(enemy.image, (enemy.rect.x - self.cameraX, enemy.rect.y))

        if self.mapRect and not self.mapCollected:
            self.drawMap(screen)
            if self.nearMap:
                font = pygame.font.SysFont("Arial", 18)
                text = font.render("Press R to pick up", True, YELLOW)
                screen.blit(text, (self.mapRect.x - self.cameraX - 20, self.mapRect.y - 30))

        screen.blit(self.player.image, (self.player.rect.x - self.cameraX, self.player.rect.y))

        for quill in self.quillGroup:
            screen.blit(quill.image, (quill.rect.x - self.cameraX, quill.rect.y))

        self.player.drawAmmo(screen)
        self.player.drawHP(screen)
        for enemy in self.enemies:
            enemy.drawHP(screen)

        effects.update_and_draw_particles(screen, self.cameraX)
        effects.update_and_draw_surrender(screen, self.cameraX)

        # Renders the Dialogue overlay box
        self.dialogue.draw(screen)

    def drawMap(self, screen):
        cx = self.mapRect.centerx - self.cameraX
        cy = self.mapRect.centery
        effects.drawPulseGlow(screen, (cx, cy))
        screen.blit(self.mapImage, (self.mapRect.x - self.cameraX, self.mapRect.y))

    def drawWindowEffect(self, screen):
        cx = self.windowBrokenPos[0] + self.windowBrokenImage.get_width() // 2 - self.cameraX
        cy = self.windowBrokenPos[1] + self.windowBrokenImage.get_height() // 2
        effects.drawShatterBurst(screen, (cx, cy), self.windowEffectTimer, self.windowEffectDuration)