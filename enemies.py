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
        raccoonIdle = pygame.transform.scale_by(raccoonIdle, 1.2)
        raccoonWalk = pygame.image.load(r"scene1_assets/raccoon_walk.png").convert_alpha()
        raccoonWalk = pygame.transform.scale_by(raccoonWalk, 1.2)
        raccoonHurt = pygame.image.load(r"scene1_assets/raccoon_hurt.png").convert_alpha()
        raccoonHurt = pygame.transform.scale_by(raccoonHurt, 1.2)
        raccoonDeath = pygame.image.load(r"scene1_assets/raccoon_death.png").convert_alpha()
        raccoonDeath = pygame.transform.scale_by(raccoonDeath, 1.2)

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

        # AI
        self.speed = 1.5
        self.runAwayRange = 180   # start running once player is this close
        self.groundY = y       # keep raccoon on the ground

        self.isHurt = False
        self.hurtTimer = 0
        self.hurtDuration = 10

    def update(self, player):
        if self.hp <= 0:
            return

        if self.isHurt:
            self.hurtTimer -= 1
            if self.hurtTimer <= 0:
                self.isHurt = False

        dx = self.rect.centerx - player.rect.centerx
        dy = self.rect.centery - player.rect.centery
        distance = max((dx ** 2 + dy ** 2) ** 0.5, 1)

        if distance <= self.runAwayRange:
            self.runAway(dx, dy, distance)

        self.rect.bottom = self.groundY  # stay grounded

        self.animate()

    def runAway(self, dx, dy, distance):
        # Move away from the player (opposite direction of dx, dy)
        self.rect.x += (dx / distance) * self.speed
        self.rect.y += (dy / distance) * self.speed
        self.facingRight = dx > 0

    def animate(self):
        if self.isHurt:
            newFrames = self.hurtRFrames if self.facingRight else self.hurtLFrames
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