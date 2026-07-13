import pygame


class Platform(pygame.sprite.Sprite):
    """A branch (or similar) Prickle can jump onto to climb higher.

    Collision follows the actual drawn shape of the image (not its full
    rectangular bounds) — for each column of pixels we record the y of the
    topmost non-transparent pixel, so landing on a diagonal/irregular branch
    feels like landing on the branch itself, not an invisible box around it.
    """

    def __init__(self, imagePath, x, y, angle=0, scale=1.0):
        super().__init__()
        self.image = pygame.image.load(imagePath).convert_alpha()

        # scale: multiplier on the original image size (1.0 = unchanged,
        # 2.0 = double, 0.5 = half). Uses a crisp (non-smoothed) resize so
        # pixel art doesn't get blurred.
        self.scale = scale
        if scale != 1.0:
            self.image = pygame.transform.scale_by(self.image, scale)

        # angle in degrees, counter-clockwise (pygame.transform.rotate convention).
        # Rotating grows the image's bounding box (pygame pads the corners with
        # transparency), so (x, y) below is the top-left of the ROTATED image,
        # not the original — reposition after rotating if it looks off.
        self.angle = angle
        if angle:
            self.image = pygame.transform.rotate(self.image, angle)

        self.rect = self.image.get_rect(topleft=(x, y))

        # Mask/height-map are built from the final (post-scale, post-rotation)
        # image, so collision always follows whatever is actually drawn on screen.
        mask = pygame.mask.from_surface(self.image)
        width, height = self.image.get_size()

        # surfaceY[col] = local y of the topmost opaque pixel in that column,
        # or None if the column is fully transparent (a gap in the shape).
        self.surfaceY = []
        for col in range(width):
            colY = None
            for row in range(height):
                if mask.get_at((col, row)):
                    colY = row
                    break
            self.surfaceY.append(colY)

    def topAt(self, worldX):
        """World-space y of the branch surface under worldX, or None if
        there's no branch pixel there (off the image, or a transparent gap)."""
        col = int(worldX - self.rect.x)
        if col < 0 or col >= len(self.surfaceY):
            return None
        localY = self.surfaceY[col]
        if localY is None:
            return None
        return self.rect.y + localY

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Wall:
    """An invisible vertical barrier that blocks horizontal movement —
    a level boundary, a fence, gating progress until something happens, etc.
    Draws nothing; it's purely a collision line at x spanning [top, bottom]."""

    def __init__(self, x, top, bottom):
        self.x = x
        self.rect = pygame.Rect(x, top, 1, bottom - top)

    def draw(self, screen):
        pass
