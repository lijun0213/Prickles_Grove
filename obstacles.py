import math
import pygame
import random
from settings import *
from effects import Particle


#General Platform for all scenes
class Platform(pygame.sprite.Sprite):

    def __init__(self, imagePath, x, y, angle=0, scale=1.0, blocksBullets=False, visible=True, hazard=False):
        super().__init__()
        self.image = pygame.image.load(imagePath).convert_alpha()

        self.scale = scale
        if scale != 1.0:
            self.image = pygame.transform.scale_by(self.image, scale)

        self.angle = angle
        if angle:
            self.image = pygame.transform.rotate(self.image, angle)

        self.rect = self.image.get_rect(topleft=(x, y))
        self.blocksBullets = blocksBullets
        self.visible = visible

        # Hazard Condition, if true it will hurt prickle over time.
        self.hazard = hazard

        self.baseY = self.rect.y

        self.mask = pygame.mask.from_surface(self.image)
        width, height = self.image.get_size()


        self.surfaceY = []
        for col in range(width):
            colY = None
            for row in range(height):
                if self.mask.get_at((col, row)):
                    colY = row
                    break
            self.surfaceY.append(colY)

    def topAt(self, worldX):
        col = int(worldX - self.rect.x)
        if col < 0 or col >= len(self.surfaceY):
            return None
        localY = self.surfaceY[col]
        if localY is None:
            return None
        return self.rect.y + localY

    def collidesRect(self, otherRect):
        if not self.rect.colliderect(otherRect):
            return False
        otherMask = pygame.mask.Mask(otherRect.size, fill=True)
        offset = (otherRect.x - self.rect.x, otherRect.y - self.rect.y)
        return self.mask.overlap(otherMask, offset) is not None

    def draw(self, screen):
        if self.visible:
            screen.blit(self.image, self.rect)

    def update(self):
        pass

#Function to slice a sprite sheet into individual frames based on gaps between them
def _sliceFramesByGaps(sheet):
    width, height = sheet.get_size()
    mask = pygame.mask.from_surface(sheet)

    colHasContent = [
        any(mask.get_at((x, y)) for y in range(height))
        for x in range(width)
    ]

    runs = []
    inRun = False
    start = 0
    for x, has in enumerate(colHasContent):
        if has and not inRun:
            start = x
            inRun = True
        elif not has and inRun:
            runs.append((start, x))
            inRun = False
    if inRun:
        runs.append((start, width))

    return [sheet.subsurface(pygame.Rect(s, 0, e - s, height)).copy() for s, e in runs]

#Bouncy Mushroom
class Mushroom(pygame.sprite.Sprite):

    def __init__(self, sheetPath, x, y, bounceForce=22, angle=0, scale=0.35, frameDelay=4):
        super().__init__()
        sheet = pygame.image.load(sheetPath).convert_alpha()
        if scale != 1.0:
            sheet = pygame.transform.scale_by(sheet, scale)

        # Slice mushroom frames into individual frames 
        self.frames = _sliceFramesByGaps(sheet)
        self.angle = angle
        if angle:
            self.frames = [pygame.transform.rotate(f, angle) for f in self.frames]

        self.restFrame = 0
        self.frameDelay = frameDelay  # game-frames each animation frame holds

        self.image = self.frames[self.restFrame]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.baseY = self.rect.y

        self.bounceForce = bounceForce

        # angle of the mushroom
        rad = math.radians(angle)
        self.bounceVX = bounceForce * -math.sin(rad)
        self.bounceVY = bounceForce * -math.cos(rad)

        self.bouncing = False
        self.animIndex = 0
        self.animTimer = 0

        # Bounce sound — same per-instance load pattern as Feathers'
        # hurt_sound / Nest's hit_sound.
        self.bounce_sound = pygame.mixer.Sound(r"scene3_assets/bounceshroom (bouncy mushroom).mp3")

        mask = pygame.mask.from_surface(self.image)
        width, height = self.image.get_size()
        self.surfaceY = []
        for col in range(width):
            colY = None
            for row in range(height):
                if mask.get_at((col, row)):
                    colY = row
                    break
            self.surfaceY.append(colY)

    def topAt(self, worldX):
        col = int(worldX - self.rect.x)
        if col < 0 or col >= len(self.surfaceY):
            return None
        localY = self.surfaceY[col]
        if localY is None:
            return None
        return self.rect.y + localY

    def trigger(self):
        self.bouncing = True
        self.animIndex = 0
        self.animTimer = 0
        self.bounce_sound.play()

    def update(self):
        if not self.bouncing:
            return

        self.animTimer += 1
        if self.animTimer >= self.frameDelay:
            self.animTimer = 0
            self.animIndex += 1

            if self.animIndex >= len(self.frames):
                self.animIndex = 0
                self.bouncing = False

        self.image = self.frames[self.animIndex] if self.bouncing else self.frames[self.restFrame]

    def draw(self, screen):
        drawRect = self.image.get_rect(midbottom=self.rect.midbottom)
        screen.blit(self.image, drawRect)


