# Entry point of the game
# Runs the game loop and switches between scenes
# --------------------------------------------------------------


import pygame
import sys
from settings import *
from scene1 import Scene1
from scene3 import Scene3
from scene0 import Scene0

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        pygame.mixer.init()
 
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock  = pygame.time.Clock()

        # Crosshair cursor, since aiming is mouse-based (fits the quill-shooting).
        try:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
        except pygame.error:
            pass  # some environments (e.g. headless) don't support system cursors

        self.current_scene = 0  # 0 = main menu, 1-4 = scenes
        self.scene = None
        self.running = True

        self.blink_timer = 0
        self.blink_show  = True

        # Debug: shows the mouse's current pixel coordinate on screen.
        # Handy for reading off x/y values when placing platforms etc.
        # Toggle with F1.
        self.showDebugCoords = True
        self.debugFont = pygame.font.SysFont("Consolas", 16)

    # Main loop
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
 
        pygame.quit()
        sys.exit()

    # Handle input events
    def handle_events(self):
        for event in pygame.event.get():
 
            # Close window
            if event.type == pygame.QUIT:
                self.running = False
 
            # Press ESCAPE to quit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == pygame.K_F1:
                    self.showDebugCoords = not self.showDebugCoords

                if event.key == pygame.K_SPACE:
                    if self.current_scene == 0 :
                        self.current_scene = 1
                        self.scene = Scene1()
                

    # Update game logic
    def update(self):
        self.blink_timer += 1
        if self.blink_timer >= 30:  # every 30 frames = 0.5 seconds
            self.blink_show  = not self.blink_show  # flip on/off
            self.blink_timer = 0

        if self.current_scene != 0:
            self.scene.update()
            if self.current_scene == 1:
                if self.scene.levelComplete:
                    self.current_scene = 3
                    self.scene = Scene3()

    # Draw everything to screen
    def draw(self):
        self.screen.fill(BLACK)

        if self.current_scene == 0:
            self.draw_main_menu()
        elif self.current_scene != 0 and self.scene:
            self.scene.draw(self.screen)

        if self.showDebugCoords:
            self.draw_debug_coords()
            self.draw_debug_keys()
            self.draw_debug_anim()

        pygame.display.flip()

    # Shows "(x, y)" next to the cursor — read pixel coordinates straight
    # off the screen when placing platforms/obstacles. Toggle with F1.
    def draw_debug_coords(self):
        mouseX, mouseY = pygame.mouse.get_pos()
        label = self.debugFont.render(f"({mouseX}, {mouseY})", True, WHITE, BLACK)

        labelX = mouseX + 14
        labelY = mouseY + 14
        # Keep the label on-screen if the cursor is near the right/bottom edge
        if labelX + label.get_width() > SCREEN_WIDTH:
            labelX = mouseX - 14 - label.get_width()
        if labelY + label.get_height() > SCREEN_HEIGHT:
            labelY = mouseY - 14 - label.get_height()

        self.screen.blit(label, (labelX, labelY))

    # Live readout of whether pygame itself currently sees A/D/SPACE/SHIFT
    # as held down — pinned to the top-left corner. Toggle with F1 (same
    # flag as the mouse coords). This is here to pin down the "movement
    # sometimes stops working" bug: if this readout shows False while a key
    # is physically being held, pygame/Windows never delivered the keypress
    # to the game at all (an OS/driver/focus issue, not a bug in this code).
    # If it shows True and Prickle still doesn't move, that means the game
    # DID see the key and the bug is in the movement code after all.
    def draw_debug_keys(self):
        keys = pygame.key.get_pressed()
        states = [
            ("A", keys[pygame.K_a]),
            ("D", keys[pygame.K_d]),
            ("SPACE", keys[pygame.K_SPACE]),
            ("SHIFT", keys[pygame.K_LSHIFT]),
        ]
        text = "  ".join(f"{name}:{held}" for name, held in states)
        label = self.debugFont.render(text, True, WHITE, BLACK)
        self.screen.blit(label, (10, 10))

    # Live readout of Prickle's animation state — which frame set is
    # currently playing (by name, matched against the player's known frame
    # lists) and which frame index within it. Pinned just below the key
    # readout. Toggle with F1. Use this to tell apart "the sprite really is
    # stuck on one frame" (animIndex never changes / frame set never
    # switches to RUN_LEFT) from "it's animating but the poses just look
    # similar" (animIndex keeps advancing normally).
    def draw_debug_anim(self):
        if not self.scene or not hasattr(self.scene, "player"):
            return

        player = self.scene.player
        namedSets = [
            ("IDLE_R", player.idleFrames),
            ("IDLE_L", player.idleLeftFrames),
            ("WALK_R", player.walkingRightFrames),
            ("WALK_L", player.walkingLeftFrames),
            ("RUN_R", player.runningRightFrames),
            ("RUN_L", player.runningLeftFrames),
            ("ATTACK_R", player.attackRightFrames),
            ("ATTACK_L", player.attackLeftFrames),
            ("HURT_R", player.hurtRightFrames),
            ("HURT_L", player.hurtLeftFrames),
        ]
        setName = next((name for name, frames in namedSets if frames is player.currentFrames), "?")

        text = (f"anim:{setName}  frame:{player.animIndex}/{len(player.currentFrames)}  "
                f"dir:{player.direction}  running:{player.isRunning}")
        label = self.debugFont.render(text, True, WHITE, BLACK)
        self.screen.blit(label, (10, 30))

    # Main Menu screen
    def draw_main_menu(self):
        # bg = pygame.image.load("")
        # bg = pygame.transform.scale(bg, (800, 500))
        # self.screen.blit(bg, (0, 0))

        font_big   = pygame.font.SysFont("Arial", 48, bold=True)
        font_small = pygame.font.SysFont("Arial", 20)
 
        # Title
        title = font_big.render("Prickle's Grove", True, WHITE)
        self.screen.blit(title, (
            SCREEN_WIDTH  // 2 - title.get_width()  // 2,
            SCREEN_HEIGHT // 2 - 80
        ))
 
        # Subtitle
        if self.blink_show:
            msg = font_small.render("PRESS SPACE TO START", True, WHITE)
            self.screen.blit(msg, (
                SCREEN_WIDTH  // 2 - msg.get_width()  // 2,
                SCREEN_HEIGHT // 2
            ))        

        # Controls hint
        hint = font_small.render("ESC = quit", True, WHITE)
        self.screen.blit(hint, (10, SCREEN_HEIGHT - 30))

    def draw_placeholder(self, scene_num):
        colours = {
            1: (0, 0, 0),
            2: (0, 0, 0),   
            3: (0, 0, 0),   
            4: (0, 0, 0), 
        }
        names = {
            1: "Scene 1 — Prickle's Home     (Lew Li Jun)",
            2: "Scene 2 — Mushroom Meadow    (Tan Zheng Da)",
            3: "Scene 3 — Thorned Canopy     (Tai Zhen Zhou)",
            4: "Scene 4 — Petal Plains       (Wu Xiaoen)",
        }
 
        self.screen.fill(colours.get(scene_num, BLACK))
 
        font = pygame.font.SysFont("Arial", 24, bold=True)
        font_small = pygame.font.SysFont("Arial", 18)
 
        # Scene name
        label = font.render(names.get(scene_num, ""), True, WHITE)
        self.screen.blit(label, (
            SCREEN_WIDTH  // 2 - label.get_width()  // 2,
            SCREEN_HEIGHT // 2 - 40
        ))
 
        # Navigation hint
        hint = font_small.render("SPACE = next scene    ESC = quit", True, WHITE)
        self.screen.blit(hint, (
            SCREEN_WIDTH  // 2 - hint.get_width()  // 2,
            SCREEN_HEIGHT // 2 + 10
        ))


# START GAME
if __name__ == "__main__":
    game = Game()
    game.run()