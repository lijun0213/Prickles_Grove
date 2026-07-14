import pygame
import random
from settings import *

pygame.init()

class Enemy(pygame.sprite.Sprite):

    def __init__(self, x, y, hp):
        super().__init__()

        self.rect = None

        self.maxHP = hp
        self.hp = hp

        self.enemy_hpFull = pygame.image.load(r"assets/enemy_hpFull.png").convert_alpha()
        self.enemy_hpFull = pygame.transform.scale_by(self.enemy_hpFull, 4.5)
        self.enemy_hpEmpty = pygame.image.load(r"assets/enemy_hpEmpty.png").convert_alpha()
        self.enemy_hpEmpty = pygame.transform.scale_by(self.enemy_hpEmpty, 4.5)

    def takeDamage(self, damage):

        self.hp -= damage

        if self.hp <= 0:
            self.hp = 0
            self.kill()

    def drawHP(self, screen):
        hpX = 590
        hpY = 10
        spacingX = 65
        spacingY = 50
        perRow = 3

        for i in range(self.maxHP):

            row = i // perRow
            col = i % perRow

            x = hpX + col * spacingX
            y = hpY + row * spacingY

            if i < self.hp:
                image = self.enemy_hpFull
            else:
                image = self.enemy_hpEmpty

            screen.blit(image, (x, y))

    
