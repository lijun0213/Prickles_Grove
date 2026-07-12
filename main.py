# Entry point of the game
# Runs the game loop and switches between scenes
# --------------------------------------------------------------


import pygame
import sys
from settings import *
from scene1 import Scene1
from scene3 import Scene3

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
 
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock  = pygame.time.Clock()

        self.current_scene = 0  # 0 = main menu, 1-4 = scenes
        self.running = True

        self.blink_timer = 0
        self.blink_show  = True
 
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
 
                if event.key == pygame.K_SPACE:
                    if self.current_scene == 0 :
                        self.current_scene = 3
                        self.scene = Scene3()

    # Update game logic
    def update(self):
        self.blink_timer += 1
        if self.blink_timer >= 30:  # every 30 frames = 0.5 seconds
            self.blink_show  = not self.blink_show  # flip on/off
            self.blink_timer = 0

        if self.current_scene != 0:
            self.scene.update()

    # Draw everything to screen
    def draw(self):
        self.screen.fill(BLACK)

        if self.current_scene == 0:
            self.draw_main_menu()
        elif self.current_scene != 0 and self.scene:
            self.scene.draw(self.screen)
 
        pygame.display.flip()

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