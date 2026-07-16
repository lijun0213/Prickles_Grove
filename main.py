# Entry point of the game
# Runs the game loop and switches between scenes
# --------------------------------------------------------------

import pygame
import sys
from settings import *
from scene0 import Scene0
from scene1 import Scene1
from scene3 import Scene3
from scene4 import Scene4

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        pygame.mixer.init()
 
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock  = pygame.time.Clock()

        try:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
        except pygame.error:
            pass  

        self.current_scene = 0  # 0 = main menu, 1-4 = scenes
        self.scene = None
        self.running = True

        self.blink_timer = 0
        self.blink_show  = True

        # Debug variables
        self.showDebugCoords = True
        self.debugFont = pygame.font.SysFont("Consolas", 16)

        # --- Added Game Over Tracking Properties ---
        self.game_over = False
        self.death_timer = 0
        self.death_duration = 120
        self.selected_option = 0  # 0 = Retry, 1 = Quit

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
 
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
 
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == pygame.K_F1:
                    self.showDebugCoords = not self.showDebugCoords

                # --- Game Over Menu Navigation ---
                if self.game_over:
                    if event.key in (pygame.K_a, pygame.K_LEFT, pygame.K_w, pygame.K_UP):
                        self.selected_option = 0
                    if event.key in (pygame.K_d, pygame.K_RIGHT, pygame.K_s, pygame.K_DOWN):
                        self.selected_option = 1
                    
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        if self.selected_option == 0:  # Retry
                            self.game_over = False
                            self.scene = Scene4()  # Hard reset scene instance
                        elif self.selected_option == 1:  # Quit to Main Menu
                            self.game_over = False
                            self.current_scene = 0
                            self.scene = None
                    return  # Bypass normal controls during game over

                # --- Standard Menu Scene Starting Navigation ---
                if event.key == pygame.K_SPACE:
                    if self.current_scene == 0:
                        self.current_scene = 4
                        self.scene = Scene4()
                
    def update(self):
        self.blink_timer += 1
        if self.blink_timer >= 30:  
            self.blink_show  = not self.blink_show  
            self.blink_timer = 0

        # 1. If global Game Over state is locked on
        if self.game_over:
            if self.death_timer < self.death_duration:
                self.death_timer += 1
            return

        # 2. Update current levels
        if self.current_scene != 0 and self.scene:
            self.scene.update()

            # --- Interlock with Scene4's Death State ---
            if self.scene.state == "DEATH" and self.scene.deathTimer <= 0:
                self.game_over = True
                self.death_timer = 0
                self.selected_option = 0

            if self.current_scene == 1:
                if self.scene.levelComplete:
                    pygame.mixer.music.stop()
                    self.current_scene = 4
                    self.scene = Scene4()

    def draw(self):
        self.screen.fill(BLACK)

        if self.current_scene == 0:
            self.draw_main_menu()
        elif self.current_scene != 0 and self.scene:
            self.scene.draw(self.screen)

        # Draw the Game Over Menu UI Layer above the scene visual contents
        if self.game_over:
            self.draw_game_over_menu()

        if self.showDebugCoords:
            self.draw_debug_coords()
            self.draw_debug_keys()
            self.draw_debug_anim()

        pygame.display.flip()

    def draw_game_over_menu(self):
        """Draws a fading dark tint screen layer overlay with interactive options."""
        # Visual fade calculated smoothly across the transition timers
        alpha = min(180, int((self.death_timer / self.death_duration) * 180))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 10, alpha))
        self.screen.blit(overlay, (0, 0))

        if alpha >= 120:
            font_title = pygame.font.SysFont("Arial", 48, bold=True)
            font_menu  = pygame.font.SysFont("Arial", 24, bold=True)

            title = font_title.render("GAME OVER", True, RED)
            self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 85))

            # Build selection lists layout items
            retry_color = YELLOW if self.selected_option == 0 else WHITE
            quit_color  = YELLOW if self.selected_option == 1 else WHITE

            retry_text = font_menu.render("RETRY", True, retry_color)
            quit_text  = font_menu.render("QUIT", True, quit_color)

            self.screen.blit(retry_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 10))
            self.screen.blit(quit_text, (SCREEN_WIDTH // 2 + 40, SCREEN_HEIGHT // 2 + 10))

    def draw_debug_coords(self):
        mouseX, mouseY = pygame.mouse.get_pos()
        label = self.debugFont.render(f"({mouseX}, {mouseY})", True, WHITE, BLACK)
        labelX = mouseX + 14
        labelY = mouseY + 14
        if labelX + label.get_width() > SCREEN_WIDTH:
            labelX = mouseX - 14 - label.get_width()
        if labelY + label.get_height() > SCREEN_HEIGHT:
            labelY = mouseY - 14 - label.get_height()
        self.screen.blit(label, (labelX, labelY))

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

    def draw_debug_anim(self):
        if not self.scene or not hasattr(self.scene, "player"):
            return
        player = self.scene.player
        namedSets = [
            ("IDLE_R", player.idleFrames), ("IDLE_L", player.idleLeftFrames),
            ("WALK_R", player.walkingRightFrames), ("WALK_L", player.walkingLeftFrames),
            ("RUN_R", player.runningRightFrames), ("RUN_L", player.runningLeftFrames),
            ("ATTACK_R", player.attackRightFrames), ("ATTACK_L", player.attackLeftFrames),
            ("HURT_R", player.hurtRightFrames), ("HURT_L", player.hurtLeftFrames),
        ]
        setName = next((name for name, frames in namedSets if frames is player.currentFrames), "?")
        text = f"anim:{setName}  frame:{player.animIndex}/{len(player.currentFrames)}  dir:{player.direction}  running:{player.isRunning}"
        label = self.debugFont.render(text, True, WHITE, BLACK)
        self.screen.blit(label, (10, 30))

    def draw_main_menu(self):
        font_big   = pygame.font.SysFont("Arial", 48, bold=True)
        font_small = pygame.font.SysFont("Arial", 20)
        title = font_big.render("Prickle's Grove", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
        if self.blink_show:
            msg = font_small.render("PRESS SPACE TO START", True, WHITE)
            self.screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2))        
        hint = font_small.render("ESC = quit", True, WHITE)
        self.screen.blit(hint, (10, SCREEN_HEIGHT - 30))

# START GAME
if __name__ == "__main__":
    game = Game()
    game.run()