class Wasp(Enemy):

    def __init__(self, x, y):
        super().__init__(x, y, 9)

        # Enemy sprite
        waspIdle = pygame.image.load(r"scene4_assets/wasp_idle.png").convert_alpha()
        waspIdle = pygame.transform.scale_by(waspIdle, 1.2)
        waspAttack = pygame.image.load(r"scene4_assets/wasp_attack.png").convert_alpha()
        waspAttack = pygame.transform.scale_by(waspAttack, 1.2)
        waspHurt = pygame.image.load(r"scene4_assets/wasp_hurt.png").convert_alpha()
        waspHurt = pygame.transform.scale_by(waspHurt, 1.2)
        
        # Animation frames
        def extractFrames(sheet, numFrames):
            frames = []

            frameWidth = sheet.get_width() // numFrames
            frameHeight = sheet.get_height()

            for i in range(numFrames):
                frame = sheet.subsurface(
                    pygame.Rect(i * frameWidth, 0, frameWidth, frameHeight)
                )
                frames.append(frame)

            return frames

        self.idleRFrames = extractFrames(waspIdle, 4)
        self.idleLFrames = [pygame.transform.flip(f, True, False) for f in self.idleRFrames]
        self.attackRFrames = extractFrames(waspAttack, 7)
        self.attackLFrames = [pygame.transform.flip(f, True, False) for f in self.attackRFrames]
        self.hurtRFrames = extractFrames(waspHurt, 3)
        self.hurtLFrames = [pygame.transform.flip(f, True, False) for f in self.hurtRFrames]

        # Animation
        self.currentFrames = self.idleRFrames
        self.animIndex = 0
        self.animTimer = 0
        self.animSpeed = 10

        self.image = self.currentFrames[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = y

        # Direction
        self.facingRight = False

        self.alive = True

        # AI
        self.speed = 2
        self.wanderTarget = self.pickWanderTarget()
        self.wanderTimer = 0
        self.wanderChangeRate = 90  # frames before picking a new random spot even if not reached
 
        self.detectRange = 250
        self.attackRange = 60
        self.isAttacking = False
        self.attackTimer = 0        
        self.attackCooldownMax = 90   # ~1.5s between attacks
        self.attackCooldown = 0
        self.attackDamage = 1

        self.isHurt = False
        self.hurtTimer = 0
        self.hurtDuration = 15 
            
    def pickWanderTarget(self):
        margin = 60
        x = random.randint(margin, SCREEN_WIDTH - margin)
        y = random.randint(margin, SCREEN_HEIGHT - margin)
        return (x, y)

    def wander(self):
        targetX, targetY = self.wanderTarget
        dx = targetX - self.rect.centerx
        dy = targetY - self.rect.centery
        distance = max((dx ** 2 + dy ** 2) ** 0.5, 1)

        self.rect.x += (dx / distance) * self.speed
        self.rect.y += (dy / distance) * self.speed
        self.facingRight = dx > 0

        self.wanderTimer += 1
        reachedTarget = distance < 10
        if reachedTarget or self.wanderTimer >= self.wanderChangeRate:
            self.wanderTarget = self.pickWanderTarget()
            self.wanderTimer = 0

    def update(self, player):
        if self.hp <= 0:
            return

        if self.attackCooldown > 0:
            self.attackCooldown -= 1

        if self.isHurt:
            self.hurtTimer -= 1
            if self.hurtTimer <= 0:
                self.isHurt = False
        else:
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance <= self.detectRange:

                if distance <= self.attackRange:
                    self.onTouchPlayer(player)

                else:
                    self.chase(player, dx, dy, distance)

            else:
                self.wander()

        if self.isAttacking:
            self.attackTimer -= 1
            if self.attackTimer <= 0:
                self.isAttacking = False

        self.animate()

    def chase(self, player, dx, dy, distance):
        distance = max(distance, 1)
        self.rect.x += (dx / distance) * self.speed
        self.rect.y += (dy / distance) * self.speed
        self.facingRight = dx > 0

    def onTouchPlayer(self, player):
        if self.attackCooldown == 0 and not self.isHurt:
            self.isAttacking = True
            self.attackTimer = len(self.attackRFrames) * self.animSpeed
            player.takeDamage(self.attackDamage)
            self.attackCooldown = self.attackCooldownMax
    
    def animate(self):
        if self.isHurt:
            newFrames = self.hurtRFrames if self.facingRight else self.hurtLFrames
        elif self.isAttacking:
            newFrames = self.attackRFrames if self.facingRight else self.attackLFrames
        else:
            newFrames = self.idleRFrames if self.facingRight else self.idleLFrames

        if newFrames != self.currentFrames:
            self.currentFrames = newFrames
            self.animIndex = 0
            self.animTimer = 0

        self.animTimer += 1

        if self.animTimer >= self.animSpeed:
            self.animTimer = 0
            self.animIndex = (self.animIndex + 1) % len(self.currentFrames)

        self.image = self.currentFrames[self.animIndex]

        oldMidBottom = self.rect.midbottom

        self.rect = self.image.get_rect()

        self.rect.midbottom = oldMidBottom

class Raccoon(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 3)

        raccoonIdle = pygame.image.load(r"scene1_assets/raccoon_idle.png").convert_alpha()
        raccoonIdle = pygame.transform.scale_by(raccoonIdle, 1.5)
        raccoonWalk = pygame.image.load(r"scene1_assets/raccoon_walk.png").convert_alpha()
        raccoonWalk = pygame.transform.scale_by(raccoonWalk, 1.5)
        raccoonHurt = pygame.image.load(r"scene1_assets/raccoon_hurt.png").convert_alpha()
        raccoonHurt = pygame.transform.scale_by(raccoonHurt, 1.5)
        raccoonDeath = pygame.image.load(r"scene1_assets/raccoon_death.png").convert_alpha()
        raccoonDeath = pygame.transform.scale_by(raccoonDeath, 1.5)

        # Extract frames
        def extractFrames(sheet, numFrames):
            frames = []
            frameWidth = sheet.get_width() // numFrames
            frameHeight = sheet.get_height()
            for i in range(numFrames):
                frame = sheet.subsurface(pygame.Rect(i * frameWidth, 0, frameWidth, frameHeight))
                frames.append(frame)
            return frames
        
        self.idleRFrames = extractFrames (raccoonIdle, 5)
        self.idleLFrames = [pygame.transform.flip(f, True, False) for f in self.idleRFrames]
        self.walkRFrames = extractFrames (raccoonWalk, 5)
        self.walkLFrames = [pygame.transform.flip(f, True, False) for f in self.walkRFrames]
        self.hurtRFrames = extractFrames (raccoonHurt, 3)
        self.hurtLFrames = [pygame.transform.flip(f, True, False) for f in self.hurtRFrames]
        self.deathRFrames = extractFrames (raccoonDeath, 1)
        self.deathLFrames = [pygame.transform.flip(f, True, False) for f in self.deathRFrames]
        
        # Animation
        self.currentFrames = self.idleRFrames
        self.animIndex = 0
        self.animTimer = 0
        self.animSpeed = 8

        self.image = self.currentFrames[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = y

        self.facingRight = True

        # Ground / platform following — the scene sets these two after
        # construction (Scene1 does `self.raccoon.platforms = self.platforms`
        # and `self.raccoon.bgWidth = self.bgWidth`), the same way Player
        # gets its platforms passed into update().
        self.groundY = 490
        self.platforms = []
        self.bgWidth = None

        self.normalSpeed = 1.5
        self.escapeSpeed = 3.5

        # Jump physics — same shape of logic as Player's gravity/landing code,
        # so Nugget can land on chairs/table/bed like Prickle does.
        self.velocityY = 0
        self.gravity = 1
        self.jumpPower = -14
        self.onGround = True
        self.currentPlatform = None
        self.jumpChance = 0.02  # per-frame odds of a hop while fleeing, roughly once every 1-2s
        self.idleJumpChance = 0.015  # smaller, nervier hop while just standing on the table

        # Random run direction while being chased
        self.runDirection = random.choice([-1, 1])
        self.runDirTimer = 0
        self.runDirChangeRate = random.randint(40, 90)

        self.isHurt = False
        self.hurtTimer = 0
        self.hurtDuration = 10

        self.active = False  # stays standing still on the table until this flips True

        # Dying state — plays deathRFrames/deathLFrames before removal,
        # instead of vanishing the instant HP hits 0.
        self.isDead = False
        self.deathTimer = 0
        self.deathDuration = 30  # frames the death animation holds before kill()

    def activate(self):
        # Called once the player gets close enough to trigger the chase —
        # Nugget stops idling and starts randomly running/jumping in panic.
        self.active = True

    def takeDamage(self, damage):
        if self.isDead:
            return

        self.hp -= damage
        self.isHurt = True
        self.hurtTimer = self.hurtDuration

        if self.hp <= 0:
            self.hp = 0
            self.isDead = True
            self.deathTimer = 60
            self.currentFrames = self.deathRFrames
            self.animIndex = 0

    def update(self, player):
        if self.isDead:
            self.animate()
            return

        if self.isHurt:
            self.hurtTimer -= 1
            if self.hurtTimer <= 0:
                self.isHurt = False

        if self.active:
            self.runAndJump()
        # else: stays put on the table, just idles in place

        self.animate()

    def runAndJump(self):
        # Pick a new random direction every so often, so movement while
        # fleeing looks panicked rather than a straight line.
        self.runDirTimer += 1
        if self.runDirTimer >= self.runDirChangeRate:
            self.runDirection = random.choice([-1, 1])
            self.runDirTimer = 0
            self.runDirChangeRate = random.randint(40, 90)

        self.rect.x += self.runDirection * self.escapeSpeed
        self.facingRight = self.runDirection > 0

        if self.bgWidth:
            if self.rect.left < 0:
                self.rect.left = 0
                self.runDirection = 1
            elif self.rect.right > self.bgWidth:
                self.rect.right = self.bgWidth
                self.runDirection = -1

        if self.onGround and random.random() < self.jumpChance:
            self.velocityY = self.jumpPower
            self.onGround = False
            self.currentPlatform = None

        self.applyGravityAndPlatforms()

    def applyGravityAndPlatforms(self):
        # Mirrors Player.handlePlatforms: land on the same platform we were
        # already standing on if possible, otherwise check for a fresh
        # landing, and fall back to the room's groundY floor.
        prevBottom = self.rect.bottom
        wasGrounded = self.onGround

        self.velocityY += self.gravity
        self.rect.y += self.velocityY
        self.onGround = False

        if self.velocityY >= 0:
            if wasGrounded and self.currentPlatform is not None:
                platform = self.currentPlatform
                if self.rect.colliderect(platform.rect):
                    surfaceY = platform.topAt(self.rect.centerx)
                    if surfaceY is not None:
                        self.rect.bottom = surfaceY + 8
                        self.velocityY = 0
                        self.onGround = True
                        return
                self.currentPlatform = None

            for platform in self.platforms:
                if not self.rect.colliderect(platform.rect):
                    continue
                surfaceY = platform.topAt(self.rect.centerx)
                if surfaceY is None:
                    continue
                landY = surfaceY + 8
                if prevBottom <= landY and self.rect.bottom >= landY:
                    self.rect.bottom = landY
                    self.velocityY = 0
                    self.onGround = True
                    self.currentPlatform = platform
                    return

        if self.rect.bottom >= self.groundY:
            self.rect.bottom = self.groundY
            self.velocityY = 0
            self.onGround = True
            self.currentPlatform = None

    def animate(self):
        if self.isDead:
            newFrames = self.deathRFrames if self.facingRight else self.deathLFrames
        elif self.isHurt:
            newFrames = self.hurtRFrames if self.facingRight else self.hurtLFrames
        elif self.active:
            newFrames = self.walkRFrames if self.facingRight else self.walkLFrames
        else:
            newFrames = self.idleRFrames if self.facingRight else self.idleLFrames

        if newFrames != self.currentFrames:
            self.currentFrames = newFrames
            self.animIndex = 0
            self.animTimer = 0

        self.animTimer += 1
        if self.animTimer >= self.animSpeed:
            self.animTimer = 0
            if self.isDead:
                # Hold on the last death frame instead of looping back to frame 0.
                self.animIndex = min(self.animIndex + 1, len(self.currentFrames) - 1)
            else:
                self.animIndex = (self.animIndex + 1) % len(self.currentFrames)

        self.image = self.currentFrames[self.animIndex]

        oldMidBottom = self.rect.midbottom
        self.rect = self.image.get_rect()
        self.rect.midbottom = oldMidBottom

class EscapeEnemy(pygame.sprite.Sprite):

    def __init__(self, imagePath, x, y, windowX, windowY, startDelay=0, numIdleFrames=4):

        super().__init__()

        sheet = pygame.image.load(imagePath).convert_alpha()

        # Slice the idle sheet into frames the same way Wasp/Raccoon/Player
        # do — previously this loaded the WHOLE sheet as one flat image, so
        # nothing ever animated (and if the sheet had multiple frames laid
        # out side by side, it looked like one wide smear instead of one
        # critter).
        frameWidth = sheet.get_width() // numIdleFrames
        frameHeight = sheet.get_height()
        self.idleFrames = [
            sheet.subsurface(pygame.Rect(i * frameWidth, 0, frameWidth, frameHeight))
            for i in range(numIdleFrames)
        ]

        self.animIndex = 0
        self.animTimer = 0
        self.animSpeed = 10

        self.image = self.idleFrames[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


        # movement
        self.speed = 5
        self.escaping = False
        self.startDelay = startDelay  # frames to wait before moving, so a group scatters instead of moving as one block

        # window target
        self.windowX = windowX
        self.windowY = windowY

        self.nearWindow = False

    def startEscape(self):
        self.escaping = True

    def update(self):
        # Idle animation always plays — waiting or fleeing — the same way
        # Prickle keeps animating in idle/walk states.
        self.animate()

        if not self.escaping:
            return

        if self.startDelay > 0:
            self.startDelay -= 1
            return

        # move right
        self.rect.x += self.speed

        # reach window
        if self.rect.x >= self.windowX:

            self.nearWindow = True

            # disappear after breaking window
            self.kill()

    def animate(self):
        self.animTimer += 1
        if self.animTimer >= self.animSpeed:
            self.animTimer = 0
            self.animIndex = (self.animIndex + 1) % len(self.idleFrames)

        self.image = self.idleFrames[self.animIndex]