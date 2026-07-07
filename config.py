"""
config.py — Constantes globales del juego FRUTAZO (estilo Suika).
Todas las frutas se dibujan por código (sin imágenes externas).
"""

# ------------------------------------------------------------------ Pantalla
WIDTH, HEIGHT = 1920, 1080      # 16:9 nativo — nítido 1:1 en pantalla completa
FPS = 60
TITLE = "FRUTAZO ^^"
HEADER_H = 84                   # alto de la franja naranja superior

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
# Proporciones tipo Suika: la sandía mide ~57% del ancho del contenedor,
# así caben muchas más frutas que antes.
CONTAINER = {
    "left":   630,     # centrado en WIDTH/2 = 960 (660 de ancho)
    "right":  1290,
    "top":    240,     # borde visual superior
    "bottom": 1020,
    "wall":   16,      # grosor de pared
}
DANGER_TIME = 2.0       # segundos que una fruta puede estar sobre la línea
DANGER_OFFSET = 60      # la línea de peligro se dibuja a top + este offset
DROP_HEIGHT = 90        # la fruta cuelga a esta altura sobre el contenedor

# ------------------------------------------------------------------ Contenedores 2 jugadores
# En modo dos jugadores la pantalla se divide: un contenedor por jugador.
# Las frutas se escalan para conservar la misma proporción que en 1 jugador
# (sandía ~57% del ancho del contenedor).
CONTAINER_P1 = {"left":   90, "right":  670, "top": 280, "bottom": 1020, "wall": 16}
CONTAINER_P2 = {"left": 1250, "right": 1830, "top": 280, "bottom": 1020, "wall": 16}
VERSUS_FRUIT_SCALE = 0.88    # = 580/660 (ancho versus / ancho 1 jugador)
SOLO_FRUIT_SCALE   = 0.80    # frutas más chicas en 1 jugador: caben más en el contenedor

# ------------------------------------------------------------------ Física
GRAVITY = (0, 1800)     # escalada a la nueva altura del contenedor
ELASTICITY = 0.18
FRICTION = 0.6
DROP_COOLDOWN = 0.55    # seg entre lanzamientos
SETTLE_SPEED = 45       # velocidad bajo la cual una fruta se considera "quieta"
KEYBOARD_SPEED = 650    # px/s al mover el dispensador con teclado (modo 2 jugadores)
MAX_SPEED = 1900        # tope de velocidad: evita expulsiones violentas cuando
                        # una fruta aparece superpuesta a otra (fusión/caída)

# ------------------------------------------------------------------ Frutas
# (nombre, radio, color_cuerpo, color_borde, puntos)  — 11 niveles
# Radios con las proporciones del Suika original (frutas pequeñas respecto
# al contenedor: la cereza mide ~4% del ancho y la sandía ~57%).
FRUITS = [
    ("Cereza",    28, (226, 60, 70),   (150, 25, 40),  1),
    ("Fresa",     36, (240, 90, 100),  (170, 40, 60),  3),
    ("Uva",       49, (160, 100, 220), (100, 55, 160), 6),
    ("Mandarina", 57, (255, 175, 60),  (200, 120, 20), 10),
    ("Naranja",   70, (255, 140, 40),  (200, 95, 10),  15),
    ("Manzana",   84, (235, 40, 50),   (160, 15, 25),  21),
    ("Pera",     101, (250, 230, 140), (190, 165, 70), 28),
    ("Durazno",  118, (255, 170, 180), (215, 110, 125),36),
    ("Piña",     137, (255, 210, 70),  (200, 150, 20), 45),
    ("Melón",    164, (200, 235, 130), (130, 175, 60), 55),
    ("Sandía",   188, (90, 180, 80),   (40, 110, 40),  66),
]
MAX_TIER = len(FRUITS) - 1
DROPPABLE_TIERS = 5          # solo los primeros 5 niveles caen del dispensador

# ------------------------------------------------------------------ Modos
MODE_NORMAL = "normal"
MODE_TIME   = "contrarreloj"
TIME_ATTACK_SECONDS = 180    # 3 minutos
MUSIC_SWITCH_AT = 60         # seg restantes para cambiar la música y avisar

# ------------------------------------------------------------------ Controles
CTRL_MOUSE  = "mouse"
CTRL_CAMERA = "camara"
CTRL_KEYS   = "teclas"       # control por teclado (modo 2 jugadores)

# ------------------------------------------------------------------ Música
# Todas las pistas viven en Assets/music/.
#   musica5  -> pantalla de título (menú/instrucciones)
#   musica2  -> último minuto del contrarreloj
#   bridge1  -> pantallas finales (game over)
#   pop.wav  -> SFX de fusión
# El resto suena de forma aleatoria al iniciar cualquier partida.
MENU_MUSIC = "musica5.mp3"
GAME_MUSIC = ["musica1.mp3", "musica3.mp3", "musica4.mp3", "musica6.mp3"]
TIME_MUSIC = "musica2.mp3"
END_MUSIC  = "bridge1.mp3"
POP_SFX    = "pop.wav"

# ------------------------------------------------------------------ Archivos
SCORES_FILE = "scores.json"
