import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

pygame.init()


class Player(pygame.sprite.Sprite):
    def __init__(self, bulletGroup, bgWidth, bgHeight=None):
        super().__init__()

        # Prickle sprite sheet
        prickleIdle = pygame.image.load(r"assets/prickle_idle.png").convert_alpha()
        prickleIdle = pygame.transform.scale_by(prickleIdle, 1.2)
        prickleWalk = pygame.image.load(r"assets/prickle_walk.png").convert_alpha()
        prickleWalk = pygame.transform.scale_by(prickleWalk, 1.2)
        prickleRun = pygame.image.load(r"assets/prickle_run.png").convert_alpha()
        prickleRun = pygame.transform.scale_by(prickleRun, 1.2)
        prickleAttack= pygame.image.load(r"assets/prickle_attack.png").convert_alpha()
        prickleAttack = pygame.transform.scale_by(prickleAttack, 1.2)
        prickleHurt= pygame.image.load(r"assets/prickle_hurt.png").convert_alpha()
        prickleHurt = pygame.transform.scale_by(prickleHurt, 1.2)

        self.bulletGroup = bulletGroup

        self.bgWidth = bgWidth

        # bgHeight is optional — scenes with a background no taller than the
        # screen (no vertical scrolling) can just omit it. When it IS taller,
        # this is what lets the camera-follow below know how much room there
        # is to scroll into.
        self.bgHeight = bgHeight if bgHeight is not None else SCREEN_HEIGHT

        self.player_hpFull = pygame.image.load(r"assets/player_hpFull.png").convert_alpha()
        self.player_hpFull = pygame.transform.scale_by(self.player_hpFull, 0.35)
        self.player_hpEmpty = pygame.image.load(r"assets/player_hpEmpty.png").convert_alpha()
        self.player_hpEmpty = pygame.transform.scale_by(self.player_hpEmpty, 0.35)

        self.ammoFull = pygame.image.load(r"assets/ammo_full.png").convert_alpha()
        self.ammoFull = pygame.transform.scale_by(self.ammoFull, 0.6)
        self.ammoEmpty = pygame.image.load(r"assets/ammo_empty.png").convert_alpha()
        self.ammoEmpty = pygame.transform.scale_by(self.ammoEmpty, 0.6)

        # Extract frames
        def extractFrames(sheet, numFrames):
            frames = []

            frameWidth = sheet.get_width() // numFrames
            frameHeight = sheet.get_height()

            for i in range(numFrames):
                frame = sheet.subsurface(pygame.Rect(i * frameWidth, 0, frameWidth, frameHeight))
                frames.append(frame)
            return frames

        prickleIdleRFrames = extractFrames (prickleIdle, 6)
        prickleIdleLFrames = [pygame.transform.flip(f, True, False) for f in prickleIdleRFrames]
        prickleWalkRFrames = extractFrames (prickleWalk, 6)
        prickleWalkLFrames = [pygame.transform.flip(f, True, False) for f in prickleWalkRFrames]
        prickleRunRFrames = extractFrames (prickleRun, 6)
        prickleRunLFrames = [pygame.transform.flip(f, True, False) for f in prickleRunRFrames]
        prickleAttackRFrames = extractFrames (prickleAttack, 1)
        prickleAttackLFrames = [pygame.transform.flip(f, True, False) for f in prickleAttackRFrames]
        prickleHurtRFrames = extractFrames (prickleHurt, 3)
        prickleHurtLFrames = [pygame.transform.flip(f, True, False) for f in prickleHurtRFrames]

        self.animations = {
            'idle'       : prickleIdleRFrames,
            'idle_left'  : prickleIdleLFrames,
            'walk_right' : prickleWalkRFrames,
            'walk_left'  : prickleWalkLFrames,
            'run_right' : prickleRunRFrames,
            'run_left'  : prickleRunLFrames,
            'attack_right': prickleAttackRFrames,
            'attack_left' : prickleAttackLFrames,
            'hurt_right': prickleHurtRFrames,
            'hurt_left' : prickleHurtLFrames
        }

        self.idleFrames = prickleIdleRFrames
        self.idleLeftFrames = prickleIdleLFrames
        self.walkingRightFrames = prickleWalkRFrames
        self.walkingLeftFrames = prickleWalkLFrames
        self.runningRightFrames = prickleRunRFrames
        self.runningLeftFrames = prickleRunLFrames
        self.attackRightFrames = prickleAttackRFrames
        self.attackLeftFrames = prickleAttackLFrames
        self.hurtRightFrames = prickleHurtRFrames
        self.hurtLeftFrames = prickleHurtLFrames
        

        # animation
        self.currentFrames = self.idleFrames
        self.animIndex = 0 
        self.animTimer = 0
        self.animSpeed = 5

        self.image = self.idleFrames[0]
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.groundY = 300
        self.rect.bottom = self.groundY
        self.imageOffsetY = 0

        self.velocityY = 0

        # Passive horizontal drift — normally 0, since A/D directly set
        # position every frame. Only used for a diagonal bounce-pad launch
        # (see handlePlatforms): A/D still override it instantly, and it's
        # cleared on any normal landing so the drift only lasts the one arc.
        self.velocityX = 0

        self.onGround = True
        self.direction = 0
        self.facingRight = True

        self.isRunning = False
        self.speed = 5

        self.isAttacking = False
        self.attackTimer = 0
        self.attackCooldown = 0
        self.attackCooldownMax = 15

        self.maxAmmo = 3
        self.ammo = self.maxAmmo
        self.reloadTimer = 0
        self.reloadRate = 120
        self.mousePressed = False

        self.currentPlatform = None
        self.dropThroughPlatform = None
        self.dropThroughTimer = 0
        self.dropThroughFrames = 20  # frames to ignore a platform after dropping through it
        self.platformLandingOffset = 8

        self.maxHP = 3
        self.hp = self.maxHP

        self.isHurt = False
        self.hurtTimer = 0
        self.hurtDuration = 15

        # Vertical camera-follow (mirrors how bgWidth bounds horizontal
        # movement). scrollY is how far the world has scrolled to keep
        # Prickle on screen; maxScrollY is how far it CAN scroll before
        # running out of background. cameraFollowY is the screen-y that,
        # once crossed, starts pulling the camera up with him — it defaults
        # to "never" (SCREEN_HEIGHT) since most scenes don't scroll; a scene
        # that wants this can set self.player.cameraFollowY after construction,
        # same way scenes already set self.player.groundY.
        self.scrollY = 0
        self.maxScrollY = max(0, self.bgHeight - SCREEN_HEIGHT)
        self.cameraFollowY = SCREEN_HEIGHT

    def update(self, keys, platforms=None):
        prevBottom = self.rect.bottom
        wasGrounded = self.onGround

        # Press S while standing on a platform to drop through it.
        if platforms and keys[pygame.K_s] and wasGrounded and self.currentPlatform is not None:
            self.dropThroughPlatform = self.currentPlatform
            self.dropThroughTimer = self.dropThroughFrames
            self.currentPlatform = None

        self.move(keys)

        if platforms:
            self.handlePlatforms(platforms, prevBottom, wasGrounded)

        if self.dropThroughTimer > 0:
            self.dropThroughTimer -= 1
            if self.dropThroughTimer == 0:
                self.dropThroughPlatform = None

        self.updateCamera()

        self.handleAmmo()
        self.handleAttack()

        if self.isHurt:
            self.hurtTimer -= 1
            if self.hurtTimer <= 0:
                self.isHurt = False

        self.animate(keys)

    def updateCamera(self):
        # How far above the follow-line Prickle is trying to be (positive =
        # above it). Feeding this into scrollY and pinning him back at the
        # line is what makes the camera "follow" him: extra upward movement
        # gets absorbed into scrolling the world instead of moving him
        # further up the screen. No-op whenever maxScrollY is 0 (the default,
        # for scenes that never passed a bgHeight taller than the screen).
        overshoot = self.cameraFollowY - self.rect.top
        self.scrollY = max(0, min(self.maxScrollY, self.scrollY + overshoot))

        if self.scrollY > 0:
            self.rect.top = self.cameraFollowY

    def handlePlatforms(self, platforms, prevBottom, wasGrounded):
        if self.velocityY < 0:
            self.currentPlatform = None
            return

        # If we were grounded last frame, check if we're still on the same platform.
        if wasGrounded and self.currentPlatform is not None:
            platform = self.currentPlatform
            if self.rect.colliderect(platform.rect):
                surfaceY = platform.topAt(self.rect.centerx)
                if surfaceY is not None:
                    self.rect.bottom = surfaceY + self.platformLandingOffset
                    self.velocityY = 0
                    self.velocityX = 0
                    self.onGround = True
                    return
            self.currentPlatform = None

        # Check for landing on any platform. Platform bounding boxes can
        # overlap (a rotated/scaled branch's box can stretch across other
        # obstacles), so rather than taking whichever platform happens to be
        # first in the list, pick whichever valid landing is HIGHEST — the
        # surface Prickle would actually hit first while falling.
        bestPlatform = None
        bestLandY = None

        for platform in platforms:
            if platform is self.dropThroughPlatform:
                continue

            if not self.rect.colliderect(platform.rect):
                continue

            surfaceY = platform.topAt(self.rect.centerx)
            if surfaceY is None:
                continue

            landY = surfaceY + self.platformLandingOffset
            landingFromAbove = prevBottom <= landY and self.rect.bottom >= landY

            if landingFromAbove and (bestLandY is None or landY < bestLandY):
                bestPlatform = platform
                bestLandY = landY

        if bestPlatform is not None:
            bounceVY = getattr(bestPlatform, "bounceVY", None)

            if bounceVY is not None:
                # Bounce pad (e.g. Mushroom) — launch back up (and sideways,
                # if it's rotated) instead of resting on it, and play its
                # squash/release animation.
                self.rect.bottom = bestLandY
                self.velocityY = bounceVY
                self.velocityX = getattr(bestPlatform, "bounceVX", 0)
                self.onGround = False
                self.currentPlatform = None
                if hasattr(bestPlatform, "trigger"):
                    bestPlatform.trigger()
            else:
                self.rect.bottom = bestLandY
                self.velocityY = 0
                self.velocityX = 0
                self.onGround = True
                self.currentPlatform = bestPlatform

            return

        self.currentPlatform = None

    def move(self, keys):
        self.isRunning = keys[pygame.K_LSHIFT]
        self.speed = 8 if self.isRunning else 5

        if keys[pygame.K_a]:
            self.rect.x -= self.speed
            self.velocityX = 0  # manual input always overrides bounce drift
            self.direction = -1
            self.facingRight = False

        elif keys[pygame.K_d]:
            self.rect.x += self.speed
            self.velocityX = 0
            self.direction = 1
            self.facingRight = True

        else:
            self.direction = 0
            if self.velocityX:
                self.rect.x += self.velocityX

        # Keep Prickle inside the screen horizontally
        if self.rect.left < 0:
            self.rect.left = 0
            self.velocityX = 0
        elif self.rect.right > self.bgWidth:
            self.rect.right = self.bgWidth
            self.velocityX = 0

        if keys[pygame.K_SPACE] and self.onGround:
            self.velocityY = -15
            self.onGround = False

        # Apply gravity
        self.velocityY += 1
        self.rect.y += self.velocityY

        if self.rect.bottom >= self.groundY:
            self.rect.bottom = self.groundY
            self.velocityY = 0
            self.velocityX = 0
            self.onGround = True
        else:
            self.onGround = False

    def handleAttack(self):
        mouse_buttons = pygame.mouse.get_pressed()
        mousePressed = mouse_buttons[0] # left click

        if self.attackCooldown > 0:
            self.attackCooldown -= 1

        justClicked = mousePressed and not self.mousePressed
        fire = justClicked and self.attackCooldown == 0 and self.ammo > 0

        if fire:
            self.shoot()
            self.ammo -= 1
            self.attackCooldown = self.attackCooldownMax
            self.attackTimer = 10

        self.mousePressed = mousePressed

        if self.attackTimer > 0:
            self.attackTimer -= 1
            self.isAttacking = True
        else:
            self.isAttacking = False

    def handleAmmo(self):
        if self.ammo < self.maxAmmo:
            self.reloadTimer += 1
            if self.reloadTimer >= self.reloadRate:
                self.ammo += 1
                self.reloadTimer = 0
        else:
            self.reloadTimer = 0

    def shoot(self):
        direction = 1 if self.facingRight else -1
        bulletX = self.rect.centerx + (direction * self.rect.width // 2)
        bulletY = self.rect.centery
        bullet = Bullet(bulletX, bulletY, direction)
        self.bulletGroup.add(bullet)

    def drawAmmo(self, screen):
        ammoX = 30
        ammoY = 70
        spacing = 65

        for i in range(self.maxAmmo):
            if i < self.ammo:
                image = self.ammoFull
            else:
                image = self.ammoEmpty

            screen.blit(image,(ammoX + i * spacing, ammoY))

    def drawHP(self,screen):
        hpX = 20
        hpY = 10
        spacing = 65

        for i in range(self.maxHP):
            if i < self.hp:
                image = self.player_hpFull
            else:
                image = self.player_hpEmpty

            screen.blit(image, (hpX + i * spacing, hpY))
    
    def takeDamage(self, damage):
        self.hp -= damage

        if self.hp <= 0:
            self.hp = 0
            print("Player Dead")

    def animate(self, keys):
        if self.direction == 1:
            newFrames = self.runningRightFrames if self.isRunning else self.walkingRightFrames

        elif self.direction == -1:
            newFrames = self.runningLeftFrames if self.isRunning else self.walkingLeftFrames

        else:
            newFrames = self.idleFrames if self.facingRight else self.idleLeftFrames

        if self.isHurt:
            newFrames = self.hurtRightFrames if self.facingRight else self.hurtLeftFrames
        elif self.direction == 1:
            newFrames = self.runningRightFrames if self.isRunning else self.walkingRightFrames
        elif self.direction == -1:
            newFrames = self.runningLeftFrames if self.isRunning else self.walkingLeftFrames
        else:
            newFrames = self.idleFrames if self.facingRight else self.idleLeftFrames
 
        if self.isAttacking:
            newFrames = self.attackRightFrames if self.facingRight else self.attackLeftFrames

        if newFrames != self.currentFrames:
            self.currentFrames = newFrames
            self.animIndex = 0
            self.animTimer = 0

        self.animTimer += 1

        if self.animTimer >= self.animSpeed:
            self.animTimer = 0
            self.animIndex = (self.animIndex + 1) % len(self.currentFrames)

        self.image = self.currentFrames[self.animIndex]

        old_midbottom = self.rect.midbottom

        self.rect = self.image.get_rect()

        self.rect.midbottom = old_midbottom

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        bullet = pygame.image.load(r"assets/bullet.png").convert_alpha()
        bullet = pygame.transform.scale_by(bullet, 1.2)

        if direction == -1:
            bullet = pygame.transform.flip(bullet, True, False)

        self.speed = 10
        self.image = bullet
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction
        self.life = 120

    def update(self):
        self.rect.x += self.speed * self.direction
        self.life -= 1
        if self.life <= 0:
            self.kill()

    