#Bird nest — only prickle's bullets interact with it.
class Nest(pygame.sprite.Sprite):

    def __init__(self, sheetPath, x, y, maxHits=5, scale=0.5, flashFrames=8, flashAmount=70):
        super().__init__()
        sheet = pygame.image.load(sheetPath).convert_alpha()
        if scale != 1.0:
            sheet = pygame.transform.scale_by(sheet, scale)

        self.frames = _sliceFramesByGaps(sheet)
        self.maxHits = maxHits
        self.hitsTaken = 0
        self.destroyed = False
        self.frameIndex = 0

        # Nest flash on hit 
        self.flashFrames = flashFrames
        self.flashAmount = flashAmount
        self.flashTimer = 0
        self._brightCache = {}  # frameIndex -> pre-brightened surface

        self.image = self.frames[self.frameIndex]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.baseY = self.rect.y  # see Platform.baseY

        # Nest hit sound
        self.hit_sound = pygame.mixer.Sound(r"feather_assets/nest_sound.mp3")

    def _brightFrame(self, frameIndex):
        bright = self._brightCache.get(frameIndex)
        if bright is None:
            bright = self.frames[frameIndex].copy()
            amount = self.flashAmount
            bright.fill((amount, amount, amount), special_flags=pygame.BLEND_RGB_ADD)
            self._brightCache[frameIndex] = bright
        return bright

    def takeHit(self):
        """Register one bullet hit. Returns True if the hit landed (nest
        wasn't already destroyed), False if it was a no-op."""
        if self.destroyed:
            return False

        self.hitsTaken += 1
        self.frameIndex = min(self.hitsTaken, len(self.frames) - 1)
        self.flashTimer = self.flashFrames
        self.hit_sound.play()

        if self.hitsTaken >= self.maxHits:
            self.destroyed = True

        return True

    def draw(self, screen):
        if self.flashTimer > 0:
            screen.blit(self._brightFrame(self.frameIndex), self.rect)
        else:
            screen.blit(self.frames[self.frameIndex], self.rect)

    def update(self):
        if self.flashTimer > 0:
            self.flashTimer -= 1


#Invisible vertical wall, prevent players from leaving game area.
class Wall:
    def __init__(self, x, top, bottom):
        self.x = x
        self.rect = pygame.Rect(x, top, 1, bottom - top)
        self.baseY = self.rect.y  # see Platform.baseY

    def draw(self, screen):
        pass

    def update(self):
        pass

class MovingPlatform(Platform):
    def __init__(self, imagePath, x, y, scale=1.0, moveRange=200, speed=2, axis='X'):
        super().__init__(imagePath, x, y, scale)
        self.startX = x
        self.startY = y
        self.moveRange = moveRange
        self.speed = speed
        self.axis = axis.upper() # 'X' for horizontal, 'Y' for vertical
        self.direction = 1

        self.scale = scale
        if scale != 1.0:
            self.image = pygame.transform.scale_by(self.image, scale)
        
        # Keep track of how much the platform shifted on the current frame
        # The player code will read this to move the player alongside it
        self.movementDeltaX = 0
        self.movementDeltaY = 0

    def update(self):
        oldX = self.rect.x
        oldY = self.rect.y

        if self.axis == 'X':
            self.rect.x += self.speed * self.direction
            # Reverse direction if bounds exceeded
            if abs(self.rect.x - self.startX) >= self.moveRange:
                self.direction *= -1
        else: # 'Y' axis movement
            self.rect.y += self.speed * self.direction
            if abs(self.rect.y - self.startY) >= self.moveRange:
                self.direction *= -1

        # Calculate exact change in position this frame
        self.movementDeltaX = self.rect.x - oldX
        self.movementDeltaY = self.rect.y - oldY


class InvisiblePlatform(pygame.sprite.Sprite):

    def __init__(self, x, y, width, height):
        super().__init__()

        self.rect = pygame.Rect(
            x,
            y,
            width,
            height
        )

        self.visible = False


    def topAt(self, worldX):

        if self.rect.left <= worldX <= self.rect.right:
            return self.rect.top

        return None


    def draw(self, screen):
        pass


    def update(self):
        pass


class Boulder(pygame.sprite.Sprite):

    def __init__(self, imagePath, x, y, speed=2):
        super().__init__()

        self.image = pygame.image.load(imagePath).convert_alpha()
        self.rect = self.image.get_rect(topleft=(x,y))

        self.speed = speed
        self.direction = -1

        # Gravity
        self.velocityY = 0
        self.gravity = 0.8

        # State
        self.active = True
        self.falling = False


    def trigger(self):
        self.active = True


    def checkEdge(self):

        # when reaching the edge
        if self.rect.x <= 400:

            self.falling = True


    def update(self):

        if not self.active:
            return


        # Horizontal movement
        if not self.falling:

            self.rect.x += self.speed * self.direction


        # Falling after edge
        else:

            self.velocityY += self.gravity
            self.rect.y += self.velocityY


            # Remove after falling off screen
            if self.rect.top > SCREEN_HEIGHT + 200:
                self.kill()


    def draw(self, screen):

        screen.blit(
            self.image,
            self.rect
        )

class SporeCloud(pygame.sprite.Sprite):

    def __init__(self, imagePath, x, y, width, height):
        super().__init__()

        self.image = pygame.image.load(imagePath).convert_alpha()

        self.image = pygame.transform.scale(
            self.image,
            (
                width,
                height
            )
        )

        self.rect = self.image.get_rect(
            topleft=(x,y)
        )
        
        self.rect = pygame.Rect(
            x,
            y,
            width,
            height
        )

        self.damageCooldown = 0
        self.emitTimer = 0


    def update(self):

        if self.damageCooldown > 0:
            self.damageCooldown -= 1

    def emit(self, particleSystem):
        self.emitTimer += 1

        if self.emitTimer >= 10:
            self.emitTimer = 0

            particle = Particle(

                self.rect.centerx + random.randint(-50,50),

                self.rect.centery + random.randint(-20,20),

                (180,255,120),

                random.randint(2,4),

                (
                    random.uniform(-0.5,0.5),
                    random.uniform(-2,-0.5)
                ),

                60

            )

            particleSystem.add(particle)