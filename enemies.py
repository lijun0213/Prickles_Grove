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

        self.enemy_hpFull = pygame.image.load(r"player_assets/enemy_hpFull.png").convert_alpha()
        self.enemy_hpFull = pygame.transform.scale_by(self.enemy_hpFull, 4.5)
        self.enemy_hpEmpty = pygame.image.load(r"player_assets/enemy_hpEmpty.png").convert_alpha()
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
        super().__init__(x, y, 1)

        # Enemy sprite
        waspIdle = pygame.image.load(r"scene4_assets/wasp_idle.png").convert_alpha()
        waspIdle = pygame.transform.scale_by(waspIdle, 1.2)
        waspAttack = pygame.image.load(r"scene4_assets/wasp_attack.png").convert_alpha()
        waspAttack = pygame.transform.scale_by(waspAttack, 1.2)
        
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

        self.idleLFrames = extractFrames(waspIdle, 4)
        self.idleRFrames = [pygame.transform.flip(f, True, False) for f in self.idleLFrames]
        self.attackLFrames = extractFrames(waspAttack, 7)
        self.attackRFrames = [pygame.transform.flip(f, True, False) for f in self.attackLFrames]

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

        # AI Mechanics
        self.speed = 2  # Modified dynamically inside Scene4 if needed
        self.wanderTarget = self.pickWanderTarget()
        self.wanderTimer = 0
        self.wanderChangeRate = 90  # frames before picking a new random spot
 
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

        self.buzz_sound = pygame.mixer.Sound(r"scene4_assets/wasp_buzz.mp3")
        self.buzz_sound.set_volume(0.3)
        self.buzzCooldown = 0
            
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
    
    def updateBuzz(self, player):
        distance = pygame.math.Vector2(
            self.rect.center
        ).distance_to(
            player.rect.center
        )

        if distance < 250:
            if self.buzzCooldown <= 0:
                self.buzz_sound.play()
                self.buzzCooldown = 90  # frames

        if self.buzzCooldown > 0:
            self.buzzCooldown -= 1

    def animate(self):
        if self.isAttacking:
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


