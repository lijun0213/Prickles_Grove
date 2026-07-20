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


class HitShockwave(pygame.sprite.Sprite):
    def __init__(self, x, y, max_radius=60, color=(255, 215, 0)):  # Defaults to a Golden Honey ring
        super().__init__()
        self.x = x
        self.y = y
        self.radius = 10
        self.max_radius = max_radius
        self.grow_speed = 3
        self.color = color
        self.alpha = 255
        
        # Create a surface large enough to contain the final ring size
        self.image = pygame.Surface((max_radius * 2, max_radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self):
        # Grow the ring outward over time
        self.radius += self.grow_speed
        
        # Calculate fade out ratio as it expands
        progress = (self.radius - 10) / (self.max_radius - 10)
        self.alpha = max(0, int(255 * (1.0 - progress)))
        
        # Redraw surface frame cleanly
        self.image.fill((0, 0, 0, 0))
        if self.alpha > 0 and self.radius < self.max_radius:
            # Draw a thick outer ring and a thinner soft inner accent ring
            pygame.draw.circle(self.image, (*self.color, self.alpha), (self.max_radius, self.max_radius), int(self.radius), width=3)
            pygame.draw.circle(self.image, (255, 255, 255, int(self.alpha * 0.5)), (self.max_radius, self.max_radius), max(1, int(self.radius - 4)), width=1)
        else:
            self.kill() # Instantly remove from all tracking groups once faded out

    def draw(self, screen, cameraX):
        # Keeps the effect pinned to the game world space relative to camera scroll
        screen.blit(self.image, (self.rect.x - cameraX, self.rect.y))


class Particle:

    def __init__(self, x, y, color, size, velocity, lifetime):

        self.x = float(x)
        self.y = float(y)

        self.velocityX = velocity[0]
        self.velocityY = velocity[1]

        self.color = color

        self.size = size

        self.life = lifetime
        self.maxLife = lifetime


    def update(self):

        self.x += self.velocityX
        self.y += self.velocityY

        # gravity (optional)
        self.velocityY += 0.03

        self.life -= 1


    def draw(self, screen, cameraX):

        if self.life <= 0:
            return


        alpha = int(
            255 * (self.life / self.maxLife)
        )


        particleSurface = pygame.Surface(
            (self.size*2, self.size*2),
            pygame.SRCALPHA
        )


        pygame.draw.circle(
            particleSurface,
            (
                self.color[0],
                self.color[1],
                self.color[2],
                alpha
            ),
            (
                self.size,
                self.size
            ),
            self.size
        )


        screen.blit(
            particleSurface,
            (
                self.x - cameraX - self.size,
                self.y - self.size
            )
        )


class ParticleSystem:

    def __init__(self):
        self.particles = []


    def add(self, particle):
        self.particles.append(particle)


    def update(self):

        for particle in self.particles[:]:

            particle.update()

            if particle.life <= 0:
                self.particles.remove(particle)


    def draw(self, screen, cameraX):

        for particle in self.particles:
            particle.draw(screen, cameraX)


def createRatDeathEffect(particleSystem, pos):

    for i in range(20):

        particle = Particle(

            pos[0] + random.randint(-10,10),
            pos[1] + random.randint(-10,10),

            (120,80,50),   # brown dust color

            random.randint(3,6),

            (
                random.uniform(-3,3),
                random.uniform(-5,-1)
            ),

            random.randint(30,50)

        )

        particleSystem.add(particle)

def draw_paralysis_aura(screen, player, camera_x):
    """Renders a glowing, pulsating yellow aura around the player when paralyzed."""
    aura_size = 100
    aura_surf = pygame.Surface((aura_size, aura_size), pygame.SRCALPHA)
    
    # Create a pulsing alpha effect
    pulse = abs(pygame.time.get_ticks() % 1000 - 500) / 500.0  
    alpha_glow = int(80 + pulse * 100) # Oscillates alpha transparency
    
    # Outer glow ring
    pygame.draw.circle(aura_surf, (255, 235, 59, alpha_glow // 2), (aura_size // 2, aura_size // 2), 42)
    # Inner solid glow
    pygame.draw.circle(aura_surf, (255, 255, 0, alpha_glow), (aura_size // 2, aura_size // 2), 30)

    # Position centered on player sprite
    aura_rect = aura_surf.get_rect(center=(player.rect.centerx - camera_x, player.rect.centery))
    screen.blit(aura_surf, aura_rect)