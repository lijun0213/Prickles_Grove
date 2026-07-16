import pygame
import random
from settings import *
from player import Player
from enemies import Wasp, WaspQueen, Sting
from obstacles import Platform, MovingPlatform
import effects

class Scene4:
    def __init__(self):
        # 1. Background setup & expanding world limits for a long stage layout
        self.bg = pygame.image.load(r"scene4_assets/scene4_bg.png").convert_alpha()
        bgWidth, bgHeight = self.bg.get_size()
        scaleY = SCREEN_HEIGHT / bgHeight
        # Explicitly make the map much wider than a single standard window frame
        self.worldWidth = max(bgWidth * scaleY, SCREEN_WIDTH * 3) 
        self.bg = pygame.transform.scale(self.bg, (int(self.worldWidth), SCREEN_HEIGHT))

        # Camera restrictions matching the expanded landscape limits
        self.cameraX = 0        
        self.maxCameraX = max(0, self.worldWidth - SCREEN_WIDTH)

        self.quills = pygame.sprite.Group()
        self.player = Player(self.quills, self.worldWidth) # Dynamic boundaries bound to world layout

        # Drop ground away to handle platform pit hazards cleanly
        self.player.groundY = SCREEN_HEIGHT + 1000

        # 2. Distribute platforms across the long scrolling horizon sequence
        self.platforms = [
            Platform(r"scene4_assets/flower_platform1.png", x=80, y=380, scale=0.5),
            Platform(r"scene4_assets/flower_platform1.png", x=200, y=240, scale=0.5),
            Platform(r"scene4_assets/vine1.png", x=230, y=260, scale=0.7),
            MovingPlatform(r"scene4_assets/flower_platform2.png", x=400, y=380, scale=0.5, moveRange=100, speed=2, axis='X'),
            Platform(r"scene4_assets/flower_platform1.png", x=750, y=320, scale=0.5),
            MovingPlatform(r"scene4_assets/flower_platform2.png", x=1050, y=100, scale=0.5, moveRange=70, speed=1.5, axis='Y'),
            MovingPlatform(r"scene4_assets/flower_platform2.png", x=1050, y=380, scale=0.5, moveRange=100, speed=1.5, axis='Y'),
            Platform(r"scene4_assets/flower_platform1.png", x=1450, y=280, scale=0.5),
        ]

        startPlatform = self.platforms[0]
        self.player.rect.midbottom = (startPlatform.rect.centerx, startPlatform.rect.top)
        self.lastSafePos = self.player.rect.midbottom

        # 3. Position the Boss Arena further down the long world path
        self.bossTeleportSpots = [(1100, 200), (1350, 150), (1500, 250), (1250, 100)]
        self.boss = WaspQueen(self.bossTeleportSpots[1][0], self.bossTeleportSpots[1][1], 
                             teleportSpots=self.bossTeleportSpots, stingGroup=self.quills)
        
        self.bossGroup = pygame.sprite.Group()
        self.bossGroup.add(self.boss)
        self.stings = pygame.sprite.Group()
        self.boss.stingGroup = self.stings 
        self.bossEffects = pygame.sprite.Group()

        # Wave tracking
        self.wasps = pygame.sprite.Group()
        self.waveConfigurations = [3, 4, 5]
        self.currentWaveIndex = 0

        self.flowerImage = pygame.image.load(r"scene4_assets/eternal_flower.png").convert_alpha()
        self.flowerImage = pygame.transform.scale_by(self.flowerImage, 0.25)
        self.flowerRect = None
        self.flowerCollected = False
        self.nearFlower = False

        self.portraits = {
            "prickle": pygame.transform.scale_by(self.player.idleFrames[0], 1.3),
            "queen" : pygame.transform.scale_by(self.boss.attackRFrames[0], 0.7)
        }

        # Finite state engine handles death routing explicitly
        self.state = "INTRO"
        self.levelComplete = False

        self.popupLines = ["The flowers glow strangely here...", "Something's watching me."]
        self.popupSpeaker = "prickle"
        self.popupNext = "BOSS_COMMAND"  
        self.showPopup = True
        self.player.controllable = False
        self._popupKeyWasDown = False
        self.popupDismissKeys = (pygame.K_SPACE, pygame.K_RETURN)

        # Death handling variables
        self.deathTimer = 0
        self.deathDuration = 120 # ~2 seconds for animation sequence to unfold

        # background music
        pygame.mixer.music.load(r"scene4_assets/scene4_bgmusic.mp3")
        pygame.mixer.music.set_volume(0.2) 
        pygame.mixer.music.play(loops=-1)


    def spawnWaspWave(self):
        self.wasps.empty()
        numWasps = self.waveConfigurations[self.currentWaveIndex]
        
        for _ in range(numWasps):
            sx = random.randint(1100, 1500)
            sy = random.randint(100, 250)
            wasp = Wasp(sx, sy)
            if hasattr(wasp, 'speed'):
                wasp.speed = 1.5
            self.wasps.add(wasp)

    def update(self):
        keys = pygame.key.get_pressed()

        # Check death trigger immediately before processing state engine vectors
        if self.player.hp <= 0 and self.state != "DEATH":
            self.state = "DEATH"
            self.player.isDeath = True
            self.player.controllable = False
            self.deathTimer = 0
            # If your Player class has a death sound, trigger it here:
            # self.player.death_sound.play()

        if self.showPopup:
            self.updatePopup(keys)
            self.updateCamera()
            if self.boss:
                self.boss.update(self.player, active=False)
            return
        
        for platform in self.platforms:
            if hasattr(platform, 'update'):
                platform.update()

        # Core operational loops
        self.player.update(keys, platforms=self.platforms)
        self.quills.update()
        self.updateCamera() # Keep camera locked precisely to current position frame-by-frame

        self.bossEffects.update()

        if self.player.onGround:
            self.lastSafePos = self.player.rect.midbottom
        if self.player.rect.top > SCREEN_HEIGHT + 50:
            self.handleFall()

        if self.state == "SWARM":
            self.updateSwarm()
        elif self.state == "BOSS_FIGHT":
            self.updateBossFight()
        elif self.state == "VICTORY":
            self.updateVictory(keys)

    def updateCamera(self):
        """Updates internal center coordinates relative to modern long map styles."""
        self.cameraX = self.player.rect.centerx - SCREEN_WIDTH // 2
        self.cameraX = max(0, min(self.cameraX, self.maxCameraX))
        self.player.cameraX = self.cameraX

    def handleFall(self):
        self.player.takeDamage(1)
        self.player.rect.midbottom = self.lastSafePos
        self.player.velocityY = 0
        self.player.velocityX = 0

    def updateSwarm(self):
        self.boss.update(self.player, active=False)
        self.boss.updateBuzz(self.player)

        self.wasps.update(self.player)
        for wasp in self.wasps:
            wasp.updateBuzz(self.player)

        for quill in list(self.quills):
            if quill.rect.colliderect(self.boss.rect):
                quill.kill()
                continue

            hits = pygame.sprite.spritecollide(quill, self.wasps, False)
            for wasp in hits:
                wasp.takeDamage(1)
                effects.create_impact_burst(quill.rect.center)
                quill.kill()

        if len(self.wasps) == 0:
            self.currentWaveIndex += 1
            if self.currentWaveIndex < len(self.waveConfigurations):
                self.spawnWaspWave()
            else:
                self.popupLines = ["My swarm has fallen...", "Now you face me directly!"]
                self.popupSpeaker = "queen"
                self.popupNext = "BOSS_FIGHT"
                self.showPopup = True

    def updateBossFight(self):
        self.boss.update(self.player, active=True)
        self.boss.updateBuzz(self.player)

        self.stings.update()

        for sting in list(self.stings):
            if sting.rect.colliderect(self.player.rect):
                if hasattr(self.player, 'applyParalysis'):
                    self.player.applyParalysis(PARALYSIS_DURATION)
                else:
                    self.player.takeDamage(1)
                sting.kill()

        for quill in list(self.quills):
            if quill.rect.colliderect(self.boss.rect) and not self.boss.teleporting:
                self.boss.takeDamage(1)
                self.boss.shakeTimer = 15      
                self.boss.shakeMagnitude = 6                   
                wave = effects.HitShockwave(quill.rect.centerx, quill.rect.centery, max_radius=70)
                self.bossEffects.add(wave)
                self.boss.takeDamage(1)
                effects.create_impact_burst(quill.rect.center)
                quill.kill()

        if self.boss.hp <= 0 and self.flowerRect is None:
            self.flowerRect = self.flowerImage.get_rect(center=self.boss.rect.center)
            self.popupLines = ["The Eternal Flower...", "It's free."]
            self.popupSpeaker = "prickle"
            self.popupNext = "VICTORY"
            self.showPopup = True

    def updateVictory(self, keys):
        if self.flowerCollected:
            return

        if self.flowerRect and self.player.rect.colliderect(self.flowerRect):
            distance = abs(self.player.rect.centerx - self.flowerRect.centerx)
            self.nearFlower = distance < 60

            if self.nearFlower and keys[pygame.K_r]:
                self.flowerCollected = True
                if hasattr(self.player, 'pickupItem_sound'):
                    self.player.pickupItem_sound.play()
                self.popupLines = ["You recovered all the treasures!", "Prickle's Grove is safe again."]
                self.popupSpeaker = "prickle"
                self.popupNext = None
                self.showPopup = True
                self.levelComplete = True
        else:
            self.nearFlower = False

    def updatePopup(self, keys):
        if hasattr(self.player, 'applyParalysis'):
            self.player.applyParalysis(1) 
        
        keyDown = any(keys[k] for k in self.popupDismissKeys)
        justPressed = keyDown and not self._popupKeyWasDown
        self._popupKeyWasDown = keyDown

        if justPressed:
            # 1. Capture what the NEXT phase was going to be
            next_phase = self.popupNext 
            
            # 2. Clear out popup variables so it cannot loop back on itself
            self.showPopup = False
            self.player.controllable = True
            self.popupNext = None 

            # 3. Safely handle step-by-step dialogue chain events
            if next_phase == "BOSS_COMMAND":
                self.popupLines = ["Intruder! Wasps, tear this hedgehog apart!"]
                self.popupSpeaker = "queen"
                self.popupNext = "START_SWARM" # Set the final dialog link
                self.showPopup = True
                self.player.controllable = False
                return

            if next_phase == "START_SWARM":
                self.state = "SWARM"
                self.currentWaveIndex = 0
                self.spawnWaspWave()
                return

            if next_phase in ["BOSS_FIGHT", "VICTORY"]:
                self.state = next_phase

    def draw(self, screen):
        screen.blit(self.bg, (-self.cameraX, 0))  

        for platform in self.platforms:
            # Shift platforms back by camera coordinate space adjustments
            screen.blit(platform.image, (platform.rect.x - self.cameraX, platform.rect.y))

        for wasp in self.wasps:
            screen.blit(wasp.image, (wasp.rect.x - self.cameraX, wasp.rect.y))

        # Render boss with relative scaling vector translations applied safely
        if self.boss and self.boss.hp > 0:
            drawX = self.boss.rect.x - self.cameraX
            drawY = self.boss.rect.y
            if self.boss.shakeTimer > 0:
                drawX += random.randint(-self.boss.shakeMagnitude, self.boss.shakeMagnitude)
                drawY += random.randint(-self.boss.shakeMagnitude, self.boss.shakeMagnitude)

            if self.state == "BOSS_FIGHT" and self.boss.teleporting:
                effects.drawTeleportPuff(screen, (self.boss.rect.centerx - self.cameraX, self.boss.rect.centery))
            else:
                screen.blit(self.boss.image, (drawX, drawY))

            if self.state == "BOSS_FIGHT":
                # Ensure the health bar updates above the scrolled space coordinates
                oldRectX = self.boss.rect.x
                self.boss.rect.x -= self.cameraX
                self.boss.drawHP(screen)
                self.boss.rect.x = oldRectX

        for sting in self.stings:
            screen.blit(sting.image, (sting.rect.x - self.cameraX, sting.rect.y))

        if self.flowerRect and not self.flowerCollected:
            scrolledFlowerCenter = (self.flowerRect.centerx - self.cameraX, self.flowerRect.centery)
            effects.drawPulseGlow(screen, scrolledFlowerCenter)
            screen.blit(self.flowerImage, (self.flowerRect.x - self.cameraX, self.flowerRect.y))
            if self.nearFlower:
                font = pygame.font.SysFont("Arial", 18)
                text = font.render("Press R to pick up", True, YELLOW)
                screen.blit(text, (self.flowerRect.x - self.cameraX - 20, self.flowerRect.y - 30))

        # Player drawing vector calculation
        screen.blit(self.player.image, (self.player.rect.x - self.cameraX, self.player.rect.y))
        
        for quill in self.quills:
            screen.blit(quill.image, (quill.rect.x - self.cameraX, quill.rect.y))

        for effect in self.bossEffects:
            effect.draw(screen, self.cameraX)

        # Interface Overlays (Drawn natively directly on viewport base vectors)
        self.player.drawAmmo(screen)
        self.player.drawHP(screen)
        effects.update_and_draw_particles(screen, self.cameraX)

        if self.showPopup:
            self.drawPopup(screen)

    def drawPopup(self, screen):
        portrait = self.portraits.get(self.popupSpeaker)
        boxWidth, boxHeight = 580, 140
        boxX = SCREEN_WIDTH // 2 - boxWidth // 2
        boxY = SCREEN_HEIGHT - boxHeight - 20

        box = pygame.Surface((boxWidth, boxHeight), pygame.SRCALPHA)
        box.fill((20, 20, 20, 210))
        screen.blit(box, (boxX, boxY))
        pygame.draw.rect(screen, WHITE, (boxX, boxY, boxWidth, boxHeight), width=2, border_radius=8)

        font = pygame.font.SysFont("Arial", 18)
        smallFont = pygame.font.SysFont("Arial", 14)
        nameFont = pygame.font.SysFont("Arial", 15, bold=True)

        textX = boxX + 20
        textStartY = boxY + 20

        if portrait:
            plateSize = 90
            plateX, plateY = boxX + 16, boxY + 16
            plate = pygame.Surface((plateSize, plateSize), pygame.SRCALPHA)
            plate.fill((10, 10, 10, 230))
            screen.blit(plate, (plateX, plateY))
            pygame.draw.rect(screen, YELLOW, (plateX, plateY, plateSize, plateSize), width=2, border_radius=6)

            portraitRect = portrait.get_rect(center=(plateX + plateSize // 2, plateY + plateSize // 2))
            screen.blit(portrait, portraitRect)

            name = "Prickle" if self.popupSpeaker == "prickle" else "Queen Beeatrice"
            nameLabel = nameFont.render(name, True, YELLOW)
            nameRect = nameLabel.get_rect(centerx=plateX + plateSize // 2, top=plateY + plateSize + 4)
            screen.blit(nameLabel, nameRect)
            textX = plateX + plateSize + 20

        for i, line in enumerate(self.popupLines):
            label = font.render(line, True, WHITE)
            screen.blit(label, (textX, textStartY + i * 26))

        hint = smallFont.render("Press SPACE to continue", True, YELLOW)
        screen.blit(hint, (textX, boxY + boxHeight - 26))