class WaspQueen(Enemy):
    def __init__(self, x, y, teleportSpots=None, stingGroup=None, scale=1.4):
        super().__init__(x, y, 10)

        self.stingGroup = stingGroup           # Bound correctly via initializer 
        self.stingRange = 400                  
        self.stingCooldown = 0
        self.stingCooldownMax = 100  

        queenIdle = pygame.image.load(r"scene4_assets/queen_idle.png").convert_alpha()
        queenIdle = pygame.transform.scale_by(queenIdle, scale)
        queenAttack = pygame.image.load(r"scene4_assets/queen_attack.png").convert_alpha()
        queenAttack = pygame.transform.scale_by(queenAttack, scale)
        queenSting = pygame.image.load(r"scene4_assets/queen_sting.png").convert_alpha()
        queenSting = pygame.transform.scale_by(queenSting, scale)

        def extractFrames(sheet, numFrames):
            frameWidth = sheet.get_width() // numFrames
            frameHeight = sheet.get_height()
            return [sheet.subsurface(pygame.Rect(i * frameWidth, 0, frameWidth, frameHeight))
                    for i in range(numFrames)]

        self.idleLFrames = extractFrames(queenIdle, 4)
        self.idleRFrames = [pygame.transform.flip(f, True, False) for f in self.idleLFrames]
        self.attackLFrames = extractFrames(queenAttack, 4)
        self.attackRFrames = [pygame.transform.flip(f, True, False) for f in self.attackLFrames]
        self.stingLFrames = extractFrames(queenSting, 2)
        self.stingRFrames = [pygame.transform.flip(f, True, False) for f in self.stingLFrames]

        self.currentFrames = self.idleRFrames
        self.animIndex = 0
        self.animTimer = 0
        self.animSpeed = 8

        self.image = self.currentFrames[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.facingRight = True

        self.teleportSpots = teleportSpots or [(x, y)]
        self.hitsTaken = 0
        self.maxHits = 10

        self.attackRange = 70
        self.attackCooldown = 0
        self.attackCooldownMax = 90
        self.isAttacking = False
        self.attackTimer = 0

        self.isHurt = False
        self.hurtTimer = 0
        self.hurtDuration = 10

        # Teleport calculations
        self.teleporting = False
        self.teleportPhase = None       
        self.teleportTimer = 0
        self.teleportOutDuration = 15
        self.teleportInDuration = 15
        self.idleTeleportCooldown = 0
        self.idleTeleportCooldownMax = 300  

        self.shakeTimer = 0
        self.shakeDuration = 12
        self.shakeMagnitude = 6

        self.buzz_sound = pygame.mixer.Sound(r"scene4_assets/wasp_buzz.mp3")
        self.buzz_sound.set_volume(0.3)
        self.buzzCooldown = 0

    def takeDamage(self, damage):
        if self.teleporting or self.hp <= 0:
            return  

        self.hitsTaken += 1
        self.hp = max(0, self.maxHits - self.hitsTaken)
        self.isHurt = True
        self.hurtTimer = self.hurtDuration
        self.shakeTimer = self.shakeDuration

        if self.hitsTaken >= self.maxHits:
            self.hp = 0
            self.kill()
        else:
            self.startTeleport()

    def startTeleport(self):
        self.teleporting = True
        self.teleportPhase = "out"
        self.teleportTimer = self.teleportOutDuration

    def update(self, player, active=False):
        if self.hp <= 0:
            return
        
        if not active:
            if self.shakeTimer > 0:
                self.shakeTimer -= 1
            self.animate()
            return

        if self.teleporting:
            self.updateTeleport()
        else:
            self.idleTeleportCooldown += 1
            if self.idleTeleportCooldown >= self.idleTeleportCooldownMax:
                self.startTeleport()

            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            distance = max((dx ** 2 + dy ** 2) ** 0.5, 1)

            if distance <= self.attackRange:
                self.onTouchPlayer(player)
            elif distance <= self.stingRange and self.stingCooldown == 0 and self.stingGroup is not None:
                self.fireSting(player)
            else:
                self.rect.x += (dx / distance) * 1.5
                self.rect.y += (dy / distance) * 1.5

            self.facingRight = dx > 0

        if self.attackCooldown > 0:
            self.attackCooldown -= 1
        if self.stingCooldown > 0:
            self.stingCooldown -= 1
        if self.isHurt:
            self.hurtTimer -= 1
            if self.hurtTimer <= 0:
                self.isHurt = False
        if self.shakeTimer > 0:
            self.shakeTimer -= 1
        if self.isAttacking:
            self.attackTimer -= 1
            if self.attackTimer <= 0:
                self.isAttacking = False

        self.animate()

    def fireSting(self, player):
        self.isAttacking = True
        self.attackTimer = len(self.attackRFrames) * self.animSpeed
        sting = Sting(self.rect.centerx, self.rect.centery, player.rect.centerx, player.rect.centery)
        self.stingGroup.add(sting)
        self.stingCooldown = self.stingCooldownMax

    def onTouchPlayer(self, player):
        if self.attackCooldown == 0 and not self.isHurt:
            self.isAttacking = True
            self.attackTimer = len(self.attackRFrames) * self.animSpeed
            player.takeDamage(1)
            self.attackCooldown = self.attackCooldownMax

    def updateTeleport(self):
        self.teleportTimer -= 1

        if self.teleportPhase == "out" and self.teleportTimer <= 0:
            newSpot = random.choice(self.teleportSpots)
            self.rect.center = newSpot
            self.teleportPhase = "in"
            self.teleportTimer = self.teleportInDuration

        elif self.teleportPhase == "in" and self.teleportTimer <= 0:
            self.teleporting = False
            self.teleportPhase = None
            self.idleTeleportCooldown = 0

    def updateBuzz(self, player):
        distance = pygame.math.Vector2(
            self.rect.center
        ).distance_to(
            player.rect.center
        )

        if distance < 250:
            if self.buzzCooldown <= 0:
                self.buzz_sound.play()
                self.buzzCooldown = 90  # frames

        if self.buzzCooldown > 0:
            self.buzzCooldown -= 1

    def animate(self):
        if self.isAttacking:
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
        oldCenter = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = oldCenter


class Sting(pygame.sprite.Sprite):
    def __init__(self, x, y, targetX, targetY, speed=7, maxRange=600):
        super().__init__()

        self.image = pygame.Surface((22, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (255, 210, 0), (0, 0, 16, 10))
        pygame.draw.polygon(self.image, (40, 40, 40), [(14, 3), (22, 5), (14, 7)])

        self.x = float(x)
        self.y = float(y)
        self.startX, self.startY = self.x, self.y
        self.maxRange = maxRange

        dx = targetX - x
        dy = targetY - y
        distance = max((dx * dx + dy * dy) ** 0.5, 1)
        self.velocityX = (dx / distance) * speed
        self.velocityY = (dy / distance) * speed

        angle = pygame.math.Vector2(dx, dy).angle_to(pygame.math.Vector2(1, 0))
        self.image = pygame.transform.rotate(self.image, angle)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.x += self.velocityX
        self.y += self.velocityY
        self.rect.center = (int(self.x), int(self.y))

        distance = ((self.x - self.startX) ** 2 + (self.y - self.startY) ** 2) ** 0.5
        if distance >= self.maxRange:
            self.kill()
        if self.x < -100 or self.x > 2000 or self.y < -100 or self.y > 1500:
            self.kill()


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

        self.flash_timer = 0
        self.flash_duration = 6

        # sound effect
        self.raccoon_whimper = pygame.mixer.Sound(r"scene1_assets/raccoon_whimper.mp3")
        self.raccoon_whimper.set_volume(0.7)

    def activate(self):
        # Called once the player gets close enough to trigger the chase —
        # Nugget stops idling and starts randomly running/jumping in panic.
        self.active = True

    def takeDamage(self, damage):
        if not self.isDead:
            self.hp -= damage
            self.isHurt = True
            self.hurtTimer = self.hurtDuration
            
            # Trigger the flash effect!
            self.flash_timer = self.flash_duration

            if self.hp <= 0:
                self.hp = 0
                self.isDead = True
                self.deathTimer = 60
                self.currentFrames = self.deathRFrames
                self.animIndex = 0
                self.raccoon_whimper.play()

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

        if self.flash_timer > 0:
            self.flash_timer -= 1

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


class Feathers(Enemy):

    def __init__(self, x, y, hp=10, hoverOffset=150, wanderRange=150, scale=0.4):
        super().__init__(x, y, hp)

        sheet = pygame.image.load(r"feather_assets/feather_movement.png").convert_alpha()
        sheet = pygame.transform.scale_by(sheet, scale)

        def extractFrames(sheet, numFrames):
            frames = []
            frameWidth = sheet.get_width() // numFrames
            frameHeight = sheet.get_height()
            for i in range(numFrames):
                frame = sheet.subsurface(pygame.Rect(i * frameWidth, 0, frameWidth, frameHeight))
                frames.append(frame)
            return frames

        # feather_movement.png is a 5-frame flapping-flight loop.
        self.flyRFrames = extractFrames(sheet, 5)
        self.flyLFrames = [pygame.transform.flip(f, True, False) for f in self.flyRFrames]

        self.currentFrames = self.flyRFrames
        self.animIndex = 0
        self.animTimer = 0
        self.animSpeed = 6

        self.image = self.currentFrames[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = y

        self.facingRight = True

        # Horizontal wander — picks a random x within wanderRange of wherever
        # it currently is, drifts toward it, then picks a new one, so it
        # reads as "flying left and right randomly" rather than patrolling a
        # fixed line.
        self.speed = 2
        self.wanderRange = wanderRange
        self.wanderTargetX = self.rect.centerx
        self.wanderTimer = 0
        self.wanderChangeRate = random.randint(60, 150)

        # Vertical tracking — eases toward hoverOffset px above Prickle's
        # current on-screen position every frame. Reading player.rect
        # directly (rather than tracking scrollY/baseY like a background
        # platform would) means this "just works" through camera scrolling —
        # it's always chasing wherever Prickle visibly is right now.
        self.hoverOffset = hoverOffset
        self.verticalSpeed = 3

        # Keeps the whole sprite on screen on both axes — without this, a
        # large hoverOffset can push Feathers' target above y=0 (off the top
        # of the screen) whenever Prickle is already near the top himself,
        # since the raw target is just "player's y minus hoverOffset" with
        # nothing stopping it from going negative.
        self.screenMargin = 20

    def pickWanderTargetX(self):
        halfWidth = self.rect.width // 2
        low = self.screenMargin + halfWidth
        high = SCREEN_WIDTH - self.screenMargin - halfWidth
        if low >= high:
            return self.rect.centerx
        return random.randint(low, high)

    def update(self, player):
        if self.hp <= 0:
            return

        # Horizontal: drift toward a randomly-changing target x.
        self.wanderTimer += 1
        reachedTarget = abs(self.rect.centerx - self.wanderTargetX) < 6
        if reachedTarget or self.wanderTimer >= self.wanderChangeRate:
            self.wanderTargetX = self.pickWanderTargetX()
            self.wanderTimer = 0
            self.wanderChangeRate = random.randint(60, 150)

        dx = self.wanderTargetX - self.rect.centerx
        if abs(dx) > 1:
            step = min(self.speed, abs(dx))
            self.rect.x += step if dx > 0 else -step
            self.facingRight = dx > 0

        # Vertical: ease toward hoverOffset px above Prickle's current
        # screen position — never snaps, so it smoothly rises as he climbs.
        # Clamped so the target itself never asks Feathers to leave the
        # screen, regardless of how large hoverOffset is or where Prickle
        # currently is.
        halfHeight = self.rect.height // 2
        minCentery = self.screenMargin + halfHeight
        maxCentery = SCREEN_HEIGHT - self.screenMargin - halfHeight
        targetY = player.rect.centery - self.hoverOffset
        targetY = max(minCentery, min(maxCentery, targetY))

        dy = targetY - self.rect.centery
        if abs(dy) > 1:
            step = min(self.verticalSpeed, abs(dy))
            self.rect.y += step if dy > 0 else -step

        # Hard safety clamp on top of the eased tracking above — belt and
        # braces in case Feathers ever starts off-screen (e.g. its initial
        # spawn position) or something else nudges its rect directly.
        self.rect.x = max(self.screenMargin, min(SCREEN_WIDTH - self.screenMargin - self.rect.width, self.rect.x))
        self.rect.y = max(self.screenMargin, min(SCREEN_HEIGHT - self.screenMargin - self.rect.height, self.rect.y))

        self.animate()

    def animate(self):
        newFrames = self.flyRFrames if self.facingRight else self.flyLFrames

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


class EscapeEnemy(pygame.sprite.Sprite):
    def __init__(self, imagePath, x, y, windowX, windowY, startDelay=0, numIdleFrames=4):
        super().__init__()

        sheet = pygame.image.load(imagePath).convert_alpha()

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
        self.speed = 3
        self.escaping = False
        self.startDelay = startDelay  # frames to wait before moving, so a group scatters instead of moving as one block

        # window target
        self.windowX = windowX
        self.windowY = windowY

        self.nearWindow = False

        self.shrinking = False
        self.shrinkTimer = 0
        self.shrinkDuration = 20
        self.shrinkStartImage = None

    def startEscape(self):
        self.escaping = True

    def update(self):
        if self.shrinking:
            self.updateShrink()
            return
        
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
            self.beginShrink()

    def beginShrink(self):
        self.shrinking = True
        self.shrinkTimer = self.shrinkDuration
        self.shrinkStartImage = self.image
        self.nearWindow = True
        self.rect.center = (self.windowX, self.windowY)

    def updateShrink(self):
        self.shrinkTimer -= 1
        progress = 1 - max(self.shrinkTimer, 0) / self.shrinkDuration  # 0 -> 1 over the shrink

        scaleFactor = max(0.02, 1 - progress)
        center = self.rect.center
        self.image = pygame.transform.scale_by(self.shrinkStartImage, scaleFactor)
        self.rect = self.image.get_rect(center=center)

        if self.shrinkTimer <= 0:
            self.kill()

    def animate(self):
        self.animTimer += 1
        if self.animTimer >= self.animSpeed:
            self.animTimer = 0
            self.animIndex = (self.animIndex + 1) % len(self.idleFrames)

        self.image = self.idleFrames[self.animIndex]