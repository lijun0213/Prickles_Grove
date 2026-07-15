import pygame
import math
import random
from settings import WHITE, SCREEN_WIDTH, SCREEN_HEIGHT

impact_particles = []

def create_impact_burst(pos):
    """Generates sparks that fly out from the impact point."""
    for _ in range(8):
        impact_particles.append({
            "x": pos[0],
            "y": pos[1],
            "vx": random.uniform(-4, 4),
            "vy": random.uniform(-6, -2),
            "radius": random.randint(3, 5),
            "life": random.randint(10, 20)
        })

def update_and_draw_particles(screen, camera_x):
    """Updates and draws active particles relative to camera coordinate space."""
    for p in impact_particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.3 # gravity pull down effect
        p["life"] -= 1
        
        if p["life"] <= 0:
            impact_particles.remove(p)
            continue
            
        # Draw small sparkling circles (Yellow/Orange mix)
        color = random.choice([(255, 220, 50), (255, 100, 30)])
        pygame.draw.circle(screen, color, (int(p["x"] - camera_x), int(p["y"])), int(p["radius"]))

surrender_particles = []

def create_surrender_sparkle(pos):
    """Small burst of pale sparkles above a defeated enemy's head, e.g. Nugget's confession."""
    for _ in range(12):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(0.5, 2)
        surrender_particles.append({
            "x": pos[0],
            "y": pos[1],
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed - 1,
            "radius": random.randint(2, 4),
            "life": random.randint(25, 40)
        })

def update_and_draw_surrender(screen, camera_x):
    for p in surrender_particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.05
        p["life"] -= 1

        if p["life"] <= 0:
            surrender_particles.remove(p)
            continue

        alpha = max(0, min(255, p["life"] * 8))
        surf = pygame.Surface((p["radius"]*2, p["radius"]*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 255, 220, alpha), (p["radius"], p["radius"]), p["radius"])
        screen.blit(surf, (p["x"] - camera_x - p["radius"], p["y"] - p["radius"]))

def drawShatterBurst(screen, center, timer, duration, color=WHITE):
    """Radiating shard-line burst + white flash (e.g. a window breaking).

    center: (x, y) screen position of the effect origin (camera-adjusted)
    timer: frames remaining on the effect
    duration: total effect duration in frames, used to fade it out
    """
    cx, cy = center

    alpha = int(255 * (timer / duration))
    flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    flash.fill((255, 255, 255, alpha // 3))
    screen.blit(flash, (0, 0))

    progress = 1 - (timer / duration)
    for angle in range(0, 360, 30):
        dist = 10 + progress * 50
        ex = cx + math.cos(math.radians(angle)) * dist
        ey = cy + math.sin(math.radians(angle)) * dist
        pygame.draw.line(screen, color, (cx, cy), (ex, ey), 2)


def drawPulseGlow(screen, center, baseRadius=32, pulseAmount=4,
                   color=(150, 220, 255, 90), size=100):
    """Soft pulsing glow, e.g. behind a glowing collectible like the map."""
    cx, cy = center

    pulse = pulseAmount + int(pulseAmount * abs(pygame.time.get_ticks() % 1000 - 500) / 500)
    glow = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(glow, color, (size // 2, size // 2), baseRadius + pulse)
    screen.blit(glow, (cx - size // 2, cy - size // 2))


def drawDoorGlow(screen, rect, timer, baseColor=(255, 255, 255)):
    pulse = abs((timer % 50) - 25) * 3.2
    alpha = 120 + int(pulse)
    
    # 1. Create a transparent canvas that covers the glowing zone
    glowWidth, glowHeight = 150, SCREEN_HEIGHT
    glowSurface = pygame.Surface((glowWidth, glowHeight), pygame.SRCALPHA)
    
    # 2. Draw layered, fading circles to simulate a soft light beam 
    r, g, b = baseColor
    for radius in range(glowWidth, 0, -10):
        # As circles get smaller/closer to the edge, they get slightly brighter
        layerAlpha = int(alpha * (1 - radius / glowWidth) * 0.5)
        if layerAlpha > 0:
            pygame.draw.circle(glowSurface, (r, g, b, layerAlpha), (0, SCREEN_HEIGHT // 2), radius * 2)
            
    # 3. Blit the final combined soft glow directly to the left edge of the monitor
    screen.blit(glowSurface, (0, 0))

def drawTeleportPuff(screen, center, camera_x=0, color=(255, 220, 255)):
    """Small radiating ring, blitted once at teleport-out and teleport-in points."""
    cx, cy = center[0] - camera_x, center[1]
    surf = pygame.Surface((80, 80), pygame.SRCALPHA)
    for r in range(10, 40, 8):
        alpha = max(0, 200 - r * 4)
        pygame.draw.circle(surf, (*color, alpha), (40, 40), r, width=2)
    screen.blit(surf, (cx - 40, cy - 40))