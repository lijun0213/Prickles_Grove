import pygame
import music
from settings import *
from player import Player
from obstacles import InvisiblePlatform, Boulder, SporeCloud
from enemies import Rat
from effects import ParticleSystem
from dialogue import Dialogue


class Scene2:

    def __init__(self):

        # ==========================
        # Background
        # ==========================

        self.bg = pygame.image.load(r"scene2_assets/Mushroom Meadows Background.png").convert()

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
        # Music Loop for both minion levels
        # ==========================

        music.playMusic(
            "scene2_assets/C418 - Aria Math (Minecraft Volume Beta).mp3",
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

        self.player.rect.x = 150
        self.player.rect.bottom = 310

        self.player.groundY = self.bgHeight + 300

        self.boulderDamageCooldown = 0
        self.sporeDamageCooldown = 0

        self.particles = ParticleSystem()


        # ==========================
        # Camera
        # ==========================

        self.cameraX = 0


        # ==========================
        # Invisible Collision Platforms
        # ==========================

        self.platforms = pygame.sprite.Group()
        self.platformList = []

        platformData = [
            (100, 320, 290, 20),
            (480, 325, 280, 20),
            (720, 360, 240, 20),
            (950, 340, 250, 20),
            (950, 430, 180, 20),
            (620, 490, 320, 20),
            (90, 470, 310, 20),
            (400, 430, 220, 20),
            (1090,475,110,20)
        ]

        for x, y, w, h in platformData:

            platform = InvisiblePlatform(x,y,w,h)

            self.platforms.add(platform)
            self.platformList.append(platform)


        # ==========================
        # Boulder
        # ==========================
        self.boulders = pygame.sprite.Group()

        boulderData = [
            {"x":600, "y":205}
        ]

        for data in boulderData:
            self.boulders.add(Boulder("scene2_assets/Boulder.png", data["x"], data["y"]))


        # ==========================
        # Spore Cloud
        # ==========================
        self.spores = pygame.sprite.Group()

        sporeData = [
            (90,350,190,120),
        ]

        for x,y,w,h in sporeData:
            self.spores.add(SporeCloud("scene2_assets/Spores.png",x,y,w,h))


        # ==========================
        # Rat Minions
        # ==========================

        self.rats = pygame.sprite.Group()

        ratData = [
            {"platform":3, "offset":0, "direction":-1, "speed":2, "hp":3},
            {"platform":5, "offset":40, "direction":1, "speed":2, "hp":4},
            {"platform":7, "offset":-20, "direction":-1, "speed":2, "hp":3}
        ]

        for data in ratData:
            platform = self.platformList[data["platform"]]

            rat = Rat("scene2_assets/rat idle.png", platform, data["offset"], data["direction"], data["speed"], data["hp"], self.particles)

            self.rats.add(rat)


        # ==========================
        # Opening dialogue
        # ==========================
        # Same shared textbox component every scene uses. Freezes the scene
        # (see the top of update()) until dismissed, then hands control
        # back to Prickle.

        self.dialogue = Dialogue()
        self.dialogue.show(
            ["According to Nugget, Giant Rat lives here...", "How nasty... so many rats..."],
            portrait=pygame.transform.scale_by(self.player.idleFrames[0], 1.3),
            name="Prickle",
            onDismiss=self._endOpeningDialogue,
        )
        self.player.controllable = False


        # ==========================
        # Level completion
        # ==========================

        self.levelComplete = False
        self.deathHeight = self.bgHeight + 100



    # =====================================================
    # Opening dialogue
    # =====================================================

    def _endOpeningDialogue(self):
        self.player.controllable = True


    # =====================================================
    # Update
    # =====================================================

    def update(self):

        keys = pygame.key.get_pressed()

        if self.dialogue.active:
            self.dialogue.update(keys)
            return


        # Player movement + collision
        self.player.update(
            keys,
            platforms=self.platforms
        )

        # ==========================
        # Fall Death Check
        # ==========================

        if self.player.rect.top > self.deathHeight:

            self.player.hp = 0

        # ==========================
        # Boulder Damage
        # ==========================

        if self.boulderDamageCooldown > 0:
            self.boulderDamageCooldown -= 1


        for boulder in self.boulders:

            boulder.checkEdge()

            if self.player.rect.colliderect(boulder.rect):

                if self.boulderDamageCooldown == 0:

                    self.player.takeDamage(1)
                    self.boulderDamageCooldown = 60
            
        self.boulders.update()

        # ==========================
        # Spore Cloud Damage
        # ==========================

        if self.sporeDamageCooldown > 0:
            self.sporeDamageCooldown -= 1


        for spore in self.spores:

            if self.player.rect.colliderect(spore.rect):

                if self.sporeDamageCooldown == 0:

                    self.player.takeDamage(1)
                    self.sporeDamageCooldown = 60

        self.spores.update()

        for spore in self.spores:
            spore.emit(self.particles)


        # Rat Minions
        self.rats.update(self.player)

        # Bullets
        self.bullets.update()
        self.handleBulletHits()

        # Camera follow
        self.updateCamera()
        self.player.cameraX = self.cameraX

        # Particle
        self.particles.update()

        # Check if player reaches end
        if self.player.rect.x >= self.bgWidth - 100:
            self.levelComplete = True


    # =====================================================
    # Bullet Handling
    # =====================================================

    def handleBulletHits(self):

        for bullet in list(self.bullets):

            hitRat = pygame.sprite.spritecollideany(
                bullet,
                self.rats
            )

            if hitRat:

                hitRat.takeDamage(1)

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

        # Boulder
        for boulder in self.boulders:

            boulderRect = boulder.rect.copy()
            boulderRect.x -= self.cameraX

            screen.blit(
                boulder.image,
                boulderRect
            )

        # Spore Cloud
        for spore in self.spores:

            sporeRect = spore.rect.copy()
            sporeRect.x -= self.cameraX

            screen.blit(
                spore.image,
                sporeRect
            )

        self.particles.draw(
            screen,
            self.cameraX
        )

        # Rat Minions
        for rat in self.rats:

            ratRect = rat.rect.copy()
            ratRect.x -= self.cameraX

            screen.blit(
                rat.image,
                ratRect
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

        # HUD
        self.player.drawHP(screen)
        self.player.drawAmmo(screen)

        # Dialogue overlay, drawn last so it sits on top of everything
        self.dialogue.draw(screen)