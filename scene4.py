import pygame
import random
from settings import *
from player import Player
from enemies import Wasp, WaspQueen, Sting
from obstacles import Platform, MovingPlatform
from obstacles import Nest 
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

        # 2. Distribute platforms & vines cleanly across the entire level width
        self.platforms = [
            # Zone 1: Entry & Initial Jumps
            Platform(r"scene4_assets/flower_platform1.png", x=80, y=380, scale=0.5),
            Platform(r"scene4_assets/flower_platform1.png", x=220, y=260, scale=0.5),
            Platform(r"scene4_assets/vine1.png", x=250, y=280, scale=0.7),
            MovingPlatform(r"scene4_assets/flower_platform2.png", x=420, y=380, scale=0.5, moveRange=100, speed=2, axis='X'),
            
            # Zone 2: Mid-Stage Traversal
            Platform(r"scene4_assets/flower_platform1.png", x=700, y=320, scale=0.5),
            MovingPlatform(r"scene4_assets/flower_platform2.png", x=1020, y=140, scale=0.5, moveRange=80, speed=1.5, axis='Y'),
            MovingPlatform(r"scene4_assets/flower_platform2.png", x=1020, y=380, scale=0.5, moveRange=100, speed=1.5, axis='Y'),
            
            # Zone 3: Far-Right Expansion
            Platform(r"scene4_assets/flower_platform1.png", x=1350, y=280, scale=0.5),
            Platform(r"scene4_assets/vine1.png", x=1520, y=240, scale=0.7),
            MovingPlatform(r"scene4_assets/flower_platform2.png", x=1680, y=350, scale=0.5, moveRange=90, speed=2, axis='X'),
            Platform(r"scene4_assets/flower_platform1.png", x=1950, y=260, scale=0.5),
            Platform(r"scene4_assets/vine1.png", x=2100, y=200, scale=0.7),
            
            # Final Destination Ground Platform at the end of the world
            Platform(r"scene4_assets/flower_platform1.png", x=2250, y=340, scale=0.5),
        ]

        self.endPlatform = self.platforms[-1]  # Target ground platform for falling flower

        # Setup Wasp Nest directly above the final platform at the very end of the stage
        self.nest = Nest(r"scene4_assets/wasp_nest.png", x=2270, y=160, maxHits=5, scale=0.2)

        # Load broken nest image and match scale
        self.brokenNestImg = pygame.image.load(r"scene4_assets/wasp_nest_broken.png").convert_alpha()
        self.brokenNestImg = pygame.transform.scale_by(self.brokenNestImg, 0.2)

        startPlatform = self.platforms[0]
        self.player.rect.midbottom = (startPlatform.rect.centerx, startPlatform.rect.top)
        self.lastSafePos = self.player.rect.midbottom

        # 3. Position the Boss Arena
        self.boss = WaspQueen(1350, 150, teleportSpots=[], stingGroup=self.quills)

        self.bossGroup = pygame.sprite.Group()
        self.bossGroup.add(self.boss)
        self.stings = pygame.sprite.Group()
        self.boss.stingGroup = self.stings
        self.bossEffects = pygame.sprite.Group()

        # Track sting warning dialogue trigger
        self.stingDialogueShown = False

        # Wave tracking
        self.wasps = pygame.sprite.Group()
        self.waveConfigurations = [3, 4, 5]
        self.currentWaveIndex = 0

        self.flowerImage = pygame.image.load(r"scene4_assets/eternal_flower.png").convert_alpha()
        self.flowerImage = pygame.transform.scale_by(self.flowerImage, 0.5)
        self.flowerRect = None
        self.flowerCollected = False
        self.nearFlower = False
        
        # Flower physics variables for falling from nest
        self.flowerFalling = False
        self.flowerVelocityY = 0

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

        # Wave 2 (index 1) spawns from the left; Waves 1 and 3 spawn from the right
        for _ in range(numWasps):
            if self.currentWaveIndex == 1:
                sx = random.randint(100, 400)   # Spawn on the LEFT side
            else:
                sx = random.randint(1100, 1500) # Spawn on the RIGHT side
                
            sy = random.randint(100, 250)
            wasp = Wasp(sx, sy)
            wasp.speed = 1.5
            self.wasps.add(wasp)

    def getRandomScreenSpot(self):
        """Calculates a random coordinate on either the LEFT or RIGHT side of current screen view."""
        side = random.choice(["LEFT", "RIGHT"])
        
        if side == "LEFT":
            minX = int(self.cameraX + 100)
            maxX = int(self.cameraX + 250)
        else:
            minX = int(self.cameraX + SCREEN_WIDTH - 250)
            maxX = int(self.cameraX + SCREEN_WIDTH - 100)

        # Clamped inside world boundary limits
        minX = max(50, minX)
        maxX = min(self.worldWidth - 50, maxX)

        targetX = random.randint(minX, max(minX + 1, maxX))
        targetY = random.randint(100, 300)
        return (targetX, targetY)

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

        self.nest.update()

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
        elif self.state == "DESTROY_NEST":
            self.updateDestroyNest()
        elif self.state == "VICTORY":
            self.updateVictory(keys)

        # Process physics for falling flower after nest destruction
        if self.flowerFalling and self.flowerRect:
            self.flowerVelocityY += 0.4  # Gravity
            self.flowerRect.y += int(self.flowerVelocityY)
            targetY = self.endPlatform.rect.top - self.flowerRect.height
            if self.flowerRect.y >= targetY:
                self.flowerRect.y = targetY
                self.flowerFalling = False

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
                if hasattr(wasp, 'buzz_sound') and wasp.buzz_sound:
                    wasp.buzz_sound.stop()
                if hasattr(wasp, 'buzzChannel') and wasp.buzzChannel:
                    wasp.buzzChannel.stop()
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
        # Override boss's teleport spot list dynamically before update
        if self.boss.teleportPhase == "out" and self.boss.teleportTimer == 1:
            self.boss.teleportSpots = [self.getRandomScreenSpot()]

        self.boss.update(self.player, active=True)
        self.stings.update()

        for sting in list(self.stings):
            if sting.rect.colliderect(self.player.rect):
                self.player.applyParalysis(60)
                sting.kill()

                # Trigger dialogue warning when first hit by a sting
                if not self.stingDialogueShown:
                    self.stingDialogueShown = True
                    self._showDialogue(
                        ["Ugh! Watch out for that sting!", "It paralyzes you for 3 seconds!"],
                        speaker="prickle"
                    )

        for quill in list(self.quills):
            if quill.rect.colliderect(self.boss.rect) and not self.boss.teleporting:
                self.boss.shakeTimer = 15      
                self.boss.shakeMagnitude = 6                   
                wave = effects.HitShockwave(quill.rect.centerx, quill.rect.centery, max_radius=70)
                self.bossEffects.add(wave)
                self.boss.takeDamage(1)
                effects.create_impact_burst(quill.rect.center)
                quill.kill()

        # Defeating Queen now prompts player to shoot down the nest
        if self.boss.hp <= 0:
            self._showDialogue(
                ["The Queen is defeated!", "Shoot down the Wasp Nest to retrieve the flower!"],
                speaker="prickle",
                next="DESTROY_NEST"
            )

    def updateDestroyNest(self):
        """Handle Quill hits on the Wasp Nest until it turns black and drops the flower."""
        for quill in list(self.quills):
            if quill.rect.colliderect(self.nest.rect):
                wasHit = self.nest.takeHit()
                if wasHit:
                    effects.create_impact_burst(quill.rect.center)
                    quill.kill()

                if self.nest.destroyed and self.flowerRect is None:
                    # Spawn flower at nest center and initiate drop
                    self.flowerRect = self.flowerImage.get_rect(center=self.nest.rect.center)
                    self.flowerFalling = True
                    self.flowerVelocityY = 0
                    self.state = "VICTORY"

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

        # Render Nest relative to camera space
        nestDrawRect = self.nest.rect.copy()
        nestDrawRect.x -= self.cameraX
        if self.nest.destroyed:
            screen.blit(self.brokenNestImg, nestDrawRect)
        elif self.nest.flashTimer > 0:
            screen.blit(self.nest._brightFrame(self.nest.frameIndex), nestDrawRect)
        else:
            screen.blit(self.nest.frames[self.nest.frameIndex], nestDrawRect)

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

        # Delegate yellow aura rendering to the effects module when paralyzed
        effects.draw_paralysis_aura(screen, self.player, self.cameraX)

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

        # Shared UI dialogue box rendering
        if self.dialogue.active:
            self.dialogue.draw(screen)

        if self.fading:
            alpha = int(255 * min(1, self.fadeTimer / self.fadeDuration))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, alpha))
            screen.blit(overlay, (0, 0))