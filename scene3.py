import pygame
from settings import *
from player import Player
from obstacles import Platform, Wall, Mushroom, Nest
from enemies import Feathers
from dialogue import Dialogue
import effects

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
            Platform(r"scene3_assets/spiky branch.png", x=285, y=-400, angle=-50, scale = 1, blocksBullets=True, hazard=True),
        ]


        self.walls = [
            Wall(x=635, top=-1000, bottom=SCREEN_HEIGHT),
            Wall(x=80, top=-1000, bottom=290),
        ]

        self.nests = [
            Nest(r"scene3_assets/bird nest.png", x=510, y=-425, maxHits=5),
        ]

        # Feathers
        self.bombs = pygame.sprite.Group()
        self.feathers = Feathers(x=400, y=-350, bombGroup=self.bombs, hp=10, hoverOffset=250, wanderRange=150,
                                  bombIntervalSeconds=1)

        # Golden petal
        self.petalImage = pygame.image.load(r"scene3_assets/golden petal.png").convert_alpha()
        self.petalImage = pygame.transform.scale_by(self.petalImage, 0.1)
        nest = self.nests[0]
        self.petalRestOffset = 20  # how far below the nest's top edge it sits, nestled into the bowl
        self.petalRect = self.petalImage.get_rect(center=(nest.rect.centerx, nest.rect.top + self.petalRestOffset))
        self.petalFalling = False
        self.petalLanded = False
        self.petalCollected = False
        self.nearPetal = False
        self.petalFallSpeed = 6
        self.petalLandOffset = 0

        # Scene-level state 
        self.state = "PLAYING"
        self.deathTimer = 0
        self.deathDuration = 120  # 2 seconds before Game Over shows

        # Spiky branch — decrese a heart every 2 seconds when prickle touch it
        self.hazardDamageTimer = 0
        self.hazardDamageInterval = FPS * 2

        # Opening dialogue 
        self.portraits = {
            "prickle": pygame.transform.scale_by(self.player.idleFrames[0], 1.3),
            "feather": pygame.transform.scale_by(self.feathers.flyRFrames[0], 1.0),
        }
        self.speakerNames = {
            "prickle": "Prickle",
            "feather": "Feather",
        }
        self.dialogue = Dialogue()
        self._showDialogue(
            ["Hey! Where is my Golden Petal"],
            speaker="prickle",
            onDismiss=self._showFeatherTaunt,
        )
        self.feathersDeathDialogueShown = False
        self.spikyBranchDialogueShown = False

        # Battle music 
        pygame.mixer.music.load(r"scene3_assets/Backwater, Kamoking - Battle BGM.mp3")
        pygame.mixer.music.set_volume(0.2)

        # Fade-to-black transition into Scene4
        self.levelComplete = False
        self.fading = False
        self.fadeTimer = 0
        self.fadeDuration = 60  # 1 second at 60fps

    def _showDialogue(self, lines, speaker="prickle", style="center", next=None, onDismiss=None):
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

    def _showFeatherTaunt(self):
        self._showDialogue(
            ["Haha, You have to kill me to find out!"],
            speaker="feather",
            onDismiss=self._showPrickleReply,
        )

    def _showPrickleReply(self):
        self._showDialogue(["Say less!"], speaker="prickle", onDismiss=self._endOpeningDialogue)


