import pygame
import music
from settings import *
from player import Player, PickupItem
from obstacles import Mushroom, Platform, InvisiblePlatform
from enemies import BossRat
from effects import ParticleSystem, createRatDeathEffect
from dialogue import Dialogue

class Scene2Boss:

    def __init__(self):

        # ==========================
        # Background
        # ==========================

        self.bg = pygame.image.load(r"scene2_assets/Rat Boss Level.png").convert()

        scale = SCREEN_HEIGHT / self.bg.get_height()

        self.bg = pygame.transform.scale(
            self.bg,
            (
                int(self.bg.get_width() * scale),
                SCREEN_HEIGHT
            )
        )


        self.bgWidth = self.bg.get_width()
        self.bgHeight = self.bg.get_height()


        # ==========================
        # Music Loop for Boss level
        # ==========================

        music.playMusic(
            "scene2_assets/Aerial City, Chika - Menu Music.mp3",
            0.3
        )


        # ==========================
        # Player bullets
        # ==========================

        self.bullets = pygame.sprite.Group()


        # ==========================
        # Player
        # ==========================

        self.player = Player(
            self.bullets,
            self.bgWidth,
            self.bgHeight
        )

        self.player.rect.x = 180
        self.player.rect.bottom = 420

        self.player.groundY = self.bgHeight + 300

        self.particles = ParticleSystem()


        # ==========================
        # Camera
        # ==========================

        self.cameraX = 0


        # ==========================
        # Arena Platforms
        # ==========================

        self.platforms = pygame.sprite.Group()
        self.visualPlatforms = pygame.sprite.Group()
        self.mushrooms = pygame.sprite.Group()


        # ==========================
        # Invisible Collision Platforms
        # ==========================

        self.platforms = pygame.sprite.Group()
        self.platformList = []

        platformData = [
            (0, 420, self.bgWidth, 50),
            (160, 200, 200, 20),
            (570, 200, 200, 20)
        ]

        for x, y, w, h in platformData:

            platform = InvisiblePlatform(x,y,w,h)

            self.platforms.add(platform)
            self.platformList.append(platform)


        # --------------------------
        # Visible platform images
        # --------------------------

        visualPlatformData = [
            # image path, x, y, scale
            (
                r"scene2_assets/Platform (Extended).png",
                0,
                280,
                0.45
            ),

            (
                r"scene2_assets/Platform.png",
                160,
                190,   # adjust visually
                0.55
            ),

            (
                r"scene2_assets/Platform.png",
                570,
                190,   # adjust visually
                0.55
            )
        ]


        for img, x, y, scale in visualPlatformData:

            platformImage = Platform(
                img,
                x,
                y,
                scale=scale,
                visible=True
            )

            self.visualPlatforms.add(platformImage)


        # ==========================
        # Bounce Mushroom
        # ==========================

        self.mushrooms = pygame.sprite.Group()

        mushroomData = [
            {
                "x":260,
                "y":310,
                "bounceForce":22,
                "angle":0,
                "scale":0.35
            },
            {
                "x":570,
                "y":310,
                "bounceForce":22,
                "angle":0,
                "scale":0.35
            },
        ]

        for data in mushroomData:

            mushroom = Mushroom(
                "scene3_assets/bouncy mushroom.png",
                data["x"],
                data["y"],
                data["bounceForce"],
                data["angle"],
                data["scale"]
            )

            self.mushrooms.add(mushroom)

        # ==========================
        # Boss
        # ==========================

        self.boss = BossRat(
            self.bgWidth - 350,
            420,
        )

        self.teleportItem = None


        # ==========================
        # Boss Dialogue
        # ==========================

        self.portraits = {
            "prickle": pygame.transform.scale_by(
                self.player.idleFrames[0], 1.3
            ),

            "rat": pygame.transform.scale_by(
                self.boss.currentFrames[0], 0.45
            )
        }

        self.speakerNames = {
            "prickle": "Prickle",
            "rat": "Mutated Rat"
        }

        self.dialogue = Dialogue()

        self.bossFightStarted = False
        self.bossDeathDialogueShown = False
        self.bossDeathTriggered = False

        self._showOpeningDialogue()


        # ==========================
        # Level completion
        # ==========================

        self.levelComplete = False
        self.deathHeight = self.bgHeight + 100

        self.fading = False
        self.fadeTimer = 0
        self.fadeDuration = 60


    # =====================================================
    # Update
    # =====================================================

    def update(self):

        keys = pygame.key.get_pressed()

        if self.fading:
            self.updateFade()
            return

        # Player movement + collision
        if self.dialogue.active:
            self.dialogue.update(keys)
            return

        self.player.update(
            keys,
            platforms=self.platforms
        )

        if self.bossFightStarted:
            self.boss.update(self.player)


        # ==========================
        # Fall Death Check
        # ==========================

        if self.player.rect.top > self.deathHeight:

            self.player.hp = 0


        # ==========================
        # Bounce Mushroom Collision
        # ==========================

        # Bounce Mushroom Animation
        self.mushrooms.update()

        for mushroom in self.mushrooms:

            mushroomTop = mushroom.topAt(
                self.player.rect.centerx
            )

            if mushroomTop is not None:

                if (
                    self.player.rect.bottom >= mushroomTop
                    and self.player.rect.bottom <= mushroomTop + 20
                    and self.player.velocityY > 0
                ):

                    mushroom.trigger()

                    self.player.velocityY = -mushroom.bounceForce

        # Bullets
        self.bullets.update()
        self.handleBossHits()

        # Boss death particle effect
        if self.boss.isDead and not self.bossDeathTriggered:

            self.bossDeathTriggered = True

            createRatDeathEffect(
                self.particles,
                (
                    self.boss.rect.centerx,
                    self.boss.rect.bottom
                )
            )

            self._showRatDeathDialogue()

        # Camera follow
        self.updateCamera()
        self.player.cameraX = self.cameraX

        # Particle
        self.particles.update()

        if self.teleportItem and not self.teleportItem.collected:

            distance = abs(
                self.player.rect.centerx -
                self.teleportItem.rect.centerx
            )

            self.teleportItem.is_near_player = distance < self.teleportItem.interaction_distance

            if (
                self.teleportItem.is_near_player
                and keys[pygame.K_r]
            ):

                self.teleportItem.collected = True
                self.player.pickupItem_sound.play()

                self.fading = True


    def updateFade(self):

        self.fadeTimer += 1

        if self.fadeTimer >= self.fadeDuration:
            self.levelComplete = True


    # =====================================================
    # Bullet Handling
    # =====================================================

    def handleBossHits(self):
        if self.boss.isDead:
            return

        for bullet in list(self.bullets):
            if self.boss.rect.colliderect(bullet.rect):

                self.boss.takeDamage(1)
                bullet.kill()

    
    # =====================================================
    # Camera
    # =====================================================

    def updateCamera(self):

        target = self.player.rect.centerx - SCREEN_WIDTH // 2


        # Keep camera inside background
        self.cameraX = max(
            0,
            min(
                target,
                self.bgWidth - SCREEN_WIDTH
            )
        )

    

    # =====================================================
    # Draw
    # =====================================================

    def draw(self, screen):

        # Background scrolling
        screen.blit(
            self.bg,
            (-self.cameraX,0)
        )

        # Draw particle
        self.particles.draw(
            screen,
            self.cameraX
        )

        # Bounce Mushrooms
        for mushroom in self.mushrooms:

            mushroomRect = mushroom.image.get_rect(
                midbottom=mushroom.rect.midbottom
            )

            mushroomRect.x -= self.cameraX

            screen.blit(
                mushroom.image,
                mushroomRect
            )

        # Draw visual platforms only
        for platform in self.visualPlatforms:

            platformRect = platform.rect.copy()
            platformRect.x -= self.cameraX

            screen.blit(
                platform.image,
                platformRect
            )

        # Boss
        bossRect = self.boss.rect.copy()
        bossRect.x -= self.cameraX

        screen.blit(
            self.boss.image,
            bossRect
        )

        # Player
        playerRect = self.player.rect.copy()
        playerRect.x -= self.cameraX

        screen.blit(
            self.player.image,
            playerRect
        )

        # Bullets
        for bullet in self.bullets:

            bulletRect = bullet.rect.copy()
            bulletRect.x -= self.cameraX

            screen.blit(
                bullet.image,
                bulletRect
            )

        # Pickup item
        if self.teleportItem:
            self.teleportItem.draw(
                screen,
                self.cameraX
            )

        # HUD
        self.player.drawHP(screen)
        self.player.drawAmmo(screen)
        self.boss.drawHP(screen)
        self.dialogue.draw(screen)

        # Fade UI
        if self.fading:

            alpha = int(
                255 *
                min(1, self.fadeTimer / self.fadeDuration)
            )

            overlay = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0,0,0,alpha)
            )

            screen.blit(
                overlay,
                (0,0)
            )

    def drawBossHP(self, screen):

        if self.boss.isDead:
            return

        barX = SCREEN_WIDTH//2 - 200
        barY = 40

        # background
        pygame.draw.rect(
            screen,
            BLACK,
            (
                barX,
                barY,
                400,
                25
            )
        )

        # hp
        hpWidth = int(
            400 *
            (self.boss.hp / self.boss.maxHP)
        )

        pygame.draw.rect(
            screen,
            RED,
            (
                barX,
                barY,
                hpWidth,
                25
            )
        )

        pygame.draw.rect(
            screen,
            WHITE,
            (
                barX,
                barY,
                400,
                25
            ),
            3
        )

    def _showOpeningDialogue(self):

        self.player.controllable = False

        self.dialogue.show(
            [
                "Finally found you!",
                "You look a bit different than I remember...",
                "Anyways give me back my ancient seed!",
            ],

            portrait=self.portraits["prickle"],
            name=self.speakerNames["prickle"],

            onDismiss=self._showRatDialogue
        )

    def _showRatDialogue(self):

        self.dialogue.show(
            [
                "You dare enter my territory?",
                "You shall become sustenance for me! Prepare yourself!"
            ],

            portrait=self.portraits["rat"],
            name=self.speakerNames["rat"],

            onDismiss=self.startBossFight
        )

    def startBossFight(self):

        self.player.controllable = True
        self.bossFightStarted = True

    def _showRatDeathDialogue(self):

        self.dialogue.show(
            [
                "Ughh...",
                "Fine you can have it back..",
                "Feather is in the Thorned Canopy..."
            ],

            portrait=self.portraits["rat"],
            name=self.speakerNames["rat"],

            onDismiss=self.spawnTeleportItem
        )

    def spawnTeleportItem(self):

        self.player.controllable = True

        self.itemX = self.boss.rect.centerx - 25
        self.itemY = self.boss.rect.bottom - 50

        self.teleportItem = PickupItem(
            self.itemX,
            self.itemY,
            "scene2_assets/Ancient Seed (Clear).png",
            [
                "My ancient seed.  ",
                "Press R to travel onward."
            ],
            title="Teleport",
            target_state="SCENE3"
        )

        # Resize seed only
        self.teleportItem.image = pygame.transform.scale(
            self.teleportItem.image,
            (50, 50)
        )

        # Reset rect based on new image position
        self.teleportItem.rect = self.teleportItem.image.get_rect(
            topleft=(self.itemX, self.itemY)
        )