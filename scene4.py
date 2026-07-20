import pygame
import random
from settings import *
from player import Player
from enemies import Wasp, WaspQueen, Sting
from obstacles import Platform, MovingPlatform
import effects

class Scene4:
    def __init__(self, dialogue_system):
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

        # Dialogue System Reference
        self.dialogue = dialogue_system
        self.speakerNames = {
            "prickle": "Prickle",
            "queen": "Queen Beeatrice"
        }
        self.portraits = {
            "prickle": pygame.transform.scale_by(self.player.idleFrames[0], 1.3),
            "queen" : pygame.transform.scale_by(self.boss.attackRFrames[0], 0.7)
        }

        # Finite state engine handles death routing explicitly
        self.state = "INTRO"
        self.levelComplete = False

        # Fade-to-black transition back to the main menu, triggered once the
        # closing victory dialogue is dismissed (see _startVictoryFade).
        # Same pattern as Scene3's Scene4 handoff — main.py watches
        # levelComplete to know when the fade has actually finished.
        self.fading = False
        self.fadeTimer = 0
        self.fadeDuration = 60  # 1 second at 60fps

        # Trigger Initial Dialogue State
        self._showDialogue(
            ["The flowers glow strangely here...", "Something's watching me."],
            speaker="prickle",
            next="BOSS_COMMAND",
            onDismiss=self._showBossCommand
        )

        # Death handling variables
        self.deathTimer = 0
        self.deathDuration = 120 # ~2 seconds for animation sequence to unfold

        # Background music
        pygame.mixer.music.load(r"scene4_assets/scene4_bgmusic.mp3")
        pygame.mixer.music.set_volume(0.2) 
        pygame.mixer.music.play(loops=-1)

    def _showDialogue(self, lines, speaker="prickle", style="center", next=None, onDismiss=None):
        """Open the shared dialogue box, resolving a speaker key into this
        scene's portrait/name."""
        def defaultOnDismiss():
            self.player.controllable = True
            if next is not None:
                self.state = next

        self.player.controllable = False
        self.dialogue.show(
            lines,
            portrait=self.portraits.get(speaker),
            name=self.speakerNames.get(speaker, speaker),
            style=style,
            onDismiss=onDismiss if onDismiss is not None else defaultOnDismiss,
        )

    def _showBossCommand(self):
        self._showDialogue(
            ["Intruder! Wasps, tear this hedgehog apart!"],
            speaker="queen",
            onDismiss=self._beginSwarm,
        )

    def _beginSwarm(self):
        self.player.controllable = True
        self.state = "SWARM"
        self.currentWaveIndex = 0
        self.spawnWaspWave()

    def spawnWaspWave(self):
        self.wasps.empty()
        numWasps = self.waveConfigurations[self.currentWaveIndex]

        for _ in range(numWasps):
            sx = random.randint(1100, 1500)
            sy = random.randint(100, 250)
            wasp = Wasp(sx, sy)
            wasp.speed = 1.5
            self.wasps.add(wasp)

    def update(self):
        keys = pygame.key.get_pressed()

        # Check death trigger immediately before processing state engine vectors
        if self.player.hp <= 0 and self.state != "DEATH":
            self.state = "DEATH"
            self.player.isDeath = True
            self.player.controllable = False
            self.deathTimer = self.deathDuration

        if self.state == "DEATH":
            self.updateDeathSequence()
            return

        # Let dialogue system update and suppress gameplay if active
        if self.dialogue.active:
            self.dialogue.update(keys)
            self.updateCamera()
            if self.boss:
                self.boss.update(self.player, active=False)
            return

        if self.fading:
            self.updateFade()
            return

        for platform in self.platforms:
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

    def updateDeathSequence(self):
        """Processes death sequence timers and tracks animations independently of controls."""
        self.deathTimer -= 1
        self.player.image = self.player.deathFrames[min(
            len(self.player.deathFrames) - 1,
            (self.deathDuration - self.deathTimer) // 10
        )]

        if self.deathTimer <= 0:
            self.__init__(self.dialogue)

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
                self._showDialogue(
                    ["My swarm has fallen...", "Now you face me directly!"],
                    speaker="queen",
                    next="BOSS_FIGHT"
                )

    def updateBossFight(self):
        self.boss.update(self.player, active=True)
        self.boss.updateBuzz(self.player)
        self.stings.update()

        for sting in list(self.stings):
            if sting.rect.colliderect(self.player.rect):
                self.player.applyParalysis(PARALYSIS_DURATION)
                sting.kill()

        for quill in list(self.quills):
            if quill.rect.colliderect(self.boss.rect) and not self.boss.teleporting:
                self.boss.shakeTimer = 15      
                self.boss.shakeMagnitude = 6                   
                wave = effects.HitShockwave(quill.rect.centerx, quill.rect.centery, max_radius=70)
                self.bossEffects.add(wave)
                self.boss.takeDamage(1)
                effects.create_impact_burst(quill.rect.center)
                quill.kill()

        if self.boss.hp <= 0 and self.flowerRect is None:
            self.flowerRect = self.flowerImage.get_rect(center=self.boss.rect.center)
            self._showDialogue(
                ["The Eternal Flower...", "It's free."],
                speaker="prickle",
                next="VICTORY"
            )

    def updateVictory(self, keys):
        if self.flowerCollected:
            return

        if self.flowerRect and self.player.rect.colliderect(self.flowerRect):
            distance = abs(self.player.rect.centerx - self.flowerRect.centerx)
            self.nearFlower = distance < 60

            if self.nearFlower and keys[pygame.K_r]:
                self.flowerCollected = True
                self.player.pickupItem_sound.play()

                self._showDialogue(
                    ["You recovered all the treasures!", "Prickle's Grove is safe again."],
                    speaker="prickle",
                    onDismiss=self._startVictoryFade,
                )
        else:
            self.nearFlower = False

    def _startVictoryFade(self):
        # Fires once the closing victory line is dismissed — hands control
        # back to Prickle isn't needed here since the fade freezes gameplay
        # immediately anyway, but keep the same contract as the other
        # dialogue callbacks in case anything else reads controllable.
        self.player.controllable = True
        self.fading = True

    def updateFade(self):
        self.fadeTimer += 1
        if self.fadeTimer >= self.fadeDuration:
            self.levelComplete = True

    def draw(self, screen):
        # Background positioning
        screen.blit(self.bg, (-self.cameraX, 0))

        for platform in self.platforms:
            screen.blit(platform.image, (platform.rect.x - self.cameraX, platform.rect.y))

        for wasp in self.wasps:
            screen.blit(wasp.image, (wasp.rect.x - self.cameraX, wasp.rect.y))

        # Render boss status adjustments
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

        # Player rendering updates
        screen.blit(self.player.image, (self.player.rect.x - self.cameraX, self.player.rect.y))

        for quill in self.quills:
            screen.blit(quill.image, (quill.rect.x - self.cameraX, quill.rect.y))

        for effect in self.bossEffects:
            effect.draw(screen, self.cameraX)

        # Interface elements
        self.player.drawAmmo(screen)
        self.player.drawHP(screen)
        effects.update_and_draw_particles(screen, self.cameraX)

        # Let shared global UI draw dialogue layer natively on top of everything
        if self.dialogue.active:
            self.dialogue.draw(screen)

        if self.fading:
            alpha = int(255 * min(1, self.fadeTimer / self.fadeDuration))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, alpha))
            screen.blit(overlay, (0, 0))