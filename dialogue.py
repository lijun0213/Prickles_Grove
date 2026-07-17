import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW

# Reusable dialogue/callout textbox, meant to be shared by every scene
# instead of each one reimplementing its own popup system. This started
# life as Scene1's popupLines/popupSpeaker/popupNext/... setup — same
# visuals and behavior, generalized so any scene can drop it in.
#
# Usage pattern (mirrors how Scene1 used to freeze itself while its old
# self.showPopup was True):
#
#   self.dialogue = Dialogue()
#   ...
#   self.dialogue.show(
#       ["Wait... something's there!"],
#       portrait=self.portraits["prickle"], name="Prickle",
#       onDismiss=lambda: setattr(self, "state", "ESCAPE"),
#   )
#   ...
#   def update(self):
#       keys = pygame.key.get_pressed()
#       if self.dialogue.active:
#           self.dialogue.update(keys)
#           return
#       ... rest of the scene's normal update ...
#
#   def draw(self, screen):
#       ... rest of the scene's normal draw ...
#       self.dialogue.draw(screen)   # last, so it overlays everything


class Dialogue:
    """A reusable dialogue/callout textbox.

    Two visual styles:
      "center"  - full-width box anchored to the bottom of the screen, with
                  an optional portrait + name plate on the left (this was
                  Scene1's old "center" style).
      "callout" - small corner box with no portrait, for brief non-blocking
                  tips (this was Scene1's old "ammo" style).

    A scene is expected to freeze its own update logic while
    `dialogue.active` is True (same early-return pattern Scene1 already
    used) — this class only owns the box itself, not the rest of the
    scene, since it has no idea what a Player or an enemy Group is.
    """

    def __init__(self, dismissKeys=(pygame.K_f,)):
        self.dismissKeys = dismissKeys

        self.active = False
        self.lines = []
        self.portrait = None
        self.name = None
        self.style = "center"
        self.onDismiss = None

        self._keyWasDown = False

    def show(self, lines, portrait=None, name=None, style="center", onDismiss=None):
        """Open the textbox.

        lines: list[str] of dialogue lines.
        portrait: optional pre-scaled Surface shown in a plate on the left
            (only drawn in "center" style).
        name: optional label rendered under the portrait.
        style: "center" or "callout".
        onDismiss: optional zero-arg callable invoked the instant the box
            closes — this is how a scene hooks its own state machine back
            up, e.g. `onDismiss=lambda: setattr(self, "state", "CHASE")`.
        """
        self.lines = lines
        self.portrait = portrait
        self.name = name
        self.style = style
        self.onDismiss = onDismiss
        self.active = True

        # Pretend the dismiss key was already down the instant this opens,
        # so a key that's incidentally held right when the popup triggers
        # (e.g. Prickle already holding SPACE to jump) can't insta-dismiss
        # it on the very same frame — only a fresh press afterward counts.
        self._keyWasDown = True

    def update(self, keys):
        if not self.active:
            return

        keyDown = any(keys[k] for k in self.dismissKeys)
        justPressed = keyDown and not self._keyWasDown
        self._keyWasDown = keyDown

        if justPressed:
            self.active = False
            callback = self.onDismiss
            self.onDismiss = None
            if callback:
                callback()

    def draw(self, screen):
        if not self.active:
            return

        if self.style == "callout":
            self._drawCallout(screen)
        else:
            self._drawCenter(screen)

    def _drawCenter(self, screen):
        boxWidth, boxHeight = 580, 140
        boxX = SCREEN_WIDTH // 2 - boxWidth // 2
        boxY = SCREEN_HEIGHT - boxHeight - 20

        box = pygame.Surface((boxWidth, boxHeight), pygame.SRCALPHA)
        box.fill((20, 20, 20, 210))
        screen.blit(box, (boxX, boxY))
        pygame.draw.rect(screen, WHITE, (boxX, boxY, boxWidth, boxHeight), width=2, border_radius=8)

        font = pygame.font.SysFont("Arial", 18)
        smallFont = pygame.font.SysFont("Arial", 14)
        nameFont = pygame.font.SysFont("Arial", 15, bold=True)

        textX = boxX + 20
        textStartY = boxY + 20

        if self.portrait:
            plateSize = 90
            plateX = boxX + 16
            plateY = boxY + 16

            plate = pygame.Surface((plateSize, plateSize), pygame.SRCALPHA)
            plate.fill((10, 10, 10, 230))
            screen.blit(plate, (plateX, plateY))
            pygame.draw.rect(screen, YELLOW, (plateX, plateY, plateSize, plateSize), width=2, border_radius=6)

            portraitRect = self.portrait.get_rect(center=(plateX + plateSize // 2, plateY + plateSize // 2))
            screen.blit(self.portrait, portraitRect)

            if self.name:
                nameLabel = nameFont.render(self.name, True, YELLOW)
                nameRect = nameLabel.get_rect(centerx=plateX + plateSize // 2, top=plateY + plateSize + 4)
                screen.blit(nameLabel, nameRect)

            textX = plateX + plateSize + 20

        for i, line in enumerate(self.lines):
            label = font.render(line, True, WHITE)
            screen.blit(label, (textX, textStartY + i * 26))

        hint = smallFont.render("Press F to continue", True, YELLOW)
        screen.blit(hint, (textX, boxY + boxHeight - 26))

    def _drawCallout(self, screen):
        boxWidth, boxHeight = 260, 80
        boxX = 250
        boxY = 60

        box = pygame.Surface((boxWidth, boxHeight), pygame.SRCALPHA)
        box.fill((20, 20, 20, 220))
        screen.blit(box, (boxX, boxY))
        pygame.draw.rect(screen, WHITE, (boxX, boxY, boxWidth, boxHeight), width=2, border_radius=8)

        font = pygame.font.SysFont("Arial", 15)
        smallFont = pygame.font.SysFont("Arial", 12)

        for i, line in enumerate(self.lines):
            label = font.render(line, True, WHITE)
            screen.blit(label, (boxX + 12, boxY + 10 + i * 20))

        hint = smallFont.render("F to continue", True, YELLOW)
        screen.blit(hint, (boxX + 12, boxY + boxHeight - 18))
