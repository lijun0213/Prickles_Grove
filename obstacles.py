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

        self.scale = scale
        if scale != 1.0:
            self.image = pygame.transform.scale_by(self.image, scale)

        self.angle = angle
        if angle:
            self.image = pygame.transform.rotate(self.image, angle)

        self.rect = self.image.get_rect(topleft=(x, y))

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
        col = int(worldX - self.rect.x)
        if col < 0 or col >= len(self.surfaceY):
            return None
        localY = self.surfaceY[col]
        if localY is None:
            return None
        return self.rect.y + localY

    def draw(self, screen):
        screen.blit(self.image, self.rect)


#Invisible vertical wall, prevent players from leaving game area.
class Wall:
    def __init__(self, x, top, bottom):
        self.x = x
        self.rect = pygame.Rect(x, top, 1, bottom - top)

    def draw(self, screen):
        pass
