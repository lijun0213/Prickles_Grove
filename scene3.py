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

        # Feathers — the Scene 3 boss. Flies left/right randomly and hovers
        # a fixed distance above wherever Prickle currently is, so he's
        # always overhead as Prickle climbs toward the nest.
        self.bombs = pygame.sprite.Group()
        self.feathers = Feathers(x=400, y=-350, bombGroup=self.bombs, hp=10, hoverOffset=250, wanderRange=150,
                                  bombIntervalSeconds=1)

        # Golden petal — the actual reward, visible sitting on top of the
        # nest from the start so Prickle can see what he's fighting for.
        # Once the nest is destroyed it drops straight down to the floor
        # (deliberately ignoring whatever branches/bridge it passes on the
        # way, rather than resting on the nearest one — it belongs on the
        # ground), then sits there to be picked up the same way Scene1's map
        # pickup works: get close and press R. Pinned to the floor
        # platform's scrolled position once landed, same landedPlatform/
        # landOffset trick Bomb and dead Feathers use, so it stays put on
        # screen as Prickle climbs back down.
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

        # Scene-level state — mainly so main.py's death/Game-Over interlock
        # (which checks scene.state/scene.deathTimer the same way it does for
        # Scene4) has something to read. Scene3 itself only ever has two
        # states: normal play, and the death sequence once Prickle's HP hits 0.
        self.state = "PLAYING"
        self.deathTimer = 0
        self.deathDuration = 120  # ~2 seconds at 60fps before Game Over shows

        # Spiky branch — touching it doesn't hurt instantly/every frame,
        # just a heart every 2 seconds for as long as Prickle stays in
        # contact with it (rather than a one-shot hit like a bullet, or
        # constant per-frame damage that would drain HP almost instantly).
        self.hazardDamageTimer = 0
        self.hazardDamageInterval = FPS * 2

        # Opening dialogue — same shared textbox component Scene1/Scene4
        # use. Freezes the scene (see the top of update()) while it plays,
        # then hands control back to Prickle once the last line is dismissed.
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

        # Fade-to-black transition into Scene4, triggered the instant the
        # petal is actually picked up (see updatePetal). levelComplete is
        # the same signal Scene1/Scene0 use for their own scene handoffs —
        # main.py watches for it to switch to Scene4 once the fade finishes.
        self.levelComplete = False
        self.fading = False
        self.fadeTimer = 0
        self.fadeDuration = 60  # 1 second at 60fps

    def _showDialogue(self, lines, speaker="prickle", style="center", next=None, onDismiss=None):
        """Open the shared dialogue box, resolving a speaker key into this
        scene's portrait/name. `next` is a convenience for the common case
        (just set self.state once dismissed); pass a custom `onDismiss`
        instead for chaining straight into another dialogue line, like the
        opening back-and-forth below."""
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
        self._showDialogue(["Say less!"], speaker="prickle")

    def _showFeatherDeathTaunt(self):
        # Fires once, right after Feathers dies — see the isDead edge-check
        # in update(). "Say less"->kill her, and now she gets one last word
        # in on her way down.
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
        # One-shot tutorial callout, chained onto the end of the post-death
        # dialogue — no portrait/speaker, just a small corner hint box.
        self._showDialogue(
            ["Climb the trees and destroy the nest"],
            style="callout",
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

        # Platform sticking, walking-along-surface, "S" drop-through, and
        # camera-follow are all handled generically inside Player now — just
        # hand it this scene's platforms each frame.
        self.player.update(keys, platforms=self.platforms)

        self.handleWallCollisions(prevRect)
        self.handleHazardCollisions()

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

        if self.feathers.isDead and not self.feathersDeathDialogueShown:
            self.feathersDeathDialogueShown = True
            self._showFeatherDeathTaunt()

        self.bombs.update(self.platforms)
        self.handleBombHits()

        self.updatePetal(keys)

    def updatePetal(self, keys):
        if self.petalCollected:
            return

        nest = self.nests[0]

        if not nest.destroyed:
            # Still resting visibly on top of the nest — just ride along
            # with it as it scrolls (nest.rect.y is kept in sync with
            # scrollY earlier in update()).
            self.petalRect.center = (nest.rect.centerx, nest.rect.top + self.petalRestOffset)
            return

        if not self.petalFalling and not self.petalLanded:
            # The nest just got destroyed this frame — let go and start
            # falling from wherever it was actually sitting.
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
                # Safety net in case topAt ever misses (shouldn't happen —
                # the floor spans the full screen width).
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
        # Keep Prickle's death animation playing (Player.update already
        # branches on isDeath internally); everything else in the scene
        # freezes so Feathers/bombs don't keep acting on a dead player.
        self.player.update(keys, platforms=self.platforms)

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
            # Not touching it anymore — reset so walking back onto it later
            # starts a fresh 2-second countdown rather than picking up
            # wherever the timer happened to be left off.
            self.hazardDamageTimer = 0

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