import pygame
import random
from settings import *
from player import Player
from enemies import Wasp, WaspQueen, Sting
from obstacles import Platform, MovingPlatform
from dialogue import Dialogue
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
            MovingPlatform(r"scene4_assets/flower_platform1.png", x=400, y=380, scale=0.5, moveRange=100, speed=2, axis='X'),
            Platform(r"scene4_assets/flower_platform1.png", x=750, y=320, scale=0.5),
            MovingPlatform(r"scene4_assets/flower_platform1.png", x=1050, y=380, scale=0.5, moveRange=100, speed=1.5, axis='Y'),
            Platform(r"scene4_assets/flower_platform1.png", x=1100, y=380, scale=0.5),
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
        self.speakerNames = {
            "prickle": "Prickle",
            "queen": "Queen Beeatrice",
        }

        # Finite state engine handles death routing explicitly
        self.state = "INTRO"
        self.levelComplete = False

        # Dialogue — shared textbox component (see dialogue.py), same one
        # Scene1 uses. _showDialogue below wires it up to this scene's
        # state machine and Player.controllable the same way Scene1's does.
        self.dialogue = Dialogue()
        self._showDialogue(
            ["The flowers glow strangely here...", "Something's watching me."],
            speaker="prickle",
            onDismiss=self._showBossCommand,
        )

        # Death handling variables
        self.deathTimer = 0
        self.deathDuration = 120 # ~2 seconds for animation sequence to unfold

    def _showDialogue(self, lines, speaker="prickle", style="center", next=None, onDismiss=None):
        """Open the shared dialogue box, resolving a speaker key into this
        scene's portrait/name. `next` is a convenience for the common case
        (just set self.state once dismissed); pass a custom `onDismiss`
        instead for anything fancier (e.g. chaining straight into another
        dialogue, like the intro -> boss-command -> swarm sequence below)."""
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
        """Spawns a swarm contextually anchored near the scrolling arena section."""
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
            self.player.controllable = False
            self.deathTimer = self.deathDuration
            # If your Player class has a death sound, trigger it here:
            # self.player.death_sound.play()

        if self.state == "DEATH":
            self.updateDeathSequence()
            return

        if self.dialogue.active:
            if hasattr(self.player, 'applyParalysis'):
                self.player.applyParalysis(1)
            self.dialogue.update(keys)
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
        # Force player object to switch into internal death frame sequence indexes
        if hasattr(self.player, 'animate_death'):
            self.player.animate_death()
        elif hasattr(self.player, 'deathFrames'):
            # Fallback frame switcher logic manually over local variables
            self.player.image = self.player.deathFrames[min(
                len(self.player.deathFrames) - 1,
                (self.deathDuration - self.deathTimer) // 10
            )]

        if self.deathTimer <= 0:
            # Reload loop or trigger reset game signals contextually here
            self.__init__()

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
        self.wasps.update(self.player)

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
                    speaker="queen", next="BOSS_FIGHT",
                )

    def updateBossFight(self):
        self.boss.update(self.player, active=True)
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
                effects.create_impact_burst(quill.rect.center)
                quill.kill()

        if self.boss.hp <= 0 and self.flowerRect is None:
            self.flowerRect = self.flowerImage.get_rect(center=self.boss.rect.center)
            self._showDialogue(
                ["The Eternal Flower...", "It's free."],
                speaker="prickle", next="VICTORY",
            )

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
                self._showDialogue(
                    ["You recovered all the treasures!", "Prickle's Grove is safe again."],
                    speaker="prickle",
                )
                self.levelComplete = True
        else:
            self.nearFlower = False

    def draw(self, screen):
        # Apply camera offset to every landscape object drawn onto the display context
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

        # Interface Overlays (Drawn natively directly on viewport base vectors)
        self.player.drawAmmo(screen)
        self.player.drawHP(screen)
        effects.update_and_draw_particles(screen, self.cameraX)

        self.dialogue.draw(screen)
