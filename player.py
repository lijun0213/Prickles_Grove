import pygame

pygame.init()


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        # Prickle sprite sheet
        prickleIdle = pygame.image.load(r"assets/idle.png").convert_alpha()
        prickleIdle = pygame.transform.scale_by(prickleIdle, 5.0)
        prickleWalk = pygame.image.load(r"assets/walk.png").convert_alpha()
        prickleWalk = pygame.transform.scale_by(prickleWalk, 5.0)
        prickleSleep = pygame.image.load(r"assets/sleep.png").convert_alpha()
        prickleSleep = pygame.transform.scale_by(prickleSleep, 5.0)
        prickleAngry = pygame.image.load(r"assets/angry.png").convert_alpha()
        prickleAngry = pygame.transform.scale_by(prickleAngry, 5.0)

        # Extract frames
        def extractFrames(sheet, numFrames):
            frames = []

            frameWidth = sheet.get_width() // numFrames
            frameHeight = sheet.get_height()

            for i in range(numFrames):
                frame = sheet.subsurface(pygame.Rect(i * frameWidth, 0, frameWidth, frameHeight))
                frames.append(frame)
            return frames

        prickleIdleFrames = extractFrames (prickleIdle, 2)
        prickleWalkRFrames = extractFrames (prickleWalk, 6)
        prickleWalkLFrames = [pygame.transform.flip(f, True, False) for f in prickleWalkRFrames]
        prickleSleepFrames = extractFrames (prickleSleep, 3)
        prickleAngryRFrames = extractFrames (prickleAngry, 1)
        prickleAngryLFrames = [pygame.transform.flip(f, True, False) for f in prickleAngryRFrames]

        self.animations = {
            'idle'       : prickleIdleFrames,
            'walk_right' : prickleWalkRFrames,
            'walk_left'  : prickleWalkLFrames,
            'sleep'      : prickleSleepFrames,
            'angry_right': prickleAngryRFrames,
            'angry_left' : prickleAngryLFrames
        }

        self.defaultFrames = prickleIdleFrames
        self.walkingRightFrames = prickleWalkRFrames
        self.walkingLeftFrames = prickleWalkLFrames
        self.sleepingFrames = prickleSleepFrames
        self.angryRightFrames = prickleAngryRFrames
        self.angryLeftFrames = prickleAngryLFrames

        # animation
        self.currentFrames = self.defaultFrames
        self.animIndex = 0 
        self.animTimer = 0
        self.animSpeed = 12

        self.image = self.defaultFrames[0]
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.rect.y = 300

        self.velocityY = 0
        self.onGround = True
        self.direction = 0
        self.facingRight = True

    def update(self, keys):
        self.move(keys) 
        self.animate(keys)

    def move(self, keys):
        self.isAngry = keys[pygame.K_TAB]

        if keys[pygame.K_LEFT]:
            self.rect.x -= 5
            self.direction = -1
            self.facingRight = False

        elif keys[pygame.K_RIGHT]:
            self.rect.x += 5
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

        # --- ADD THIS FLOOR CHECK ---
        # Adjust 300 to match wherever your game's floor level actually is
        if self.rect.y >= 300:
            self.rect.y = 300
            self.velocityY = 0
            self.onGround = True

    def animate(self, keys):
        if self.direction == 1:
            newFrames = self.walkingRightFrames

        elif self.direction == -1:
            newFrames = self.walkingLeftFrames

        else:
            newFrames = self.defaultFrames

        if keys[pygame.K_TAB]:
            newFrames = self.angryRightFrames if self.facingRight else self.angryLeftFrames    

        if newFrames != self.currentFrames:
            self.currentFrames = newFrames
            self.animIndex = 0
            self.animTimer = 0

        self.animTimer += 1

        if self.animTimer >= self.animSpeed:
            self.animTimer = 0
            self.animIndex = (self.animIndex + 1) % len(self.currentFrames)

        self.image = self.currentFrames[self.animIndex]