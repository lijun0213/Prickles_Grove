import pygame
from settings import *
from player import Player
from obstacles import Platform, Wall, Mushroom, Nest
from enemies import Feathers

class Scene3:
    def __init__(self):

        self.bg = pygame.image.load(r"scene3_assets/scene 3 background.jpg").convert()
        bgWidth, bgHeight = self.bg.get_size()
        scale = SCREEN_WIDTH / bgWidth
        self.bg = pygame.transform.scale(self.bg, (SCREEN_WIDTH, int(bgHeight * scale)))
        self.bgHeight = self.bg.get_height()

        self.bullets = pygame.sprite.Group()
        self.player = Player(self.bullets, self.bg.get_width(), self.bgHeight)

        self.groundY = SCREEN_HEIGHT
        self.player.rect.x = 100
        self.player.rect.bottom = self.groundY
        self.player.groundY = self.groundY

        # Once Prickle climbs above this screen-y, the camera starts
        # following him upward instead of letting him keep climbing off the
        # top of the screen. (Camera-follow itself now lives in Player —
        # see Player.updateCamera — this just opts this scene into it.)
        self.player.cameraFollowY = 365


        self.platforms = [
            # Floor strip along the bottom of the screen — invisible (not
            # drawn), just a collision surface so falling bombs (and
            # Prickle) land on solid ground instead of passing through.
            # floor.png is a thin 500x3 sliver, stretched to span the full
            # screen width but kept at its native (near-zero) thickness.
            Platform(r"scene3_assets/floor.png", x=0, y=SCREEN_HEIGHT - 3, scale=(SCREEN_WIDTH / 500, 1), visible=False),
            Platform(r"scene3_assets/branch_right.png", x=240, y=300, angle=22, scale = (2.2, 1.3)),
            Platform(r"scene3_assets/bridge.png", x=92, y=190, scale = (1.23, 1.1)),
            Platform(r"scene3_assets/branch_left.png", x=75, y=70, angle=22, scale = (1.7, 1.3)),
            Platform(r"scene3_assets/branch_right.png", x=360, y=-50, angle=22, scale = (1.5, 1.3)),
            Platform(r"scene3_assets/branch_left.png", x=75, y=-155, angle=-22, scale = (1.7, 1.3)),
            Mushroom(r"scene3_assets/bouncy mushroom.png", x=100, y=-220, bounceForce=20, angle=-10),
            Platform(r"scene3_assets/spiky branch.png", x=285, y=-400, angle=-50, scale = 1, blocksBullets=True),
        ]


        self.walls = [
            Wall(x=635, top=-1000, bottom=SCREEN_HEIGHT),
            Wall(x=80, top=-1000, bottom=290),
        ]

        self.nests = [
            Nest(r"scene3_assets/bird nest.png", x=510, y=-425, maxHits=5),
        ]

        # Feathers — the Scene 3 boss. Flies left/right randomly and hovers
        # a fixed distance above wherever Prickle currently is, so he's
        # always overhead as Prickle climbs toward the nest.
        self.bombs = pygame.sprite.Group()
        self.feathers = Feathers(x=400, y=-350, bombGroup=self.bombs, hp=10, hoverOffset=250, wanderRange=150,
                                  bombIntervalSeconds=1)

    def update(self):
        keys = pygame.key.get_pressed()
        prevRect = self.player.rect.copy()

        # Platform sticking, walking-along-surface, "S" drop-through, and
        # camera-follow are all handled generically inside Player now — just
        # hand it this scene's platforms each frame.
        self.player.update(keys, platforms=self.platforms)

        self.handleWallCollisions(prevRect)

        # Keep platforms/walls/nests anchored to the background art as the
        # camera scrolls (Player owns scrollY; this scene just reacts to it).
        for platform in self.platforms:
            platform.rect.y = platform.baseY + self.player.scrollY
            platform.update()  # advances things like the mushroom's bounce animation
        for wall in self.walls:
            wall.rect.y = wall.baseY + self.player.scrollY
        for nest in self.nests:
            nest.rect.y = nest.baseY + self.player.scrollY
            nest.update()  # fades the hit-flash back to normal

        self.bullets.update()
        self.handleBulletHits()

        self.feathers.update(self.player, self.platforms)

        self.bombs.update(self.platforms)
        self.handleBombHits()

    def handleBombHits(self):
        for bomb in list(self.bombs):
            # Only the explosion itself can hurt Prickle — not the fall,
            # not just sitting landed with its fuse burning. hasDealtDamage
            # keeps this a one-time hit rather than damage every frame the
            # blast/smoke animation is playing. The bomb removes itself
            # once its animation finishes (see Bomb.animate).
            if not bomb.exploded or bomb.hasDealtDamage:
                continue
            if bomb.rect.colliderect(self.player.rect):
                self.player.takeDamage(bomb.damage)
                bomb.hasDealtDamage = True

    def handleBulletHits(self):
        for bullet in list(self.bullets):
            hit = False

            # Feathers herself — same takeDamage/HP pattern as Raccoon in
            # Scene1 (both inherit it from Enemy), just a direct rect check
            # here since there's only the one enemy rather than a group.
            if self.feathers.hp > 0 and bullet.rect.colliderect(self.feathers.rect):
                self.feathers.takeDamage(1)
                bullet.kill()
                continue

            for nest in self.nests:
                if nest.destroyed:
                    continue
                if bullet.rect.colliderect(nest.rect):
                    nest.takeHit()
                    bullet.kill()
                    hit = True
                    break

            if hit:
                continue

            # Bullet-blocking platforms (e.g. the spiky branch) just stop
            # the bullet outright — no hit-tracking, they're not a target.
            # Uses shape-accurate collision (collidesRect), not just the
            # bounding rect, since a rotated platform's rect can be much
            # bigger than its visible sprite.
            for platform in self.platforms:
                if not getattr(platform, "blocksBullets", False):
                    continue
                if platform.collidesRect(bullet.rect):
                    bullet.kill()
                    break

    def handleWallCollisions(self, prevRect):
        for wall in self.walls:
            if not self.player.rect.colliderect(wall.rect):
                continue

            # Use last frame's position to tell which side Prickle approached
            # from, then clamp him back to that side of the wall.
            if prevRect.right <= wall.x:
                self.player.rect.right = wall.x
            elif prevRect.left >= wall.x:
                self.player.rect.left = wall.x

    def draw(self, screen):
        # Anchor the bottom of the background to the bottom of the screen,
        # then shift up by scrollY as Prickle climbs.
        bgY = SCREEN_HEIGHT - self.bgHeight + self.player.scrollY
        screen.blit(self.bg, (0, bgY))

        for platform in self.platforms:
            platform.draw(screen)
        for nest in self.nests:
            nest.draw(screen)

        self.feathers.draw(screen)
        for bomb in self.bombs:
            bomb.draw(screen)

        screen.blit(self.player.image, self.player.rect)
        self.bullets.draw(screen)
        self.player.drawAmmo(screen)
        self.player.drawHP(screen)
        self.feathers.drawHP(screen)