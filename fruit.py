"""
fruit.py — Clase Fruit (física con pymunk) + dibujo kawaii por código.
"""
import math
import pygame
import pymunk

from config import FRUITS, ELASTICITY, FRICTION

FRUIT_COLLISION_TYPE = 1


class Fruit:
    """Una fruta con cuerpo físico y carita kawaii."""

    def __init__(self, space: pymunk.Space, x: float, y: float, tier: int):
        self.tier = tier
        name, radius, color, edge, points = FRUITS[tier]
        self.name = name
        self.radius = radius
        self.color = color
        self.edge = edge
        self.points = points

        mass = radius * radius * 0.02
        moment = pymunk.moment_for_circle(mass, 0, radius)
        self.body = pymunk.Body(mass, moment)
        self.body.position = (x, y)
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity = ELASTICITY
        self.shape.friction = FRICTION
        self.shape.collision_type = FRUIT_COLLISION_TYPE
        self.shape.fruit = self          # referencia inversa para colisiones
        self.space = space
        space.add(self.body, self.shape)

        self.danger_timer = 0.0          # tiempo acumulado sobre la línea límite
        self.spawn_pop = 0.25            # animación de "pop" al nacer

    # -------------------------------------------------------------- utilidades
    def remove(self):
        if self.body in self.space.bodies:
            self.space.remove(self.body, self.shape)

    @property
    def pos(self):
        return self.body.position

    def is_settled(self, settle_speed: float) -> bool:
        return self.body.velocity.length < settle_speed

    # -------------------------------------------------------------- dibujo
    def draw(self, screen: pygame.Surface):
        x, y = int(self.body.position.x), int(self.body.position.y)
        angle = self.body.angle
        r = self.radius
        if self.spawn_pop > 0:                       # pequeño rebote al aparecer
            r = int(r * (1.0 + 0.35 * self.spawn_pop))
        draw_fruit(screen, (x, y), r, self.tier, angle)

    def update(self, dt: float):
        if self.spawn_pop > 0:
            self.spawn_pop = max(0.0, self.spawn_pop - dt * 2.5)


# ====================================================================== ARTE
def draw_fruit(screen, center, radius, tier, angle=0.0):
    """Dibuja una fruta kawaii: cuerpo, brillo, hoja/tallo y carita."""
    x, y = center
    name, _, color, edge, _ = FRUITS[tier]

    # cuerpo + contorno
    pygame.draw.circle(screen, edge, (x, y), radius + 3)
    pygame.draw.circle(screen, color, (x, y), radius)

    # brillo superior-izquierdo
    hl = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(hl, (255, 255, 255, 70),
                        (radius * 0.25, radius * 0.15, radius * 0.9, radius * 0.6))
    screen.blit(hl, (x - radius, y - radius))

    # detalles por fruta (rotan con el cuerpo)
    ca, sa = math.cos(angle), math.sin(angle)

    def rot(dx, dy):
        return (int(x + dx * ca - dy * sa), int(y + dx * sa + dy * ca))

    top = rot(0, -radius)
    if name in ("Cereza", "Manzana", "Durazno"):
        pygame.draw.line(screen, (110, 70, 30), top, rot(6, -radius - 12), 4)
        pygame.draw.ellipse(screen, (90, 170, 60),
                            (*_off(rot(10, -radius - 10), -4, -4), 16, 10))
    elif name == "Fresa":
        pygame.draw.polygon(screen, (80, 160, 70),
                            [rot(-10, -radius + 2), rot(0, -radius - 10), rot(10, -radius + 2)])
        for dx, dy in ((-radius*0.4, -radius*0.1), (0, radius*0.2), (radius*0.4, -radius*0.1),
                       (-radius*0.2, radius*0.45), (radius*0.2, radius*0.45)):
            pygame.draw.circle(screen, (255, 235, 190), rot(dx, dy), max(2, radius // 12))
    elif name == "Uva":
        pygame.draw.circle(screen, edge, rot(-radius*0.45, -radius*0.35), radius // 3, 2)
        pygame.draw.circle(screen, edge, rot(radius*0.45, -radius*0.35), radius // 3, 2)
        pygame.draw.circle(screen, edge, rot(0, radius*0.45), radius // 3, 2)
    elif name in ("Mandarina", "Naranja"):
        pygame.draw.circle(screen, (90, 170, 60), top, max(4, radius // 7))
    elif name == "Pera":
        pygame.draw.line(screen, (110, 70, 30), top, rot(0, -radius - 12), 4)
    elif name == "Piña":
        step = max(10, radius // 3)
        for i in range(-radius, radius, step):
            pygame.draw.line(screen, edge, rot(i, -radius*0.7), rot(i + radius, radius*0.7), 2)
            pygame.draw.line(screen, edge, rot(i + radius, -radius*0.7), rot(i, radius*0.7), 2)
        pygame.draw.polygon(screen, (80, 160, 70),
                            [rot(-12, -radius + 4), rot(-6, -radius - 16), rot(0, -radius + 2),
                             rot(6, -radius - 16), rot(12, -radius + 4)])
    elif name == "Melón":
        for k in (-0.5, 0.0, 0.5):
            rect = pygame.Rect(0, 0, radius * 2, radius * 2)
            rect.center = (x, y)
            pygame.draw.arc(screen, edge, rect, math.pi/2 + k - 0.4, math.pi/2 + k + 0.4, 2)
    elif name == "Sandía":
        for k in range(5):
            a0 = angle + k * (2 * math.pi / 5)
            pygame.draw.line(screen, (40, 110, 40),
                             (x + math.cos(a0) * radius * 0.2, y + math.sin(a0) * radius * 0.2),
                             (x + math.cos(a0) * radius * 0.95, y + math.sin(a0) * radius * 0.95), 6)

    # carita kawaii (no rota: siempre mira al jugador)
    eye_dx = radius * 0.35
    eye_dy = -radius * 0.1
    eye_r = max(2, radius // 9)
    pygame.draw.circle(screen, (60, 40, 30), (int(x - eye_dx), int(y + eye_dy)), eye_r)
    pygame.draw.circle(screen, (60, 40, 30), (int(x + eye_dx), int(y + eye_dy)), eye_r)
    mouth = pygame.Rect(0, 0, radius * 0.5, radius * 0.35)
    mouth.center = (x, y + radius * 0.25)
    pygame.draw.arc(screen, (60, 40, 30), mouth, math.pi, 2 * math.pi, max(2, radius // 14))
    # chapitas rosas
    blush = pygame.Surface((radius, radius), pygame.SRCALPHA)
    pygame.draw.circle(blush, (255, 140, 140, 90), (radius // 4, radius // 4), max(2, radius // 8))
    screen.blit(blush, (x - eye_dx - radius // 4, y + radius * 0.12))
    screen.blit(blush, (x + eye_dx - radius // 4, y + radius * 0.12))


def _off(pos, dx, dy):
    return (pos[0] + dx, pos[1] + dy)
