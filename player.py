import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

pygame.init()


class Player(pygame.sprite.Sprite):
    def __init__(self, quillGroup, bgWidth, bgHeight=None):
        super().__init__()

        # Prickle sprite sheet
        prickleIdle = pygame.image.load(r"player_assets/prickle_idle.png").convert_alpha()
        prickleIdle = pygame.transform.scale_by(prickleIdle, 1.2)
        prickleWalk = pygame.image.load(r"player_assets/prickle_walk.png").convert_alpha()
        prickleWalk = pygame.transform.scale_by(prickleWalk, 1.2)
        prickleRun = pygame.image.load(r"player_assets/prickle_run.png").convert_alpha()
        prickleRun = pygame.transform.scale_by(prickleRun, 1.2)
        prickleAttack= pygame.image.load(r"player_assets/prickle_attack.png").convert_alpha()
        prickleAttack = pygame.transform.scale_by(prickleAttack, 1.2)
        prickleHurt= pygame.image.load(r"player_assets/prickle_hurt.png").convert_alpha()
        prickleHurt = pygame.transform.scale_by(prickleHurt, 1.2)

        self.quillGroup = quillGroup

        self.bgWidth = bgWidth

        # bgHeight is optional — scenes with a background no taller than the
        # screen (no vertical scrolling) can just omit it. When it IS taller,
        # this is what lets the camera-follow below know how much room there
        # is to scroll into.
        self.bgHeight = bgHeight if bgHeight is not None else SCREEN_HEIGHT

        self.player_hpFull = pygame.image.load(r"player_assets/player_hpFull.png").convert_alpha()
        self.player_hpFull = pygame.transform.scale_by(self.player_hpFull, 0.245)
        self.player_hpEmpty = pygame.image.load(r"player_assets/player_hpEmpty.png").convert_alpha()
        self.player_hpEmpty = pygame.transform.scale_by(self.player_hpEmpty, 0.245)

        self.ammoFull = pygame.image.load(r"player_assets/ammo_full.png").convert_alpha()
        self.ammoFull = pygame.transform.scale_by(self.ammoFull, 0.42)
        self.ammoEmpty = pygame.image.load(r"player_assets/ammo_empty.png").convert_alpha()
        self.ammoEmpty = pygame.transform.scale_by(self.ammoEmpty, 0.42)

        # Extract frames
        def extractFrames(sheet, numFrames):
            frames = []

            frameWidth = sheet.get_width() // numFrames
            frameHeight = sheet.get_height()

            for i in range(numFrames):
                frame = sheet.subsurface(pygame.Rect(i * frameWidth, 0, frameWidth, frameHeight))
                frames.append(frame)
            return frames

        prickleIdleRFrames = extractFrames (prickleIdle, 6)
        prickleIdleLFrames = [pygame.transform.flip(f, True, False) for f in prickleIdleRFrames]
        prickleWalkRFrames = extractFrames (prickleWalk, 6)
        prickleWalkLFrames = [pygame.transform.flip(f, True, False) for f in prickleWalkRFrames]
        prickleRunRFrames = extractFrames (prickleRun, 6)
        prickleRunLFrames = [pygame.transform.flip(f, True, False) for f in prickleRunRFrames]
        prickleAttackRFrames = extractFrames (prickleAttack, 1)
        prickleAttackLFrames = [pygame.transform.flip(f, True, False) for f in prickleAttackRFrames]
        prickleHurtRFrames = extractFrames (prickleHurt, 3)
        prickleHurtLFrames = [pygame.transform.flip(f, True, False) for f in prickleHurtRFrames]

        self.animations = {
            'idle'       : prickleIdleRFrames,
            'idle_left'  : prickleIdleLFrames,
            'walk_right' : prickleWalkRFrames,
            'walk_left'  : prickleWalkLFrames,
            'run_right' : prickleRunRFrames,
            'run_left'  : prickleRunLFrames,
            'attack_right': prickleAttackRFrames,
            'attack_left' : prickleAttackLFrames,
            'hurt_right': prickleHurtRFrames,
            'hurt_left' : prickleHurtLFrames
        }

        self.idleFrames = prickleIdleRFrames
        self.idleLeftFrames = prickleIdleLFrames
        self.walkingRightFrames = prickleWalkRFrames
        self.walkingLeftFrames = prickleWalkLFrames
        self.runningRightFrames = prickleRunRFrames
        self.runningLeftFrames = prickleRunLFrames
        self.attackRightFrames = prickleAttackRFrames
        self.attackLeftFrames = prickleAttackLFrames
        self.hurtRightFrames = prickleHurtRFrames
        self.hurtLeftFrames = prickleHurtLFrames
        
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

        # Passive horizontal drift — normally 0, since A/D directly set
        # position every frame. Only used for a diagonal bounce-pad launch
        # (see handlePlatforms): A/D still override it instantly, and it's
        # cleared on any normal landing so the drift only lasts the one arc.
        self.velocityX = 0

        self.onGround = True
        self.direction = 0
        self.facingRight = True

        self.controllable = True

        self.showAmmo = False
        self.showCooldown = False
        self.hasShot = False

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

        self.currentPlatform = None
        self.dropThroughPlatform = None
        self.dropThroughTimer = 0
        self.dropThroughFrames = 20  # frames to ignore a platform after dropping through it
        self.platformLandingOffset = 8

        self.maxHP = 3
        self.hp = self.maxHP

        self.isHurt = False
        self.hurtTimer = 0
        self.hurtDuration = 15

        # HP-bar hit flash — same BLEND_RGB_ADD trick as Nest's/Feathers'
        # hit-flash, but reddened rather than brightened, so the heart icons
        # themselves glow red for a moment whenever Prickle takes damage.
        # Cached per exact surface (there are only ever two: full/empty).
        self.hpFlashDuration = 20
        self.hpFlashAmount = 140
        self.spriteFlashAmount = 60  # subtler than the heart flash — just a slight red glow on Prickle himself
        self.hpFlashTimer = 0
        self._hpFlashCache = {}
        self.paralyzed = False
        self.paralyzeTimer = 0

        # Vertical camera-follow (mirrors how bgWidth bounds horizontal
        # movement). scrollY is how far the world has scrolled to keep
        # Prickle on screen; maxScrollY is how far it CAN scroll before
        # running out of background. cameraFollowY is the screen-y that,
        # once crossed, starts pulling the camera up with him — it defaults
        # to "never" (SCREEN_HEIGHT) since most scenes don't scroll; a scene
        # that wants this can set self.player.cameraFollowY after construction,
        # same way scenes already set self.player.groundY.
        self.scrollY = 0
        self.maxScrollY = max(0, self.bgHeight - SCREEN_HEIGHT)
        self.cameraFollowY = SCREEN_HEIGHT

        self.cameraX = 0
        self.cameraY = 0

        self.jump_sound = pygame.mixer.Sound(r"player_assets/jump.mp3")
        self.jump_sound.set_volume(0.4)
        self.shoot_sound = pygame.mixer.Sound(r"player_assets/quill_shoot.mp3")
        self.shoot_sound.set_volume(0.4)
        self.pickupItem_sound = pygame.mixer.Sound(r"player_assets/pickup_item.mp3")
        self.pickupItem_sound.set_volume(0.4)
        

    def update(self, keys, platforms=None):
        prevBottom = self.rect.bottom
        wasGrounded = self.onGround

        # Press S while standing on a platform to drop through it.
        if platforms and keys[pygame.K_s] and wasGrounded and self.currentPlatform is not None:
            self.dropThroughPlatform = self.currentPlatform
            self.dropThroughTimer = self.dropThroughFrames
            self.currentPlatform = None

        if self.controllable:
            self.move(keys)

        if platforms:
            self.handlePlatforms(platforms, prevBottom, wasGrounded)

        if self.dropThroughTimer > 0:
            self.dropThroughTimer -= 1
            if self.dropThroughTimer == 0:
                self.dropThroughPlatform = None

        self.updateCamera()

        self.handleAmmo()
        self.handleAttack()

        if self.isHurt:
            self.hurtTimer -= 1
            if self.hurtTimer <= 0:
                self.isHurt = False

        if self.hpFlashTimer > 0:
            self.hpFlashTimer -= 1
        if self.paralyzed:
            self.paralyzeTimer -= 1
            if self.paralyzeTimer <= 0:
                self.paralyzed = False

        self.animate(keys)

    def updateCamera(self):
        # How far above the follow-line Prickle is trying to be (positive =
        # above it). That overshoot gets absorbed into scrollY (shifting the
        # world down instead of him up) — but only up to however much
        # background is left to scroll. Once scrollY hits maxScrollY there's
        # no more room to absorb, so any further climb has to actually raise
        # him further up the screen instead of being silently discarded
        # (discarding it is what caused the "invisible ceiling" bug — he'd
        # get snapped back to cameraFollowY every frame forever once the
        # background was fully scrolled). Symmetric on the way down too: as
        # he descends back below the line, scroll credit is given back the
        # same way, and once scrollY hits 0 he's free to actually drop below
        # the line on screen.
        overshoot = self.cameraFollowY - self.rect.top

        if overshoot > 0:
            consumed = min(overshoot, self.maxScrollY - self.scrollY)
        else:
            consumed = max(overshoot, -self.scrollY)

        self.scrollY += consumed
        self.rect.top += consumed

    def handlePlatforms(self, platforms, prevBottom, wasGrounded):
        if self.velocityY < 0:
            self.currentPlatform = None
            return

        # If we were grounded last frame, check if we're still on the same platform.
        if wasGrounded and self.currentPlatform is not None:
            platform = self.currentPlatform
            if self.rect.colliderect(platform.rect):
                surfaceY = platform.topAt(self.rect.centerx)
                if surfaceY is not None:
                    self.rect.bottom = surfaceY + self.platformLandingOffset
                    self.velocityY = 0
                    self.velocityX = 0
                    self.onGround = True
                    
                    # RIDE LOGIC: Move with the platform if it is moving
                    if hasattr(platform, 'movementDeltaX'):
                        self.rect.x += platform.movementDeltaX
                        self.rect.y += platform.movementDeltaY
                    return
            self.currentPlatform = None

        # Check for landing on any platform.
        bestPlatform = None
        bestLandY = None

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

            if landingFromAbove and (bestLandY is None or landY < bestLandY):
                bestPlatform = platform
                bestLandY = landY

        if bestPlatform is not None:
            bounceVY = getattr(bestPlatform, "bounceVY", None)

            if bounceVY is not None:
                # Bounce pad (e.g. Mushroom)
                self.rect.bottom = bestLandY
                self.velocityY = bounceVY
                self.velocityX = getattr(bestPlatform, "bounceVX", 0)
                self.onGround = False
                self.currentPlatform = None
                if hasattr(bestPlatform, "trigger"):
                    bestPlatform.trigger()
            else:
                self.rect.bottom = bestLandY
                self.velocityY = 0
                self.velocityX = 0
                self.onGround = True
                self.currentPlatform = bestPlatform
                
                # RIDE LOGIC: Move with the platform on the frame we land
                if hasattr(bestPlatform, 'movementDeltaX'):
                    self.rect.x += bestPlatform.movementDeltaX
                    self.rect.y += bestPlatform.movementDeltaY

            return

        self.currentPlatform = None

    def move(self, keys):
        self.isRunning = keys[pygame.K_LSHIFT]
        self.speed = 8 if self.isRunning else 5

        if not self.paralyzed:
            if keys[pygame.K_a]:
                self.rect.x -= self.speed
                self.velocityX = 0  # manual input always overrides bounce drift
                self.direction = -1
                self.facingRight = False

            elif keys[pygame.K_d]:
                self.rect.x += self.speed
                self.velocityX = 0
                self.direction = 1
                self.facingRight = True

            else:
                self.direction = 0
                if self.velocityX:
                    self.rect.x += self.velocityX

            # Keep Prickle inside the screen horizontally
            if self.rect.left < 0:
                self.rect.left = 0
                self.velocityX = 0
            elif self.rect.right > self.bgWidth:
                self.rect.right = self.bgWidth
                self.velocityX = 0

            if keys[pygame.K_SPACE] and self.onGround:
                self.velocityY = -15
                self.onGround = False
                self.jump_sound.play()

            # Apply gravity
            self.velocityY += 0.87
            self.rect.y += self.velocityY

            if self.rect.bottom >= self.groundY:
                self.rect.bottom = self.groundY
                self.velocityY = 0
                self.velocityX = 0
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
            self.shoot_sound.play()
            self.shoot()
            self.ammo -= 1

            if not self.hasShot:
                self.hasShot = True
                self.showAmmo = True

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
        mouseX, mouseY = pygame.mouse.get_pos()

        # camera correction
        mouseX += self.cameraX

        quill = Quill(self.rect.centerx,self.rect.centery,mouseX,mouseY)
        self.quillGroup.add(quill)

    def drawAmmo(self, screen):
        if not self.showAmmo:
            return

        ammoX = 30
        ammoY = 63
        spacing = 48

        for i in range(self.maxAmmo):
            if i < self.ammo:
                image = self.ammoFull
            else:
                image = self.ammoEmpty

            screen.blit(image,(ammoX + i * spacing, ammoY))

    def _redFlashFrame(self, image, amount):
        key = (id(image), amount)
        flashed = self._hpFlashCache.get(key)
        if flashed is None:
            flashed = image.copy()
            flashed.fill((amount, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
            self._hpFlashCache[key] = flashed
        return flashed

    def drawHP(self,screen):
        hpX = 20
        hpY = 10
        spacing = 58

        for i in range(self.maxHP):
            if i < self.hp:
                image = self.player_hpFull
            else:
                image = self.player_hpEmpty

            if self.hpFlashTimer > 0:
                image = self._redFlashFrame(image, self.hpFlashAmount)

            screen.blit(image, (hpX + i * spacing, hpY))

    def takeDamage(self, damage):
        self.hp -= damage
        self.hpFlashTimer = self.hpFlashDuration

        if self.hp <= 0:
            self.hp = 0
            print("Player Dead")

    def applyParalysis(self, duration):
        if not self.paralyzed:
            self.paralyzed = True
            self.paralyzeTimer = duration

    def animate(self, keys):
        if self.direction == 1:
            newFrames = self.runningRightFrames if self.isRunning else self.walkingRightFrames

        elif self.direction == -1:
            newFrames = self.runningLeftFrames if self.isRunning else self.walkingLeftFrames

        else:
            newFrames = self.idleFrames if self.facingRight else self.idleLeftFrames

        if self.isHurt:
            newFrames = self.hurtRightFrames if self.facingRight else self.hurtLeftFrames
        elif self.direction == 1:
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

        # Same hit-flash that reddens the HP hearts, applied to Prickle's
        # own sprite too — just a slight tint (spriteFlashAmount is much
        # lower than hpFlashAmount) so he visibly reacts to damage without
        # looking like a completely different color.
        if self.hpFlashTimer > 0:
            self.image = self._redFlashFrame(self.image, self.spriteFlashAmount)


class Quill(pygame.sprite.Sprite):
    def __init__(self, x, y, targetX, targetY):
        super().__init__()

        self.image = pygame.image.load(r"player_assets/quill.png" ).convert_alpha()
        self.image = pygame.transform.scale(self.image,(50,20))

        # Starting position
        self.x = float(x)
        self.y = float(y)
        self.startX = float(x)
        self.startY = float(y)

        # Maximum shooting range
        self.maxRange = 500

        self.rect = self.image.get_rect(center=(x,y))

        # Calculate shooting direction
        dx = targetX - x
        dy = targetY - y
        distance = max((dx*dx + dy*dy) ** 0.5,1)

        speed = 12

        self.velocityX = (dx / distance) * speed
        self.velocityY = (dy / distance) * speed

        # Rotate quill
        angle = pygame.math.Vector2(dx, dy).angle_to(pygame.math.Vector2(1,0))

        self.image = pygame.transform.rotate(    self.image,angle )

        self.rect = self.image.get_rect(center=(x,y))

    def update(self):
        # move position
        self.x += self.velocityX
        self.y += self.velocityY

        # update image position
        self.rect.center = (int(self.x),int(self.y))

        # Calculate distance travelled
        distance = ((self.x - self.startX) ** 2 +(self.y - self.startY) ** 2) ** 0.5

        # Remove after exceeding range
        if distance >= self.maxRange:
            self.kill()
            
        # remove after leaving world
        if (self.x < -100 or self.x > 5000 or self.y < -100 or self.y > 2000):
            self.kill()