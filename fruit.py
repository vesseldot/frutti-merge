"""
fruit.py — Clase Fruit (física con pymunk) + dibujo con sprites PNG.

Los sprites viven en Assets/imagenes/ ({tier}.png). Al cargarlos se calcula el
círculo real del cuerpo a partir del canal alpha (ignorando hojas/tallo) para
que el dibujo coincida EXACTAMENTE con el círculo de física (hitbox). Si falta
un PNG se usa el dibujo kawaii procedural original como respaldo.
"""
import math
import os
import pygame
import pymunk

from config import FRUITS, ELASTICITY, FRICTION

FRUIT_COLLISION_TYPE = 1


class Fruit:
    """Una fruta con cuerpo físico y carita kawaii."""

    def __init__(self, space: pymunk.Space, x: float, y: float, tier: int,
                 scale: float = 1.0):
        self.tier = tier
        name, radius, color, edge, points = FRUITS[tier]
        self.name = name
        self.scale = scale               # 2 jugadores: frutas proporcionales
        self.radius = radius * scale
        self.color = color
        self.edge = edge
        self.points = points

        mass = self.radius * self.radius * 0.02
        moment = pymunk.moment_for_circle(mass, 0, self.radius)
        self.body = pymunk.Body(mass, moment)
        self.body.position = (x, y)
        self.shape = pymunk.Circle(self.body, self.radius)
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


# ====================================================================== SPRITES
_IMG_DIRS = (os.path.join("assets", "imagenes"), os.path.join("Assets", "imagenes"))
_images: dict = {}       # nombre -> Surface | None
_scaled: dict = {}       # (nombre, (w, h)) -> Surface | None
_sprites: dict = {}      # tier -> (Surface con el cuerpo centrado, radio_cuerpo_px) | None
_rot_cache: dict = {}    # (tier, radio_px, angulo_cuantizado) -> Surface


def load_image(filename):
    """Carga un PNG de Assets/imagenes (cacheado). Devuelve None si no existe."""
    if filename not in _images:
        surf = None
        for d in _IMG_DIRS:
            path = os.path.join(d, filename)
            if os.path.exists(path):
                try:
                    surf = pygame.image.load(path)
                    if pygame.display.get_surface():
                        surf = surf.convert_alpha()
                except pygame.error:
                    surf = None
                break
        _images[filename] = surf
    return _images[filename]


def scaled_image(filename, size):
    """Versión escalada (cacheada) de una imagen de Assets/imagenes."""
    key = (filename, size)
    if key not in _scaled:
        img = load_image(filename)
        _scaled[key] = pygame.transform.smoothscale(img, size) if img else None
    return _scaled[key]


def _body_circle(img):
    """Círculo (cx, cy, r) del cuerpo de la fruta a partir del canal alpha.

    Las hojas/tallo siempre están arriba y el cuerpo apoya en el borde
    inferior del sprite, así que: r = mitad de la fila opaca más ancha del
    65% inferior, y el centro queda a un radio del borde inferior.
    """
    w, h = img.get_size()
    k = 100.0 / max(w, h)
    small = pygame.transform.smoothscale(img, (max(1, int(w * k)), max(1, int(h * k))))
    mask = pygame.mask.from_surface(small, 127)
    sw, sh = small.get_size()
    rows = []
    for y in range(sh):
        xs = [x for x in range(sw) if mask.get_at((x, y))]
        rows.append((xs[0], xs[-1]) if xs else None)
    ys = [y for y, row in enumerate(rows) if row]
    if not ys:
        return w / 2, h / 2, min(w, h) / 2
    top, bottom = ys[0], ys[-1]
    cut = top + int((bottom - top) * 0.35)
    width, ybest = max((rows[y][1] - rows[y][0] + 1, y)
                       for y in range(cut, bottom + 1) if rows[y])
    r = width / 2.0
    cx = (rows[ybest][0] + rows[ybest][1] + 1) / 2.0
    cy = bottom + 1 - r
    return cx / k, cy / k, r / k


def _get_sprite(tier):
    """Sprite del tier re-encuadrado para que el cuerpo quede en el centro.

    Así la rotación y el blit centrado alinean el cuerpo del PNG con el
    cuerpo físico de pymunk sin offsets por fruta.
    """
    if tier not in _sprites:
        img = load_image(f"{tier}.png")
        if img is None:
            _sprites[tier] = None
        else:
            cx, cy, r = _body_circle(img)
            w, h = img.get_size()
            # re-muestrea a 2x: así TODOS los dibujados en pantalla son
            # reducciones (nítidas) y nunca ampliaciones (pixeladas), y la
            # rotación tiene el doble de muestras para interpolar
            img = pygame.transform.smoothscale(img, (w * 2, h * 2))
            cx, cy, r, w, h = cx * 2, cy * 2, r * 2, w * 2, h * 2
            ext = int(max(cx, w - cx, cy, h - cy)) + 1
            canvas = pygame.Surface((ext * 2, ext * 2), pygame.SRCALPHA)
            canvas.blit(img, (round(ext - cx), round(ext - cy)))
            _sprites[tier] = (canvas, r)
    return _sprites[tier]


def draw_fruit(screen, center, radius, tier, angle=0.0):
    """Dibuja una fruta con su PNG (o arte procedural si no hay sprite).

    El sprite se escala para que el radio del CUERPO coincida con el radio
    físico (+2 px para que las frutas se aniden sin huecos visibles).
    """
    sprite = _get_sprite(tier)
    if sprite is None:
        _draw_fruit_procedural(screen, center, radius, tier, angle)
        return
    surf, body_r = sprite
    deg = round(-math.degrees(angle) / 4) * 4      # cuantizado para cachear
    key = (tier, int(radius), deg)
    img = _rot_cache.get(key)
    if img is None:
        if len(_rot_cache) > 2500:
            _rot_cache.clear()
        img = pygame.transform.rotozoom(surf, deg, (radius + 2) / body_r)
        _rot_cache[key] = img
    screen.blit(img, img.get_rect(center=(int(center[0]), int(center[1]))))


# ================================================== ARTE PROCEDURAL (respaldo)
def _draw_fruit_procedural(screen, center, radius, tier, angle=0.0):
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
