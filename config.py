"""
config.py — Constantes globales del juego Frutti Merge (estilo Suika).
Todas las frutas se dibujan por código (sin imágenes externas).
"""

# ------------------------------------------------------------------ Pantalla
WIDTH, HEIGHT = 1000, 720
FPS = 60
TITLE = "Frutti Merge 🍉"

# ------------------------------------------------------------------ Colores UI
BG_COLOR        = (214, 164, 110)   # café claro (fondo)
HEADER_COLOR    = (245, 130, 32)    # naranja del header
PANEL_COLOR     = (255, 244, 214)   # crema (paneles)
PANEL_BORDER    = (240, 200, 70)    # amarillo dorado
CONTAINER_FILL  = (255, 240, 200)   # interior del contenedor
CONTAINER_EDGE  = (238, 210, 130)   # borde del contenedor
TEXT_DARK       = (90, 60, 30)
TEXT_LIGHT      = (255, 255, 255)
DANGER_COLOR    = (220, 60, 60)
BTN_COLOR       = (245, 130, 32)
BTN_HOVER       = (255, 160, 70)
BTN_TEXT        = (255, 255, 255)

# ------------------------------------------------------------------ Contenedor
CONTAINER = {
    "left":   330,
    "right":  670,
    "top":    150,     # borde visual superior
    "bottom": 660,
    "wall":   12,      # grosor de pared
}
DANGER_Y = 190          # línea límite: fruta estable arriba de esto = game over
DANGER_TIME = 2.0       # segundos que una fruta puede estar sobre la línea

# ------------------------------------------------------------------ Física
GRAVITY = (0, 1100)
ELASTICITY = 0.18
FRICTION = 0.6
DROP_COOLDOWN = 0.55    # seg entre lanzamientos
SETTLE_SPEED = 30       # velocidad bajo la cual una fruta se considera "quieta"

# ------------------------------------------------------------------ Frutas
# (nombre, radio, color_cuerpo, color_borde, puntos)  — 11 niveles
FRUITS = [
    ("Cereza",    16, (226, 60, 70),   (150, 25, 40),  1),
    ("Fresa",     22, (240, 90, 100),  (170, 40, 60),  3),
    ("Uva",       30, (160, 100, 220), (100, 55, 160), 6),
    ("Mandarina", 38, (255, 175, 60),  (200, 120, 20), 10),
    ("Naranja",   48, (255, 140, 40),  (200, 95, 10),  15),
    ("Manzana",   58, (235, 40, 50),   (160, 15, 25),  21),
    ("Pera",      70, (250, 230, 140), (190, 165, 70), 28),
    ("Durazno",   84, (255, 170, 180), (215, 110, 125),36),
    ("Piña",      98, (255, 210, 70),  (200, 150, 20), 45),
    ("Melón",    115, (200, 235, 130), (130, 175, 60), 55),
    ("Sandía",   135, (90, 180, 80),   (40, 110, 40),  66),
]
MAX_TIER = len(FRUITS) - 1
DROPPABLE_TIERS = 5          # solo los primeros 5 niveles caen del dispensador

# ------------------------------------------------------------------ Modos
MODE_NORMAL = "normal"
MODE_TIME   = "contrarreloj"
TIME_ATTACK_SECONDS = 120    # 2 minutos

# ------------------------------------------------------------------ Controles
CTRL_MOUSE  = "mouse"
CTRL_CAMERA = "camara"

# ------------------------------------------------------------------ Archivos
SCORES_FILE = "scores.json"
