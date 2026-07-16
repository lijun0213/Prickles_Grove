import math
import pygame


class Platform(pygame.sprite.Sprite):
    """A branch (or similar) Prickle can jump onto to climb higher.

    Collision follows the actual drawn shape of the image (not its full
    rectangular bounds) — for each column of pixels we record the y of the
    topmost non-transparent pixel, so landing on a diagonal/irregular branch
    feels like landing on the branch itself, not an invisible box around it.
    """

    def __init__(self, imagePath, x, y, angle=0, scale=1.0, blocksBullets=False):
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
        screen.blit(self.image, self.rect)

    def update(self):
        pass


def _sliceFramesByGaps(sheet):
    """Split a sprite sheet into frames using its own transparent gaps,
    instead of assuming every frame is the same fixed width. Needed for
    sheets like the bouncy mushroom's, where the squash frame is wider than
    the others so an even division would cut frames in half."""
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

        # Slice into individual frames BEFORE rotating. The sheet is a
        # horizontal strip of frames separated by thin transparent gaps —
        # rotating the whole strip first smears those frames diagonally into
        # each other, so the gap-detection merges two adjacent frames into
        # one "slice" (visually showing two overlapping mushrooms). Rotating
        # each frame individually after slicing avoids that entirely.
        self.frames = _sliceFramesByGaps(sheet)

        # angle in degrees, counter-clockwise (same convention as Platform's
        # angle / pygame.transform.rotate) — rotates the cap visually AND
        # tilts the bounce direction to match, so a tilted mushroom launches
        # Prickle diagonally instead of straight up.
        self.angle = angle
        if angle:
            self.frames = [pygame.transform.rotate(f, angle) for f in self.frames]

        self.restFrame = 0
        self.frameDelay = frameDelay  # game-frames each animation frame holds

        self.image = self.frames[self.restFrame]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.baseY = self.rect.y

        self.bounceForce = bounceForce

        # "Up" (0, -1) rotated by angle degrees, counter-clockwise, matching
        # pygame.transform.rotate's convention on screen (y grows downward).
        # angle=0 keeps the old straight-up bounce (bounceVX=0).
        rad = math.radians(angle)
        self.bounceVX = bounceForce * -math.sin(rad)
        self.bounceVY = bounceForce * -math.cos(rad)

        self.bouncing = False
        self.animIndex = 0
        self.animTimer = 0

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
        # Frames have different widths/heights (independently cropped), so
        # anchor by midbottom each draw instead of blitting at self.rect
        # directly — otherwise wider/taller frames would appear to shift.
        drawRect = self.image.get_rect(midbottom=self.rect.midbottom)
        screen.blit(self.image, drawRect)


#Bird nest — a bullet target, not a physical obstacle. Prickle passes
#through it freely; only Prickle's bullets interact with it.
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

        # Brief brightness flash on hit — a lightweight visual "ouch" cue
        # separate from the persistent damage-frame change. flashAmount is
        # how much brighter (0-255ish) each RGB channel gets; flashFrames is
        # how many game-frames the flash lasts before fading back to normal.
        self.flashFrames = flashFrames
        self.flashAmount = flashAmount
        self.flashTimer = 0
        self._brightCache = {}  # frameIndex -> pre-brightened surface

        self.image = self.frames[self.frameIndex]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.baseY = self.rect.y  # see Platform.baseY

    def _brightFrame(self, frameIndex):
        bright = self._brightCache.get(frameIndex)
        if bright is None:
            bright = self.frames[frameIndex].copy()
            amount = self.flashAmount
            # BLEND_RGB_ADD only touches RGB, leaving per-pixel alpha (and so
            # the shape's transparency) untouched.
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