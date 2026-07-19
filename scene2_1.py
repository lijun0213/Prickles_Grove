import pygame
from settings import *
from player import Player
from obstacles import InvisiblePlatform, SporeCloud, Mushroom, Platform
from enemies import Rat
from effects import ParticleSystem


class Scene2_1:

    def __init__(self):

        # ==========================
        # Background
        # ==========================

        self.bg = pygame.image.load(r"scene2_assets/Mushroom Meadows Background 2 (Extended).png").convert()

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

        self.showCoords = True
        self.debugFont = pygame.font.SysFont("Consolas",16)


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
        self.player.rect.bottom = 350

        self.player.groundY = self.bgHeight + 300

        self.sporeDamageCooldown = 0
        self.spikeDamageCooldown = 0

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
            (30, 360, 975, 20),
            (1250, 360, 390, 20),
            (1640, 200, 440, 20),
            (2170, 445, 565, 20),
            (2120, 240, 390, 20),
            (2500, 280, 235, 20)
            
        ]

        for x, y, w, h in platformData:

            platform = InvisiblePlatform(x,y,w,h)

            self.platforms.add(platform)
            self.platformList.append(platform)


        # ==========================
        # Spore Cloud
        # ==========================
        self.spores = pygame.sprite.Group()

        sporeData = [
            {"x": 380, "y": 320, "w": 190, "h": 120, "scale": 0.35},
            {"x": 680, "y": 320, "w": 190, "h": 120, "scale": 0.35},
            {"x": 1380, "y": 320, "w": 190, "h": 120, "scale": 0.35},
            {"x": 1810, "y": 160, "w": 190, "h": 120, "scale": 0.35},
            {"x": 2580, "y": 335, "w": 190, "h": 120, "scale": 0.8}
        ]

        for data in sporeData:
            self.spores.add(SporeCloud("scene2_assets/Spores.png",
                data["x"],
                data["y"],
                int(data["w"] * data["scale"]),
                int(data["h"] * data["scale"])
                )
            )

        # ==========================
        # Spike Traps
        # ==========================

        self.spikes = []

        spikeData = [
            {
                "x": 980,
                "y": 380,
                "scale": 1.4
            }
        ]

        for data in spikeData:
            spike = Platform(
                "scene2_assets/Spikefall Trap.png",
                data["x"],
                data["y"],
                scale=data["scale"],
                hazard=True
            )

            self.spikes.append(spike)


        # ==========================
        # Rat Minions
        # ==========================

        self.rats = pygame.sprite.Group()

        ratData = [
            {"platform":0, "offset":200, "direction":-1, "speed":2, "hp":3},
            {"platform":0, "offset":450, "direction":-1, "speed":3, "hp":4},
            {"platform":4, "offset":-100, "direction":1, "speed":2, "hp":2},
            {"platform":4, "offset":150, "direction":-1, "speed":2, "hp":2},
            {"platform":3, "offset":200, "direction":-1, "speed":3, "hp":4}
        ]

        for data in ratData:
            platform = self.platformList[data["platform"]]

            rat = Rat("scene2_assets/rat idle.png", platform, data["offset"], data["direction"], data["speed"], data["hp"], self.particles)

            self.rats.add(rat)


        # ==========================
        # Bounce Mushroom
        # ==========================

        self.mushrooms = pygame.sprite.Group()

        mushroomData = [
            {
                "x":1580,
                "y":260,
                "bounceForce":22,
                "angle":0,
                "scale":0.35
            },
            {
                "x":2170,
                "y":345,
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
        # Level completion
        # ==========================

        self.levelComplete = False
        self.deathHeight = self.bgHeight + 100



    # =====================================================
    # Update
    # =====================================================

    def update(self):

        keys = pygame.key.get_pressed()


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


        # ==========================
        # Spike Damage
        # ==========================

        if self.spikeDamageCooldown > 0:
            self.spikeDamageCooldown -= 1


        for spike in self.spikes:

            if spike.rect.colliderect(self.player.rect):

                if self.spikeDamageCooldown == 0:

                    self.player.takeDamage(3)
                    self.spikeDamageCooldown = 60


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

        # Spore Cloud
        for spore in self.spores:

            sporeRect = spore.rect.copy()
            sporeRect.x -= self.cameraX

            screen.blit(
                spore.image,
                (
                    spore.rect.x - self.cameraX,
                    spore.rect.y
                )
            )

        self.particles.draw(
            screen,
            self.cameraX
        )

        # Spike traps
        for spike in self.spikes:
            spikeRect = spike.rect.copy()
            spikeRect.x -= self.cameraX

            screen.blit(
                spike.image,
                spikeRect
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