#Dialogues after Feather dead
    def _endOpeningDialogue(self):
        self.player.controllable = True
        pygame.mixer.music.play(loops=-1)

    def _showFeatherDeathTaunt(self):
        self._showDialogue(
            ["Tell me where is it!"],
            speaker="prickle",
            onDismiss=self._showFeatherDeathReply,
        )

    def _showFeatherDeathReply(self):
        self._showDialogue(
            ["You will never reach it!", "My nest is guarded by a poisonous branch at the top of the tree! "],
            speaker="feather",
            onDismiss=self._showClimbTip,
        )

    def _showClimbTip(self):
        self._showDialogue(
            ["Climb the trees and destroy the nest"],
            style="callout",
        )

    def _showSpikyBranchTip(self):
        self._showDialogue(
            ["Ugh I can't hit the nest... I need to hit it from above"],
            speaker="prickle",
        )

    def update(self):
        keys = pygame.key.get_pressed()

        if self.dialogue.active:
            self.dialogue.update(keys)
            return

        if self.fading:
            self.updateFade()
            return

        if self.player.hp <= 0 and self.state != "DEATH":
            self.state = "DEATH"
            self.deathTimer = self.deathDuration

        if self.state == "DEATH":
            self.updateDeathSequence(keys)
            return

        prevRect = self.player.rect.copy()

        # Platform sticking, walking-along-surface
        self.player.update(keys, platforms=self.platforms)

        self.handleWallCollisions(prevRect)
        self.handleHazardCollisions()

        # Keep platforms/walls/nests anchored to the background art for when camera moves vertically
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

        if self.feathers.isDead and not self.feathersDeathDialogueShown:
            self.feathersDeathDialogueShown = True
            pygame.mixer.music.stop()
            self._showFeatherDeathTaunt()

        self.bombs.update(self.platforms)
        self.handleBombHits()

        self.updatePetal(keys)

    def updatePetal(self, keys):
        if self.petalCollected:
            return

        nest = self.nests[0]

        if not nest.destroyed:
            # golden petal still resting on top of the nest
            self.petalRect.center = (nest.rect.centerx, nest.rect.top + self.petalRestOffset)
            return

        if not self.petalFalling and not self.petalLanded:
            # nest destroyed, petal starts falling
            self.petalFalling = True

        floor = self.platforms[0]  # the invisible floor strip, see __init__

        if self.petalFalling:
            prevBottom = self.petalRect.bottom
            self.petalRect.y += self.petalFallSpeed

            surfaceY = floor.topAt(self.petalRect.centerx)
            if surfaceY is not None and prevBottom <= surfaceY and self.petalRect.bottom >= surfaceY:
                self.petalRect.bottom = surfaceY
                self.petalFalling = False
                self.petalLanded = True
                self.petalLandOffset = self.petalRect.bottom - floor.rect.y
            elif self.petalRect.top > SCREEN_HEIGHT + 500:
                self.petalRect.bottom = SCREEN_HEIGHT
                self.petalFalling = False
                self.petalLanded = True
                self.petalLandOffset = self.petalRect.bottom - floor.rect.y
            return

        if self.petalLanded:
            self.petalRect.bottom = floor.rect.y + self.petalLandOffset

            self.nearPetal = False
            if self.player.rect.colliderect(self.petalRect.inflate(40, 40)):
                distance = abs(self.player.rect.centerx - self.petalRect.centerx)
                if distance < 60:
                    self.nearPetal = True
                    if keys[pygame.K_r]:
                        self.petalCollected = True
                        self.player.pickupItem_sound.play()
                        self.fading = True

    def updateFade(self):
        self.fadeTimer += 1
        if self.fadeTimer >= self.fadeDuration:
            self.levelComplete = True

    def updateDeathSequence(self, keys):
        if self.deathTimer > 0:
            self.deathTimer -= 1
        # Keep Prickle's death animation playing 
        self.player.update(keys, platforms=self.platforms)

    def handleBombHits(self):
        for bomb in list(self.bombs):
            # Only the explosion hurts Prickle
            if not bomb.exploded or bomb.hasDealtDamage:
                continue
            if bomb.rect.colliderect(self.player.rect):
                self.player.takeDamage(bomb.damage)
                bomb.hasDealtDamage = True

    def handleBulletHits(self):
        for bullet in list(self.bullets):
            hit = False

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

            # Bullet-blocking platforms 
            for platform in self.platforms:
                if not getattr(platform, "blocksBullets", False):
                    continue
                if platform.collidesRect(bullet.rect):
                    bullet.kill()
                    # show tip for prickle to use bouncy mushroom and get above
                    if getattr(platform, "hazard", False) and not self.spikyBranchDialogueShown:
                        self.spikyBranchDialogueShown = True
                        self._showSpikyBranchTip()
                    break


    # for spiky branch to deal damage
    def handleHazardCollisions(self):
        if self.hazardDamageTimer > 0:
            self.hazardDamageTimer -= 1

        touchingHazard = any(
            getattr(platform, "hazard", False) and platform.collidesRect(self.player.rect)
            for platform in self.platforms
        )

        if touchingHazard:
            if self.hazardDamageTimer <= 0:
                self.player.takeDamage(1)
                self.hazardDamageTimer = self.hazardDamageInterval
        else:
            self.hazardDamageTimer = 0

    def handleWallCollisions(self, prevRect):
        for wall in self.walls:
            if not self.player.rect.colliderect(wall.rect):
                continue
            if prevRect.right <= wall.x:
                self.player.rect.right = wall.x
            elif prevRect.left >= wall.x:
                self.player.rect.left = wall.x

    def draw(self, screen):
        bgY = SCREEN_HEIGHT - self.bgHeight + self.player.scrollY
        screen.blit(self.bg, (0, bgY))

        for platform in self.platforms:
            platform.draw(screen)
        for nest in self.nests:
            nest.draw(screen)

        self.feathers.draw(screen)
        for bomb in self.bombs:
            bomb.draw(screen)

        if not self.petalCollected:
            effects.drawPulseGlow(screen, self.petalRect.center)
            screen.blit(self.petalImage, self.petalRect)
            if self.nearPetal:
                font = pygame.font.SysFont("Arial", 18)
                text = font.render("Press R to pick up", True, YELLOW)
                screen.blit(text, (self.petalRect.x - 20, self.petalRect.y - 30))

        screen.blit(self.player.image, self.player.rect)
        self.bullets.draw(screen)
        self.player.drawAmmo(screen)
        self.player.drawHP(screen)
        self.feathers.drawHP(screen)

        self.dialogue.draw(screen)

        if self.fading:
            alpha = int(255 * min(1, self.fadeTimer / self.fadeDuration))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, alpha))
            screen.blit(overlay, (0, 0))