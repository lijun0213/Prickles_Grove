import pygame

pygame.init()

# Prickle sprite sheet
prickleSprite = pygame.image.load("assets/images/prickle/hedgehog.png").convert_alpha()
prickleSprite = pygame.transform.scale_by(prickleSprite, 0.5)

spriteSheetWidth = prickleSprite.get_width()
spriteSheetHeight = prickleSprite.get_height()

numFrames = 4
prickleFrameWidth = spriteSheetWidth // numFrames
prickleFrameHeight = spriteSheetHeight // 4

# Extract frames
def extractFrames(sheet, row, numFrames):
    frames = []

    for i in range(numFrames):
        frame = sheet.subsurface(pygame.Rect(i * prickleFrameWidth, row * prickleFrameHeight, prickleFrameWidth, prickleFrameWidth))
        frames.append(frame)
    return frames

prickleIdleFrames = extractFrames (prickleSprite, 0, 2)
prickleWalkRFrames = extractFrames (prickleSprite, 1, 6)
prickleWalkLFrames = [pygame.transform.flip(f, True, False) for f in prickleWalkRFrames]
prickleSleepFrames = extractFrames (prickleSprite, 2, 4)
prickleJumpRFrames = extractFrames (prickleSprite, 3, 3)
prickleJumpLFrames = [pygame.transform.flip(f, True, False) for f in prickleJumpRFrames]


animations = {
    'idle'       : prickleIdleFrames,
    'walk_right' : prickleWalkRFrames,
    'walk_left'  : prickleWalkLFrames,
    'sleep'      : prickleSleepFrames,
    'jump_right' : prickleJumpRFrames,
    'jump_left'  : prickleJumpLFrames,

}

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        self.defaultFrames = prickleIdleFrames
        self.walkingRightFrames = prickleWalkRFrames
        self.walkingLeftFrames = prickleWalkLFrames
        self.sleepingFrames = prickleSleepFrames
        self.jumpingRightFrames = prickleJumpRFrames
        self.jumpingLeftFrames = prickleJumpLFrames

        # animation speed


        self.image = self.defaultFrames
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.rect.y = 300

        self.direction = 0
        self.facingRight = True