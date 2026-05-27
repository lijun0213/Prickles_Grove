# Entry point of the game
# Runs the game loop and switches between scenes
# --------------------------------------------------------------


import pygame
import sys
from settings import *

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
 
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock  = pygame.time.Clock()
 
        self.current_scene = 0  # 0 = main menu, 1-4 = scenes
        self.running = True
 
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
 
                # Press SPACE to go to next scene (temporary for testing)
                if event.key == pygame.K_SPACE:
                    self.current_scene += 1
                    if self.current_scene > 4:
                        self.current_scene = 0

    # Update game logic
    def update(self):
        pass

    # Main Menu screen


# START GAME
if __name__ == "__main__":
    game = Game()
    game.run()