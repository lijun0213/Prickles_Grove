import pygame
from settings import *
from player import Player, Quill
from enemies import Raccoon, EscapeEnemy
from obstacles import Platform
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

        self.showAmmoTutorial = False
        self.showHP = False

        # Popup display setup — shown immediately on entering the scene.
        self.showPopup = True
        self.popupLines = [
            "OMG... What happened?",
            "My treasures are gone!"
        ]
        self.popupNext = None
        self.popupStyle = "center"
        self.ammoInfoShown = False
        self.popupDismissKeys = (pygame.K_SPACE, pygame.K_RETURN)

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
        pygame.mixer.music.set_volume(0.3) 
        pygame.mixer.music.play(loops=-1)

    def update(self):
        keys = pygame.key.get_pressed()

        # If dialogue popup is open, intercept updates to freeze elements
        if self.showPopup:
            self.updatePopup(keys)
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
        # Trigger once the player walks close
        triggerRange = 300
        nearEnemy = any(
            abs(self.player.rect.centerx - enemy.rect.centerx) <= triggerRange
            for enemy in self.escapeEnemies
        )
        if nearEnemy:
            self.popupLines = [
                "Wait... something's there!"
            ]
            self.showPopup = True
            self.popupNext = "ESCAPE"
 
    def updateEscape(self):
        keys = pygame.key.get_pressed()

        if not self.escapeStarted:
            self.escapeStarted = True
            for enemy in self.escapeEnemies:
                enemy.startEscape()

        for enemy in self.escapeEnemies:
            if enemy.nearWindow and not self.windowBroken:
                self.windowBroken = True
                self.windowEffectTimer = self.windowEffectDuration

        # Transition once the wasps clear the room
        if len(self.escapeEnemies) == 0:
            self.popupLines = [
                "They escaped!",
                "But someone left behind..."
            ]
            self.popupNext = "CHASE"
            self.showPopup = True
 
    def updateChase(self, keys):
        # Raccoon intercepts the player
        if self.player.rect.colliderect(self.raccoon.rect.inflate(80, 50)):
            self.raccoon.activate()
            self.popupLines = [
                "Try shooting your quills!",
                "Press LEFT CLICK to shoot!"
            ]
            self.popupNext = "SHOOT"
            self.showPopup = True

    def updateShoot(self):
        # Quills and enemy collision processing
        for quill in self.quillGroup:
            hits = pygame.sprite.spritecollide(quill, self.enemies, False)
            for enemy in hits:
                enemy.takeDamage(1)
                quill.kill()

        # First shot fired — pop a small callout next to the ammo HUD
        # explaining the 3-shot limit and cooldown. Doesn't change state,
        # just pauses briefly and resumes SHOOT once dismissed.
        if self.player.hasShot and not self.ammoInfoShown:
            self.ammoInfoShown = True
            self.popupLines = [
                "Only 3 quills at a time!",
                "Cool down 2s to reload."
            ]
            self.popupStyle = "ammo"
            self.popupNext = None
            self.showPopup = True

        # If raccoon is dead, drop the map reward
        if self.raccoon.isDead and self.mapRect is None:
            self.state = "MAP"
            self.mapRect = self.mapImage.get_rect(center=self.raccoon.rect.center)

    def updateMap(self, keys):
        self.nearMap = False

        if self.mapRect and self.player.rect.colliderect(self.mapRect):
            distance = abs(self.player.rect.centerx - self.mapRect.centerx)
            if distance < 60:
                self.nearMap = True

                if keys[pygame.K_r]:
                    self.mapCollected = True
                    self.player.pickupItem_sound.play()
                    self.popupLines = [
                        "You found the map!",
                        "Go to Mushroom Meadow!"
                    ]
                    self.showPopup = True
                    self.state = "EXIT"

    def updateExit(self):
        self.doorGlowTimer += 1

        if self.player.rect.colliderect(self.doorRect):
            self.levelComplete = True
        if self.player.rect.x <= 10:
            pygame.mixer.music.fadeout(1000) 
            self.levelComplete = True

    def updatePopup(self, keys):
        # Dismiss text popup window safely across states
        if keys[pygame.K_SPACE]:
            self.showPopup = False
            self.player.controllable = True
            if self.popupNext in ["ESCAPE", "CHASE", "SHOOT"]:
                self.state = self.popupNext
                self.popupNext = None
            self.popupStyle = "center"
    
    def updateCamera(self):
        self.cameraX = self.player.rect.centerx - SCREEN_WIDTH // 2
        self.cameraX = max(0, min(self.cameraX, self.bgWidth - SCREEN_WIDTH))
 
        self.player.cameraX = self.cameraX

    def draw(self, screen):
        # Draw parallax background
        screen.blit(self.bg, (-self.cameraX, 0))  

        # Draw platforms relative to camera screen position
        for platform in self.platforms:
            screen.blit(platform.image, (platform.rect.x - self.cameraX, platform.rect.y))
        
        # Environmental assets mapping
        if self.windowBroken:
            screen.blit(self.windowBrokenImage, (self.windowBrokenPos[0] - self.cameraX, self.windowBrokenPos[1]))
            if self.windowEffectTimer > 0:
                self.drawWindowEffect(screen)
                self.windowEffectTimer -= 1

        if self.state == "EXIT":
            rect = self.doorRect.move(-self.cameraX,0)

            effects.drawDoorGlow(screen,rect,self.doorGlowTimer)

        # Draw characters & group assets
        for enemy in self.enemies:
            screen.blit(enemy.image, (enemy.rect.x - self.cameraX, enemy.rect.y))
        
        for enemy in self.escapeEnemies:
            screen.blit(enemy.image, (enemy.rect.x - self.cameraX, enemy.rect.y))

        if self.mapRect and not self.mapCollected:
            self.drawMap(screen)
            if self.nearMap:
                font = pygame.font.SysFont("Arial",18)
                text = font.render("Press R to pick up",True,YELLOW)
                screen.blit(text,(self.mapRect.x - self.cameraX - 20,self.mapRect.y - 30))
        
        screen.blit(self.player.image, (self.player.rect.x - self.cameraX, self.player.rect.y))
 
        for quill in self.quillGroup:
            screen.blit(quill.image, (quill.rect.x - self.cameraX, quill.rect.y))
 
        self.quillGroup.draw(screen)

        # Draw standard user interface over context surfaces
        self.player.drawAmmo(screen)
        self.player.drawHP(screen)
        for enemy in self.enemies:
            enemy.drawHP(screen)
 
        if self.showPopup:
            self.drawPopup(screen)

    def drawMap(self, screen):
        cx = self.mapRect.centerx - self.cameraX
        cy = self.mapRect.centery

        effects.drawPulseGlow(screen, (cx, cy))

        screen.blit(self.mapImage, (self.mapRect.x - self.cameraX, self.mapRect.y))
 
    def drawWindowEffect(self, screen):
        cx = self.windowBrokenPos[0] + self.windowBrokenImage.get_width() // 2 - self.cameraX
        cy = self.windowBrokenPos[1] + self.windowBrokenImage.get_height() // 2

        effects.drawShatterBurst(screen, (cx, cy), self.windowEffectTimer, self.windowEffectDuration)
 
    def drawPopup(self, screen):
        if self.popupStyle == "ammo":
            self.drawAmmoPopup(screen)
        else:
            self.drawCenterPopup(screen)

    def drawCenterPopup(self, screen):
        boxWidth, boxHeight = 520, 110
        boxX = SCREEN_WIDTH // 2 - boxWidth // 2
        boxY = SCREEN_HEIGHT - boxHeight - 30
 
        box = pygame.Surface((boxWidth, boxHeight), pygame.SRCALPHA)
        box.fill((20, 20, 20, 210))
        screen.blit(box, (boxX, boxY))
        pygame.draw.rect(screen, WHITE, (boxX, boxY, boxWidth, boxHeight), width=2, border_radius=8)
 
        font = pygame.font.SysFont("Arial", 18)
        smallFont = pygame.font.SysFont("Arial", 14)
 
        for i, line in enumerate(self.popupLines):
            label = font.render(line, True, WHITE)
            screen.blit(label, (boxX + 20, boxY + 16 + i * 26))
 
        hint = smallFont.render("Press SPACE to continue", True, YELLOW)
        screen.blit(hint, (boxX + 20, boxY + boxHeight - 26))

    def drawAmmoPopup(self, screen):
        boxWidth, boxHeight = 260, 80
        boxX = 250
        boxY = 60
 
        box = pygame.Surface((boxWidth, boxHeight), pygame.SRCALPHA)
        box.fill((20, 20, 20, 220))
        screen.blit(box, (boxX, boxY))
        pygame.draw.rect(screen, WHITE, (boxX, boxY, boxWidth, boxHeight), width=2, border_radius=8)
 
        font = pygame.font.SysFont("Arial", 15)
        smallFont = pygame.font.SysFont("Arial", 12)
 
        for i, line in enumerate(self.popupLines):
            label = font.render(line, True, WHITE)
            screen.blit(label, (boxX + 12, boxY + 10 + i * 20))
 
        hint = smallFont.render("SPACE to continue", True, YELLOW)
        screen.blit(hint, (boxX + 12, boxY + boxHeight - 18))