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
from dialogue import Dialogue

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        pygame.mixer.init()
 
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock  = pygame.time.Clock()

        try:
            self.bg = pygame.image.load(r"scene0_assets/scene 0 & 1.png").convert_alpha()
            bgWidth, bgHeight = self.bg.get_size()
            scale = SCREEN_HEIGHT / bgHeight
            self.bg = pygame.transform.scale(self.bg, (int(bgWidth * scale), SCREEN_HEIGHT))
            self.bgWidth = self.bg.get_width()
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
        self.paused_by_esc = False

        # Scene4 takes a shared Dialogue instance (dialogue_system) rather
        # than owning its own like every other scene — created once here so
        # every Scene4() construction below can hand it the same one.
        self.dialogueSystem = Dialogue()

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
                    if self.current_scene != 0:  # only in an actual scene, not the main menu
                        if self.game_over and self.paused_by_esc:
                            # ESC again while paused → resume
                            self.game_over = False
                            self.paused_by_esc = False
                        elif not self.game_over:
                            # Open the menu immediately — full alpha, no fade-in wait
                            self.game_over = True
                            self.paused_by_esc = True
                            self.death_timer = self.death_duration
                            self.selected_option = 0

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
                            if self.paused_by_esc:
                                self.game_over = False
                                self.paused_by_esc = False
                            else:
                                self.restart_level()                        
                        elif self.selected_option == 1:  # Quit to Main Menu
                            self.exit_to_menu()
                    continue  # Skip checking normal gameplay key presses

                # --- Normal Gameplay Key Bindings ---
                if event.key == pygame.K_SPACE and self.current_scene == 0:
                    self.current_scene = -1
                    self.scene = Scene0()

    def restart_level(self):
        self.game_over = False
        self.death_timer = 0  # Reset overlay animation timer
        
        # Instantiate a fresh copy of the scene based on active current_scene ID
        if self.current_scene == 1:
            self.scene = Scene1()
        elif self.current_scene == 3:
            self.scene = Scene3() 
        elif self.current_scene == 4:
            self.scene = Scene4(self.dialogueSystem)

    def exit_to_menu(self):
        self.game_over = False
        self.paused_by_esc = False
        self.death_timer = 0
        self.current_scene = 0
        self.scene = None

        # --- Standard Menu Scene Starting Navigation ---
        if event.key == pygame.K_SPACE:
            if self.current_scene == 0 :
                self.current_scene = 3
                self.scene = Scene3()
                
    def update(self):
        self.blink_timer += 1
        if self.blink_timer >= 30:  
            self.blink_show  = not self.blink_show  
            self.blink_timer = 0

        # 1. If game over is triggered, run the overlay fade transition
        if self.game_over:
            if self.death_timer < self.death_duration:
                self.death_timer += 1
            return  # Stop updating the underlying level

        # 2. Update current active scene
        if self.current_scene != 0 and self.scene:
            self.scene.update()

            # --- Player HP Death Check ---
            # Direct check using self.scene.player.hp
            if self.scene.player.hp <= 0:
                self.scene.player.takeDamage = True
                self.game_over = True
                self.paused_by_esc = False
                self.death_timer = 0
                self.selected_option = 0

            # Level completion transition
            if self.current_scene == -1:
                if self.scene.levelComplete:
                    self.current_scene = 1
                    self.scene = Scene1()
            elif self.current_scene == 1:
                if self.scene.levelComplete:
                    pygame.mixer.music.stop()
                    self.current_scene = 3
                    self.scene = Scene3()
            elif self.current_scene == 3:
                if self.scene.levelComplete:
                    pygame.mixer.music.stop()
                    self.current_scene = 4
                    self.scene = Scene4(self.dialogueSystem)

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
        if self.paused_by_esc:
            alpha = 180
        else:
            alpha = min(180, int((self.death_timer / self.death_duration) * 180))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 10, alpha))
        self.screen.blit(overlay, (0, 0))

        if alpha >= 120:
            font_title = pygame.font.SysFont("Arial", 48, bold=True)
            font_menu  = pygame.font.SysFont("Arial", 24, bold=True)

            title_text = "PAUSED" if self.paused_by_esc else "GAME OVER"
            title_color = WHITE if self.paused_by_esc else RED
            title = font_title.render(title_text, True, title_color)
            self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 85))

            retry_color = YELLOW if self.selected_option == 0 else WHITE
            quit_color  = YELLOW if self.selected_option == 1 else WHITE

            retry_label = "RESUME" if self.paused_by_esc else "RETRY"
            retry_text = font_menu.render(retry_label, True, retry_color)
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
        if self.bg:
            self.screen.blit(self.bg, (0,0))
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