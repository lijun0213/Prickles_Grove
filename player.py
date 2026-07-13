import pygame
from settings import SCREEN_WIDTH

pygame.init()


class Player(pygame.sprite.Sprite):
    def __init__(self, bulletGroup):
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

        self.bulletGroup = bulletGroup

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

        prickleIdleFrames = extractFrames (prickleIdle, 6)
        prickleIdleLFrames = [pygame.transform.flip(f, True, False) for f in prickleIdleFrames]
        prickleWalkRFrames = extractFrames (prickleWalk, 6)
        prickleWalkLFrames = [pygame.transform.flip(f, True, False) for f in prickleWalkRFrames]
        prickleRunRFrames = extractFrames (prickleRun, 6)
        prickleRunLFrames = [pygame.transform.flip(f, True, False) for f in prickleRunRFrames]
        prickleAttackRFrames = extractFrames (prickleAttack, 1)
        prickleAttackLFrames = [pygame.transform.flip(f, True, False) for f in prickleAttackRFrames]

        self.animations = {
            'idle'       : prickleIdleFrames,
            'idle_left'  : prickleIdleLFrames,
            'walk_right' : prickleWalkRFrames,
            'walk_left'  : prickleWalkLFrames,
            'run_right' : prickleRunRFrames,
            'run_left'  : prickleRunLFrames,
            'attack_right': prickleAttackRFrames,
            'attack_left' : prickleAttackLFrames
        }

        self.idleFrames = prickleIdleFrames
        self.idleLeftFrames = prickleIdleLFrames
        self.walkingRightFrames = prickleWalkRFrames
        self.walkingLeftFrames = prickleWalkLFrames
        self.runningRightFrames = prickleRunRFrames
        self.runningLeftFrames = prickleRunLFrames
        self.attackRightFrames = prickleAttackRFrames
        self.attackLeftFrames = prickleAttackLFrames

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

        # Platform state — shared by any scene that passes a `platforms` list
        # into update(). Lets Prickle jump onto elevated obstacles (branches,
        # bridges, etc.), walk along their actual pixel shape, and drop
        # through them with "S", without each scene reimplementing it.
        self.currentPlatform = None
        self.dropThroughPlatform = None
        self.dropThroughTimer = 0
        self.dropThroughFrames = 20  # frames to ignore a platform after dropping through it

        # Prickle's sprite has some transparent padding below his feet, so
        # landing exactly on a platform's pixel surface leaves a visible gap.
        # Sink him down a few px to close it up.
        self.platformLandingOffset = 8

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

        self.handleAmmo()
        self.handleAttack()
        self.animate(keys)

    def handlePlatforms(self, platforms, prevBottom, wasGrounded):
        """Jump-on-top collision against a scene's `platforms` list (see
        obstacles.Platform). Uses each platform's actual pixel shape, not
        its full rectangular bounds."""

        # Rising (jumping) — don't stick to anything overhead.
        if self.velocityY < 0:
            self.currentPlatform = None
            return

        # First, try to stay on the specific platform we were already
        # standing on — this is what lets walking across an uneven/sagging
        # surface (like a rope bridge) feel continuous without needing a
        # fresh "falling from above" every frame.
        if wasGrounded and self.currentPlatform is not None:
            platform = self.currentPlatform
            if self.rect.colliderect(platform.rect):
                surfaceY = platform.topAt(self.rect.centerx)
                if surfaceY is not None:
                    self.rect.bottom = surfaceY + self.platformLandingOffset
                    self.velocityY = 0
                    self.onGround = True
                    return
            # Walked off the platform we were on (past its solid columns,
            # or off its box entirely) — fall through to check for a fresh
            # landing on something else below.
            self.currentPlatform = None

        # Otherwise, only land if genuinely falling onto a platform from
        # above. This also prevents snapping sideways into a platform
        # whenever bounding boxes happen to overlap (e.g. a rotated/scaled
        # platform's box stretching under another one).
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

            if landingFromAbove:
                self.rect.bottom = landY
                self.velocityY = 0
                self.onGround = True
                self.currentPlatform = platform
                return

        self.currentPlatform = None

    def move(self, keys):
        self.isRunning = keys[pygame.K_LSHIFT]
        self.speed = 8 if self.isRunning else 5

        if keys[pygame.K_a]:
            self.rect.x -= self.speed
            self.direction = -1
            self.facingRight = False

        elif keys[pygame.K_d]:
            self.rect.x += self.speed
            self.direction = 1
            self.facingRight = True          

        else:
            self.direction = 0

        # Keep Prickle inside the screen horizontally
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        if keys[pygame.K_SPACE] and self.onGround:
            self.velocityY = -15
            self.onGround = False

        # Apply gravity
        self.velocityY += 1
        self.rect.y += self.velocityY

        if self.rect.bottom >= self.groundY:
            self.rect.bottom = self.groundY
            self.velocityY = 0
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
        ammoX = 20
        ammoY = 80
        spacing = 65

        for i in range(self.maxAmmo):
            if i < self.ammo:
                image = self.ammoFull
            else:
                image = self.ammoEmpty

            screen.blit(image,(ammoX + i * spacing, ammoY))

    def animate(self, keys):
        if self.direction == 1:
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