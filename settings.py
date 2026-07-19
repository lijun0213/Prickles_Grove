# Screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500
FPS = 60
TITLE = "Prickle's Quest"

# Physics
GRAVITY = 0.8
PLAYER_SPEED = 4 # pixels per frame
JUMP_FORCE = -15

# Player
PLAYER_MAX_HP = 5
PLAYER_MAX_XP = 100
QUILL_SPEED = 10 # pixels per frame
PARALYSIS_DURATION = 180 # frames (180 / 60fps = 3 seconds)

# HUD
HP_BAR_WIDTH = 150
HP_BAR_HEIGHT = 16
XP_BAR_WIDTH  = 150
XP_BAR_HEIGHT = 10

# Timer
SCENE_TIME = {
    1: 90,   # Scene 1 tutorial — 90 seconds
    2: 120,  # Scene 2 — 120 seconds
    3: 120,  # Scene 3 — 120 seconds
    4: 150,  # Scene 4 final boss — 150 seconds
}

# Colours
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
RED    = (220, 50,  50)
GREEN  = (50,  200, 100)
YELLOW = (255, 220, 0)
BLUE = (0,0,255)