import pygame

pygame.init()


class Player(pygame.sprite.Sprite):
    def __init__(self):
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
        self.animSpeed = 12

        self.image = self.idleFrames[0]
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.rect.y = 300        
        self.groundY = 300
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

        self.maxAmmo = 6
        self.ammo = self.maxAmmo
        self.reloadTimer = 0
        self.reloadRate = 120
        self.mousePressed = False

    def update(self, keys):
        self.move(keys) 
        self.animate(keys)

    def move(self, keys):
        self.isRunning = keys[pygame.K_LSHIFT]
        self.speed = 8 if self.isRunning else 5

        mouse_buttons = pygame.mouse.get_pressed()
        self.attack = mouse_buttons[0] # left click

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

    def animate(self, keys):
        if self.direction == 1:
            newFrames = self.runningRightFrames if self.isRunning else self.walkingRightFrames

        elif self.direction == -1:
            newFrames = self.runningLeftFrames if self.isRunning else self.walkingLeftFrames

        else:
            newFrames = self.idleFrames if self.facingRight else self.idleLeftFrames

        if self.attack:
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
    def __int__(self, x, y, direction):
        super.__init__(self)
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