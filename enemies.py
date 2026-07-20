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

        self.enemy_hpFull = pygame.image.load(r"enemy_assets/enemy_hpFull.png").convert_alpha()
        self.enemy_hpFull = pygame.transform.scale_by(self.enemy_hpFull, 3.15)
        self.enemy_hpEmpty = pygame.image.load(r"enemy_assets/enemy_hpEmpty.png").convert_alpha()
        self.enemy_hpEmpty = pygame.transform.scale_by(self.enemy_hpEmpty, 3.15)

    def takeDamage(self, damage):
        self.hp -= damage

        if self.hp <= 0:
            self.hp = 0
            self.kill()

    def drawHP(self, screen):
        hpX = 590
        hpY = 10
        spacingX = 45
        spacingY = 50
        perRow = 4

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
        self.animSpeed = 8

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

        # --- Dynamic Spatial Audio Setup ---
        self.buzz_sound = pygame.mixer.Sound(r"scene4_assets/wasp_buzz.mp3")
        self.buzzChannel = pygame.mixer.find_channel()
        if self.buzzChannel:
            self.buzzChannel.play(self.buzz_sound, loops=-1)
            self.buzzChannel.set_volume(0.0) # Hidden silently until player approaches
            
    def pickWanderTarget(self):
        margin = 60
        try:
            w, h = SCREEN_WIDTH, SCREEN_HEIGHT
        except NameError:
            w, h = 800, 600
        x = random.randint(margin, w - margin)
        y = random.randint(margin, h - margin)
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
            if self.buzzChannel:
                self.buzzChannel.stop()
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
        """Linearly scales sound channel volume based on proximity to the player."""
        if not self.buzzChannel or not self.buzzChannel.get_busy():
            return

        distance = pygame.math.Vector2(self.rect.center).distance_to(player.rect.center)
        maxHearingDistance = 450.0  # Distance where buzz fades completely down to 0
        
        if distance < maxHearingDistance:
            # Scale volume between 0.0 and 0.5 max volume caps
            volume = (1.0 - (distance / maxHearingDistance)) * 0.5
            self.buzzChannel.set_volume(volume)
        else:
            self.buzzChannel.set_volume(0.0)

    def kill(self):
        if self.buzzChannel:
            self.buzzChannel.stop()
        super().kill()

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

        self.stingGroup = stingGroup           
        self.stingRange = 400                  
        self.stingCooldown = 0
        self.stingCooldownMax = 45  

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
        self.animSpeed = 4    

        self.image = self.currentFrames[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.facingRight = True

        self.teleportSpots = teleportSpots or [(x, y)]
        self.hitsTaken = 0
        self.maxHits = 10

        self.attackRange = 70
        self.attackCooldown = 200
        self.attackCooldownMax = 40   
        self.isAttacking = False
        self.attackTimer = 0

        self.isHurt = False
        self.hurtTimer = 0
        self.hurtDuration = 10

        # Teleport calculations
        self.teleporting = False
        self.teleportPhase = None       
        self.teleportTimer = 0
        self.teleportOutDuration = 10
        self.teleportInDuration = 10  
        self.idleTeleportCooldown = 0
        self.idleTeleportCooldownMax = 175 

        self.shakeTimer = 0
        self.shakeDuration = 12
        self.shakeMagnitude = 6

        # Move speed towards player
        self.moveSpeed = 2.5

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
                # Fast movement tracking
                self.rect.x += (dx / distance) * self.moveSpeed
                self.rect.y += (dy / distance) * self.moveSpeed

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

    def _findLandingSurface(rect, prevBottom, platforms):
        bestPlatform = None
        bestLandY = None

        for platform in platforms:
            if not rect.colliderect(platform.rect):
                continue

            surfaceY = platform.topAt(rect.centerx)
            if surfaceY is None:
                continue

            landingFromAbove = prevBottom <= surfaceY and rect.bottom >= surfaceY
            if landingFromAbove and (bestLandY is None or surfaceY < bestLandY):
                bestPlatform = platform
                bestLandY = surfaceY

        return bestPlatform, bestLandY


class Bomb(pygame.sprite.Sprite):
    _explodeSound = None

    def __init__(self, x, y, speed=4, damage=1, scale=0.3, animSpeed=8, explosionFrameIndex=5, targetPlatform=None):
        super().__init__()

        if Bomb._explodeSound is None:
            Bomb._explodeSound = pygame.mixer.Sound(r"feather_assets/bomb sound.mp3")
        self.explodeSound = Bomb._explodeSound

        sheet = pygame.image.load(r"feather_assets/egg bomb.png").convert()
        numFrames = 10
        sheetWidth = sheet.get_width()
        frameHeight = sheet.get_height()

        #Split the sprite sheet into individual frames.
        frames = []
        for i in range(numFrames):
            startX = round(i * sheetWidth / numFrames)
            endX = round((i + 1) * sheetWidth / numFrames)
            frame = sheet.subsurface(pygame.Rect(startX, 0, endX - startX, frameHeight)).copy()
            frame.set_colorkey((0, 0, 0))
            frame = frame.convert_alpha()
            if scale != 1.0:
                frame = pygame.transform.scale_by(frame, scale)
            frames.append(frame)

        self.currentFrames = frames
        self.animIndex = 0
        self.animTimer = 0
        self.animSpeed = animSpeed

        self.image = self.currentFrames[0]
        self.rect = self.image.get_rect(center=(x, y))

        self.speed = speed
        self.damage = damage

        # State of the bomb and frame index at which the bomb explode
        self.landed = False
        self.exploded = False
        self.explosionFrameIndex = min(explosionFrameIndex, len(self.currentFrames) - 1)
        self.hasDealtDamage = False

        #The platform prickle is currently on
        self.targetPlatform = targetPlatform

        self.landedPlatform = None
        self.landOffset = 0

    def update(self, platforms=None):
        if not self.landed:
            prevBottom = self.rect.bottom
            self.rect.y += self.speed

            if self.targetPlatform is not None:
                self._checkLanding([self.targetPlatform], prevBottom)
            elif platforms:
                self._checkLanding(platforms, prevBottom)

            if not self.landed and self.rect.top > SCREEN_HEIGHT:
                self.kill()
        else:
            if self.landedPlatform is not None:
                self.rect.bottom = self.landedPlatform.rect.y + self.landOffset
            self.animate()

    def _checkLanding(self, platforms, prevBottom):
        bestPlatform, bestLandY = _findLandingSurface(self.rect, prevBottom, platforms)

        if bestLandY is not None:
            self.rect.bottom = bestLandY
            self.landed = True
            self.landedPlatform = bestPlatform
            self.landOffset = self.rect.bottom - bestPlatform.rect.y

    def animate(self):
        self.animTimer += 1
        if self.animTimer >= self.animSpeed:
            self.animTimer = 0

            if self.animIndex >= len(self.currentFrames) - 1:
                # Played all the way through the blast + smoke — done.
                self.kill()
                return

            self.animIndex += 1
            if self.animIndex >= self.explosionFrameIndex and not self.exploded:
                self.exploded = True
                self.explodeSound.play()

        self.image = self.currentFrames[self.animIndex]

        oldMidBottom = self.rect.midbottom
        self.rect = self.image.get_rect()
        self.rect.midbottom = oldMidBottom

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Feathers(Enemy):

    def __init__(self, x, y, bombGroup=None, hp=10, hoverOffset=150, wanderRange=150, scale=0.4,
                 bombIntervalSeconds=2, bombSpeed=4, bombDamage=1, flashFrames=8, flashAmount=70,
                 deadScaleFactor=0.6, verticalWanderRange=100):
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

        self.flyRFrames = extractFrames(sheet, 5)
        self.flyLFrames = [pygame.transform.flip(f, True, False) for f in self.flyRFrames]

        hurtRaw = pygame.image.load(r"feather_assets/feather_hurt.png").convert()
        hurtRaw.set_colorkey((0, 0, 0))
        hurtRaw = hurtRaw.convert_alpha()
        hurtScale = self.flyRFrames[0].get_height() / hurtRaw.get_height()
        hurtImage = pygame.transform.smoothscale_by(hurtRaw, hurtScale)
        self.hurtRFrames = [hurtImage]
        self.hurtLFrames = [pygame.transform.flip(hurtImage, True, False)]

        self.currentFrames = self.flyRFrames
        self.animIndex = 0
        self.animTimer = 0
        self.animSpeed = 6

        self.isHurt = False
        self.hurtTimer = 0
        self.hurtDuration = 15

        self.hurt_sound = pygame.mixer.Sound(r"feather_assets/bird_hurt.mp3")

        deadRaw = pygame.image.load(r"feather_assets/feather_dead.png").convert_alpha()
        deadScale = (self.flyRFrames[0].get_height() / deadRaw.get_height()) * deadScaleFactor
        deadImage = pygame.transform.smoothscale_by(deadRaw, deadScale)
        self.deadRImage = deadImage
        self.deadLImage = pygame.transform.flip(deadImage, True, False)

        # Death physics of Feather
        self.isDead = False
        self.deathFallSpeed = 6
        self.landed = False
        self.landedPlatform = None
        self.landOffset = 0

        # Brief brightness flash on hit 
        self.flashFrames = flashFrames
        self.flashAmount = flashAmount
        self.flashTimer = 0
        self._brightCache = {}

        self.image = self.currentFrames[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = y

        self.facingRight = True

        # Random horizontal movement
        self.speed = 4
        self.wanderRange = wanderRange
        self.wanderTargetX = self.rect.centerx
        self.wanderTimer = 0
        self.wanderChangeRate = random.randint(60, 150)

        # Vertical space between Prickle and Feathers 
        self.hoverOffset = hoverOffset
        self.verticalSpeed = 6

        # Random vertical movement
        self.verticalWanderRange = verticalWanderRange
        self.verticalWanderOffset = 0
        self.verticalWanderTimer = 0
        self.verticalWanderChangeRate = random.randint(60, 150)

        # Keeps the Feather on screen on both x & y
        self.screenMargin = 20

        # Bomb settings
        self.bombGroup = bombGroup
        self.bombInterval = FPS * bombIntervalSeconds
        self.bombTimer = 0
        self.bombSpeed = bombSpeed
        self.bombDamage = bombDamage

    def pickWanderTargetX(self):
        halfWidth = self.rect.width // 2
        low = self.screenMargin + halfWidth
        high = SCREEN_WIDTH - self.screenMargin - halfWidth
        if low >= high:
            return self.rect.centerx
        return random.randint(low, high)

    def takeDamage(self, damage):
        super().takeDamage(damage)
        self.flashTimer = self.flashFrames
        self.hurt_sound.play()
        if self.hp > 0:
            self.isHurt = True
            self.hurtTimer = self.hurtDuration

    def _brightFrame(self, image):
        bright = self._brightCache.get(id(image))
        if bright is None:
            bright = image.copy()
            amount = self.flashAmount
            bright.fill((amount, amount, amount), special_flags=pygame.BLEND_RGB_ADD)
            self._brightCache[id(image)] = bright
        return bright

    def draw(self, screen):
        if self.flashTimer > 0:
            screen.blit(self._brightFrame(self.image), self.rect)
        else:
            screen.blit(self.image, self.rect)

    def update(self, player, platforms=None):
        if self.flashTimer > 0:
            self.flashTimer -= 1

        if self.hp <= 0:
            if not self.isDead:
                self.isDead = True
                self.image = self.deadRImage if self.facingRight else self.deadLImage
                oldMidBottom = self.rect.midbottom
                self.rect = self.image.get_rect()
                self.rect.midbottom = oldMidBottom

            if not self.landed:
                prevBottom = self.rect.bottom
                self.rect.y += self.deathFallSpeed

                if platforms:
                    bestPlatform, bestLandY = _findLandingSurface(self.rect, prevBottom, platforms)
                    if bestLandY is not None:
                        self.rect.bottom = bestLandY
                        self.landed = True
                        self.landedPlatform = bestPlatform
                        self.landOffset = self.rect.bottom - bestPlatform.rect.y

                # stop it at the bottom of the screen instead of falling forever off-screen.
                if not self.landed and self.rect.top > SCREEN_HEIGHT:
                    self.rect.bottom = SCREEN_HEIGHT
                    self.landed = True
            elif self.landedPlatform is not None:
                self.rect.bottom = self.landedPlatform.rect.y + self.landOffset

            return

        if self.isHurt:
            self.hurtTimer -= 1
            if self.hurtTimer <= 0:
                self.isHurt = False

        # Random horizontal movement.
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

        # Random vertical movement while keeping Feathers above Prickle.
        self.verticalWanderTimer += 1
        if self.verticalWanderTimer >= self.verticalWanderChangeRate:
            self.verticalWanderOffset = random.randint(-self.verticalWanderRange, self.verticalWanderRange)
            self.verticalWanderTimer = 0
            self.verticalWanderChangeRate = random.randint(60, 150)

        halfHeight = self.rect.height // 2
        minCentery = self.screenMargin + halfHeight
        maxCentery = SCREEN_HEIGHT - self.screenMargin - halfHeight
        targetY = player.rect.centery - self.hoverOffset + self.verticalWanderOffset
        targetY = max(minCentery, min(maxCentery, targetY))

        dy = targetY - self.rect.centery
        if abs(dy) > 1:
            step = min(self.verticalSpeed, abs(dy))
            self.rect.y += step if dy > 0 else -step

        self.rect.x = max(self.screenMargin, min(SCREEN_WIDTH - self.screenMargin - self.rect.width, self.rect.x))
        self.rect.y = max(self.screenMargin, min(SCREEN_HEIGHT - self.screenMargin - self.rect.height, self.rect.y))

        # Drop a bomb every bombInterval frames (bombIntervalSeconds * FPS).
        if self.bombGroup is not None:
            self.bombTimer += 1
            if self.bombTimer >= self.bombInterval:
                self.bombTimer = 0

                targetPlatform = getattr(player, "currentPlatform", None)
                if targetPlatform is not None:
                    # Drop it above wherever Prickle currently stands
                    dropX = max(targetPlatform.rect.left,
                                min(targetPlatform.rect.right - 1, player.rect.centerx))
                else:
                    # no specific platform to target, so just drop from wherever Feathers currently is.
                    dropX = self.rect.centerx

                bomb = Bomb(dropX, self.rect.bottom, speed=self.bombSpeed, damage=self.bombDamage,
                            targetPlatform=targetPlatform)
                self.bombGroup.add(bomb)

        self.animate()

    def animate(self):
        if self.isHurt:
            newFrames = self.hurtRFrames if self.facingRight else self.hurtLFrames
        else:
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
    def __init__(self, imagePath, x, y, windowX, windowY, startDelay=0, scale=1.0, numIdleFrames=1):
        super().__init__()

        sheet = pygame.image.load(imagePath).convert_alpha()

        self.frames = []
        frameWidth = sheet.get_width() // numIdleFrames
        frameHeight = sheet.get_height()
        for i in range(numIdleFrames):
            frame = sheet.subsurface(pygame.Rect(i * frameWidth, 0, frameWidth, frameHeight))
            # Apply scaling factor dynamically to each frame
            if scale != 1.0:
                frame = pygame.transform.scale_by(frame, scale)
            self.frames.append(frame)

        self.animIndex = 0
        self.animTimer = 0
        self.animSpeed = 10

        self.image = self.frames[self.animIndex]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        # movement
        self.speed = 3
        self.escaping = False
        self.startDelay = startDelay  # frames to wait before moving

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
        
        # Idle animation always plays — waiting or fleeing
        self.animate()

        if not self.escaping:
            return

        if self.startDelay > 0:
            self.startDelay -= 1
            return

        # move right
        self.rect.x += self.speed

        # reach window (or slightly before it to trigger the window smash smoothly)
        if self.rect.x >= self.windowX - 10:
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
            self.animIndex = (self.animIndex + 1) % len(self.frames)

        self.image = self.frames[self.animIndex]

class Rat(pygame.sprite.Sprite):

    def __init__(self, imagePath, platform, offset = 0, direction = -1, speed = 3, hp = 3, particleSystem=None):

        super().__init__()

        self.animations = {

            "idle": self.loadFrames("scene2_assets/rat idle.png",5),

            "walk": self.loadFrames("scene2_assets/rat walk.png",5),

            "attack": self.loadFrames("scene2_assets/rat attack.png",5),

            "hurt": self.loadFrames("scene2_assets/rat hurt.png",3),

            "death": self.loadFrames("scene2_assets/rat death.png",2)
        }

        # ==========================
        # Sprite Scaling
        # ==========================

        self.scale = 0.75

        for state in self.animations:
            scaledFrames = []

            for frame in self.animations[state]:
                frame = pygame.transform.scale_by(
                    frame,
                    self.scale
                )

                scaledFrames.append(frame)

            self.animations[state] = scaledFrames


        self.state = "idle"

        self.frameIndex = 0
        self.animationSpeed = 0.15
        self.yOffset = 20

        self.image = self.animations["idle"][0]

        self.rect = self.image.get_rect()

        self.rect.midbottom = (platform.rect.centerx + offset, platform.rect.top + self.yOffset)


        # Patrol
        self.platform = platform

        self.direction = direction
        self.speed = speed
        self.xVelocity = 0


        # Combat
        self.hp = hp

        self.aggroRange = 250
        self.attackRange = 60
        self.attackCooldown = 0
        self.attackDamage = 1

        self.facingLeft = True

        self.hurtTimer = 0

        self.isDead = False
        self.deathTimer = 60

        self.particleSystem = particleSystem


    def update(self, player):

        if self.attackCooldown > 0:
            self.attackCooldown -= 1

        if self.isDead:
            self.deathTimer -= 1

            self.changeState("death")
            self.animate()

            if self.deathTimer <= 0:
                self.kill()

            return

        if self.hurtTimer > 0:
            self.hurtTimer -= 1

        else:

            distanceX = abs(player.rect.centerx -self.rect.centerx)
            distanceY = abs(player.rect.centery -self.rect.centery)

            if (distanceX <= self.aggroRange and distanceY <= 40):
                self.chase(player)

            else:
                self.patrol()

        self.animate()


    def patrol(self):

        self.changeState("walk")

        self.xVelocity = self.direction * self.speed
        self.rect.x += int(self.xVelocity)

        if self.rect.left <= self.platform.rect.left:
            self.rect.left = self.platform.rect.left
            self.direction = 1

        elif self.rect.right >= self.platform.rect.right:
            self.rect.right = self.platform.rect.right
            self.direction = -1

        self.facingLeft = self.direction < 0


    def chase(self, player):

        dx = (player.rect.centerx - self.rect.centerx)
        dy = abs(player.rect.centery - self.rect.centery)

        if (abs(dx) <= self.attackRange and dy <= 30):

            if dx < 0:
                self.direction = -1
            else:
                self.direction = 1

            self.facingLeft = self.direction < 0
            self.changeState("attack")

            if self.attackCooldown == 0:
                player.takeDamage(1)
                self.attackCooldown = 60
                player.rect.x += self.direction * 50

            return

        self.changeState("walk")

        if dx < 0:
            self.direction = -1

        else:
            self.direction = 1

        self.xVelocity = self.direction * self.speed
        self.rect.x += int(self.xVelocity)

        # IMPORTANT
        # Stop leaving patrol platform

        if self.rect.left < self.platform.rect.left:
            self.rect.left = self.platform.rect.left

        if self.rect.right > self.platform.rect.right:
            self.rect.right = self.platform.rect.right

        self.facingLeft = self.direction < 0


    def takeDamage(self, amount):

        if self.isDead:
            return

        self.hp -= amount

        if self.hp <= 0:
            self.hp = 0
            self.isDead = True

            self.changeState("death")
            self.deathTimer = 30

            if self.particleSystem:

                from effects import createRatDeathEffect

                createRatDeathEffect(
                    self.particleSystem,
                    self.rect.center
                )

        else:
            self.changeState("hurt")
            self.hurtTimer = 15


    def loadFrames(self, imagePath, frameCount):

        sheet = pygame.image.load(imagePath).convert_alpha()

        frames=[]

        width = sheet.get_width() // frameCount
        height = sheet.get_height()

        for i in range(frameCount):
            frame = sheet.subsurface(pygame.Rect(i * width, 0, width, height))

            frames.append(frame)

        return frames


    def animate(self):
        frames = self.animations[self.state]

        self.frameIndex += self.animationSpeed

        if self.frameIndex >= len(frames):
            self.frameIndex = 0

        bottom = self.rect.bottom
        left = self.rect.left

        self.image = frames[int(self.frameIndex)]

        self.rect = self.image.get_rect()

        self.rect.left = left
        self.rect.bottom = bottom

        if self.facingLeft:self.image = pygame.transform.flip(self.image, True, False)


    def changeState(self,state):

        if self.state != state:
            self.state = state
            self.frameIndex = 0


class BossRat(Enemy):

    def __init__(self, x, y, hp = 10):
        super().__init__(x, y, hp)

        # ==========================
        # Load Sprite Sheets
        # ==========================

        ratIdle = pygame.image.load(
            r"scene2_assets/Rat Boss Idle.png"
        ).convert_alpha()

        ratWalk = pygame.image.load(
            r"scene2_assets/Rat Boss Walk.png"
        ).convert_alpha()

        ratAttack = pygame.image.load(
            r"scene2_assets/Rat Boss Pounce.png"
        ).convert_alpha()

        ratHurt = pygame.image.load(
            r"scene2_assets/Rat Boss Hurt.png"
        ).convert_alpha()

        ratDeath = pygame.image.load(
            r"scene2_assets/Rat Boss Death.png"
        ).convert_alpha()


        # Scale
        scale = 1.2

        ratIdle = pygame.transform.scale_by(ratIdle, scale)
        ratWalk = pygame.transform.scale_by(ratWalk, scale)
        ratAttack = pygame.transform.scale_by(ratAttack, scale)
        ratHurt = pygame.transform.scale_by(ratHurt, scale)
        ratDeath = pygame.transform.scale_by(ratDeath, scale)



        # ==========================
        # Frame Extraction
        # ==========================

        def extractFrames(sheet, count):

            frames = []

            width = sheet.get_width() // count
            height = sheet.get_height()

            for i in range(count):

                frame = sheet.subsurface(
                    pygame.Rect(
                        i * width,
                        0,
                        width,
                        height
                    )
                )

                frames.append(frame)

            return frames

        idleFrames = extractFrames(ratIdle, 7)
        walkFrames = extractFrames(ratWalk, 7)
        attackFrames = extractFrames(ratAttack, 4)
        hurtFrames = extractFrames(ratHurt, 7)
        deathFrames = extractFrames(ratDeath, 6)

        self.animations = {

            "idle": idleFrames,
            "walk": walkFrames,
            "attack": attackFrames,
            "hurt": hurtFrames,
            "death": deathFrames

        }


        # ==========================
        # Animation Variables
        # ==========================

        self.currentFrames = self.animations["idle"]

        self.animIndex = 0
        self.animTimer = 0
        self.animSpeed = 8

        self.image = self.currentFrames[0]

        self.rect = self.image.get_rect()

        self.rect.x = x
        self.rect.bottom = y + 15


        # ==========================
        # Boss Stats
        # ==========================
        self.isDead = False

        self.isHurt = False
        self.hurtTimer = 0
        self.hurtDuration = 45


        # ==========================
        # Boss AI
        # ==========================

        self.speed = 2

        self.attackRange = 100
        self.detectRange = 900

        self.attackCooldown = 0
        self.attackCooldownMax = 120
        self.attackDamage = 1

        self.isAttacking = False
        self.attackTimer = 0

        self.state = "idle"


    def takeDamage(self, damage):

        if self.isDead:
            return

        self.hp -= damage

        self.isHurt = True
        self.hurtTimer = self.hurtDuration

        self.state = "hurt"

        if self.hp <= 0:

            self.hp = 0
            self.isDead = True

    def animate(self):

        if self.isDead:
            newFrames = self.animations["death"]

        elif self.isHurt:
            newFrames = self.animations["hurt"]

        elif self.state == "attack":
            newFrames = self.animations["attack"]

        elif self.state == "walk":
            newFrames = self.animations["walk"]

        else:
            newFrames = self.animations["idle"]


        if newFrames != self.currentFrames:
            self.currentFrames = newFrames
            self.animIndex = 0
            self.animTimer = 0

        self.animTimer += 1

        if self.animTimer >= self.animSpeed:

            self.animTimer = 0

            self.animIndex += 1

            if self.animIndex >= len(self.currentFrames):

                if self.isDead:

                    self.animIndex = len(self.currentFrames)-1

                else:

                    self.animIndex = 0

        self.flipImage()

    def update(self, player):
        if self.isDead:
            self.animate()
            return

        # Attack cooldown
        if self.attackCooldown > 0:
            self.attackCooldown -= 1

        # Hurt cooldown
        if self.hurtTimer > 0:
            self.hurtTimer -= 1

        else:
            self.isHurt = False

        dx = player.rect.centerx - self.rect.centerx

        if dx > 0:

            self.facingRight = True

        else:

            self.facingRight = False

        dy = player.rect.centery - self.rect.centery

        distance = (dx*dx + dy*dy)**0.5

        if distance <= self.detectRange:

            if distance <= self.attackRange:

                self.attack(player)

            elif not self.isAttacking:

                self.chase(player, dx)

        else:

            self.state = "idle"


        if self.isAttacking:

            self.attackTimer -= 1

            if self.attackTimer <= 0:

                self.isAttacking = False
                self.state = "idle"

        self.animate()

    def chase(self, player, dx):

        self.state = "walk"

        if dx > 0:
            self.rect.x += self.speed
            self.facingRight = True

        else:
            self.rect.x -= self.speed
            self.facingRight = False

    def attack(self, player):

        if self.attackCooldown == 0 and not self.isAttacking:

            self.state = "attack"
            self.isAttacking = True

            self.attackTimer = (
                len(self.animations["attack"])
                *
                self.animSpeed
            )

            player.takeDamage(
                self.attackDamage
            )

            if player.rect.centerx < self.rect.centerx:
                player.rect.x -= 40

            else:
                player.rect.x += 40

            self.attackCooldown = self.attackCooldownMax
            self.attackCooldown = self.attackCooldownMax

    def flipImage(self):

        if self.facingRight:
            self.image = pygame.transform.flip(
                self.currentFrames[self.animIndex],
                True,
                False
            )
            
        else:
            self.image = self.currentFrames[self.animIndex]