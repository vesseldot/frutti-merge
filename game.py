"""
game.py — Lógica principal: máquina de estados (menú, instrucciones, juego,
game over), física, fusiones, modos de juego y control mouse/cámara/teclado.

Un `Board` encapsula todo el estado de un contenedor (física, frutas, puntaje,
dispensador). En 1 jugador hay un solo tablero centrado; en 2 jugadores hay dos
tableros lado a lado (pantalla dividida).
"""
import math
import os
import random
import pygame
import pymunk

import config as C
import scores as SC
import ui
from fruit import Fruit, draw_fruit, scaled_image, FRUIT_COLLISION_TYPE

# Estados
MENU, INSTRUCTIONS, PLAYING, GAME_OVER = "menu", "instrucciones", "jugando", "fin"

# Evento: terminó la pista de música actual (para rotar canciones de partida)
MUSIC_END = pygame.USEREVENT + 1


def random_tier():
    return random.randint(0, C.DROPPABLE_TIERS - 1)


# ====================================================================== Tablero
class Board:
    """Estado y física de un contenedor individual."""

    def __init__(self, game, bounds, control, keys=None, label="", accent=None,
                 scale=1.0, hand=None, cam_range=(0.0, 1.0)):
        self.game = game
        self.bounds = bounds
        self.danger_y = bounds["top"] + C.DANGER_OFFSET
        self.control = control           # CTRL_MOUSE | CTRL_CAMERA | CTRL_KEYS
        self.keys = keys or {}           # {"left":.., "right":.., "drop":..}
        self.label = label
        self.accent = accent or C.HEADER_COLOR
        self.scale = scale               # factor de tamaño de fruta del tablero
        self.hand = hand                 # None | "Right" | "Left" (modo cámara)
        self.cam_range = cam_range       # franja horizontal de la cámara usada

        self.space = pymunk.Space()
        self.space.gravity = C.GRAVITY
        self.space.collision_slop = 0.5      # tolera solapamientos mínimos sin expulsar
        self._build_walls()
        self.space.on_collision(FRUIT_COLLISION_TYPE, FRUIT_COLLISION_TYPE,
                                begin=self._on_fruit_collision)

        self.fruits: list[Fruit] = []
        self.pending_merges = []
        self.score = 0
        self.dropper_x = (bounds["left"] + bounds["right"]) / 2
        self.current_tier = random_tier()
        self.next_tier = random_tier()
        self.cooldown = 0.0
        self.alive = True                # False = contenedor lleno (eliminado)

    # ---------------------------------------------------------------- física
    def _build_walls(self):
        b = self.bounds
        w = b["wall"]
        segs = [
            pymunk.Segment(self.space.static_body, (b["left"],  b["top"] - 300), (b["left"],  b["bottom"]), w),
            pymunk.Segment(self.space.static_body, (b["right"], b["top"] - 300), (b["right"], b["bottom"]), w),
            pymunk.Segment(self.space.static_body, (b["left"],  b["bottom"]),    (b["right"], b["bottom"]), w),
        ]
        for s in segs:
            s.elasticity = C.ELASTICITY
            s.friction = 0.9
        self.space.add(*segs)

    def _on_fruit_collision(self, arbiter, space, data):
        a, b = arbiter.shapes
        fa, fb = getattr(a, "fruit", None), getattr(b, "fruit", None)
        if fa and fb and fa.tier == fb.tier and fa.tier < C.MAX_TIER:
            flat = [f for p in self.pending_merges for f in p]
            if fa not in flat and fb not in flat:
                self.pending_merges.append((fa, fb))

    def _apply_merges(self):
        for fa, fb in self.pending_merges:
            if fa not in self.fruits or fb not in self.fruits:
                continue
            nx = (fa.pos.x + fb.pos.x) / 2
            ny = (fa.pos.y + fb.pos.y) / 2
            new_tier = fa.tier + 1
            fa.remove(); fb.remove()
            self.fruits.remove(fa); self.fruits.remove(fb)
            merged = Fruit(self.space, nx, ny, new_tier, scale=self.scale)
            self.fruits.append(merged)
            self.score += C.FRUITS[new_tier][4]
            self.game._play_pop()
        self.pending_merges.clear()

    def step_physics(self, dt):
        if not self.alive:
            return
        self.cooldown = max(0.0, self.cooldown - dt)
        for _ in range(4):                   # más sub-pasos = pilas estables
            self.space.step(dt / 4)
            for f in self.fruits:            # tope de velocidad anti-rebote
                v = f.body.velocity
                if v.length > C.MAX_SPEED:
                    f.body.velocity = v * (C.MAX_SPEED / v.length)
        self._apply_merges()
        for f in self.fruits:
            f.update(dt)

    def check_topout(self, dt) -> bool:
        """Devuelve True si una fruta quieta se apiló sobre la línea de peligro."""
        if not self.alive:
            return False
        for f in self.fruits:
            over = f.pos.y - f.radius < self.danger_y
            if over and f.is_settled(C.SETTLE_SPEED):
                f.danger_timer += dt
                if f.danger_timer >= C.DANGER_TIME:
                    return True
            else:
                f.danger_timer = 0.0
        return False

    # ---------------------------------------------------------------- control
    def clamp_x(self, x):
        b = self.bounds
        r = C.FRUITS[self.current_tier][1] * self.scale
        return max(b["left"] + r + 20, min(b["right"] - r - 20, x))

    def move_with_keys(self, pressed, dt):
        dx = 0
        if pressed[self.keys["left"]]:
            dx -= 1
        if pressed[self.keys["right"]]:
            dx += 1
        if dx:
            b = self.bounds
            self.dropper_x += dx * C.KEYBOARD_SPEED * dt
            self.dropper_x = max(b["left"] + 30, min(b["right"] - 30, self.dropper_x))

    def drop_fruit(self):
        if self.cooldown > 0 or not self.alive:
            return
        b = self.bounds
        # jitter: sin él, dos frutas con centros perfectamente alineados se
        # apilan en torre vertical estable (el contacto no genera torque)
        x = self.clamp_x(self.dropper_x) + random.uniform(-4, 4)
        fruit = Fruit(self.space, x, b["top"] - C.DROP_HEIGHT, self.current_tier,
                      scale=self.scale)
        fruit.body.angular_velocity = random.uniform(-0.6, 0.6)
        self.fruits.append(fruit)
        self.current_tier = self.next_tier
        self.next_tier = random_tier()
        self.cooldown = C.DROP_COOLDOWN


# ======================================================================== Juego
class Game:
    def __init__(self, screen):
        self.screen = screen
        self.state = MENU
        self.mode = C.MODE_NORMAL
        self.control = C.CTRL_MOUSE
        self.players = 1
        self.tracker = None                  # HandTracker (si eligen cámara)
        self.t = 0.0                         # reloj global para animaciones

        # --- música
        self.music_context = None            # "menu" | "game" | None
        self.current_track = None            # pista de juego en curso
        self.music_changed = False           # ya se hizo el cambio del último minuto
        self.pop_sound = None                # SFX: fusión de frutas
        self._pop_sound_loaded = False

        # ---------------- botones del menú
        cx = C.WIDTH // 2
        self.btn_mouse  = ui.Button("Mouse",  (cx - 210, 510))
        self.btn_camera = ui.Button("Camara", (cx + 210, 510))
        self.btn_1p     = ui.Button("1 Jugador",   (cx - 210, 660))
        self.btn_2p     = ui.Button("2 Jugadores", (cx + 210, 660))
        self.btn_normal = ui.Button("Modo Normal",       (cx - 210, 810))
        self.btn_time   = ui.Button("Contrarreloj 3:00", (cx + 210, 810))
        self.btn_play   = ui.Button("¡ JUGAR !", (cx, 950), size=(420, 90), font=ui.FONT_LG)
        self.btn_mouse.selected = True
        self.btn_1p.selected = True
        self.btn_normal.selected = True

        self.btn_accept = ui.Button("¡Entendido, a jugar!", (cx, 930), size=(510, 90))
        self.btn_again  = ui.Button("Volver a jugar", (cx, 0))
        self.btn_menu   = ui.Button("Menú", (cx, 0), size=(300, 75))

        self.camera_error = ""
        self.reset_match()
        self._play_menu_music()

    # ================================================================ partida
    def reset_match(self):
        self.best = SC.best_score(self.mode)
        self.time_left = C.TIME_ATTACK_SECONDS
        self.time_notice = 0.0               # temporizador del aviso "último minuto"
        self.music_changed = False
        self.game_over_reason = ""
        self.final_scores = []
        self.winner = 0                      # 0 empate/na, 1 = J1, 2 = J2
        self.score = 0

        if self.players == 2:
            # con cámara: J1 = mano derecha (mitad izquierda de la cámara),
            # J2 = mano izquierda (mitad derecha); con mouse/teclado: teclas
            ctrl = C.CTRL_CAMERA if self.control == C.CTRL_CAMERA else C.CTRL_KEYS
            self.boards = [
                Board(self, C.CONTAINER_P1, ctrl,
                      keys={"left": pygame.K_a, "right": pygame.K_d, "drop": pygame.K_s},
                      label="Jugador 1", accent=(70, 150, 240),
                      scale=C.VERSUS_FRUIT_SCALE, hand="Right", cam_range=(0.0, 0.55)),
                Board(self, C.CONTAINER_P2, ctrl,
                      keys={"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "drop": pygame.K_DOWN},
                      label="Jugador 2", accent=(240, 110, 70),
                      scale=C.VERSUS_FRUIT_SCALE, hand="Left", cam_range=(0.45, 1.0)),
            ]
        else:
            self.boards = [Board(self, C.CONTAINER, self.control, accent=C.HEADER_COLOR)]

    # ================================================================ SFX pop
    def _ensure_pop_sound(self):
        if self._pop_sound_loaded:
            return
        self._pop_sound_loaded = True
        if not self._init_mixer():
            return
        try:
            self.pop_sound = pygame.mixer.Sound(self._music_path(C.POP_SFX))
        except pygame.error:
            self.pop_sound = None

    def _play_pop(self):
        self._ensure_pop_sound()
        if self.pop_sound:
            self.pop_sound.play()

    # ================================================================ música
    def _music_path(self, filename):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(base_dir, "assets", "music", filename),
            os.path.join(base_dir, "Assets", "music", filename),
            os.path.join("assets", "music", filename),
            os.path.join("Assets", "music", filename),
            os.path.join("assets", filename),
            os.path.join("Assets", filename),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return candidates[1]

    def _init_mixer(self):
        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except pygame.error:
                return False
        pygame.mixer.music.set_endevent(MUSIC_END)
        return True

    def _load_and_play(self, filename, loops=-1):
        if not self._init_mixer():
            return
        try:
            pygame.mixer.music.load(self._music_path(filename))
            pygame.mixer.music.play(loops)
        except pygame.error:
            pass

    def _play_menu_music(self):
        """Fondo de la pantalla de título/instrucciones (musica5)."""
        if self.music_context == "menu":
            return
        self.music_context = "menu"
        self._load_and_play(C.MENU_MUSIC)

    def _play_game_music(self):
        """Pista aleatoria de partida, siempre distinta a la anterior.

        Suena UNA vez (loops=0): al terminar, MUSIC_END dispara la
        siguiente canción aleatoria en _on_music_end.
        """
        self.music_context = "game"
        options = [m for m in C.GAME_MUSIC if m != self.current_track] or C.GAME_MUSIC
        self.current_track = random.choice(options)
        self._load_and_play(self.current_track, loops=0)

    def _on_music_end(self):
        """Rota a otra canción cuando termina una pista de partida.

        Las de título/fin/último minuto van en loop y no llegan aquí; el
        chequeo de get_busy ignora los eventos generados al cambiar de pista
        manualmente (la nueva ya está sonando cuando llega el evento).
        """
        if (self.music_context == "game" and self.state == PLAYING
                and not self.music_changed
                and pygame.mixer.get_init() is not None
                and not pygame.mixer.music.get_busy()):
            self._play_game_music()

    def _play_end_music(self):
        """Pantallas finales (game over): bridge1."""
        self.music_context = "end"
        self._load_and_play(C.END_MUSIC)

    def _maybe_switch_music(self):
        """Último minuto del contrarreloj: cambia a musica2 y avisa."""
        if self.music_changed or self.time_left > C.MUSIC_SWITCH_AT:
            return
        self.music_changed = True            # no reintentar aunque falle la carga
        self.time_notice = 4.0               # muestra el aviso unos segundos
        self.current_track = C.TIME_MUSIC
        self._load_and_play(C.TIME_MUSIC)

    def _stop_music(self):
        self.music_context = None
        if pygame.mixer.get_init() is not None:
            pygame.mixer.music.stop()

    # ================================================================ eventos
    def handle_event(self, event, mouse):
        if event.type == MUSIC_END:
            self._on_music_end()
            return
        if self.state == MENU:
            self._menu_events(event, mouse)
        elif self.state == INSTRUCTIONS:
            if self.btn_accept.clicked(event, mouse) or \
               (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
                self._play_game_music()
                self.state = PLAYING
        elif self.state == PLAYING:
            self._playing_events(event, mouse)
        elif self.state == GAME_OVER:
            if self.btn_again.clicked(event, mouse):
                self.reset_match()
                self._play_game_music()
                self.state = PLAYING
            if self.btn_menu.clicked(event, mouse):
                self._close_camera()
                self.reset_match()
                self._play_menu_music()
                self.state = MENU

    def _playing_events(self, event, mouse):
        for board in self.boards:
            if board.control == C.CTRL_MOUSE:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    board.drop_fruit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    board.drop_fruit()
            elif board.control == C.CTRL_KEYS:
                if event.type == pygame.KEYDOWN and event.key == board.keys["drop"]:
                    board.drop_fruit()

    def _menu_events(self, event, mouse):
        if self.btn_mouse.clicked(event, mouse):
            self.btn_mouse.selected, self.btn_camera.selected = True, False
            self.control = C.CTRL_MOUSE
            self.camera_error = ""
        if self.btn_camera.clicked(event, mouse):
            self.btn_camera.selected, self.btn_mouse.selected = True, False
            self.control = C.CTRL_CAMERA
        if self.btn_1p.clicked(event, mouse):
            self.btn_1p.selected, self.btn_2p.selected = True, False
            self.players = 1
        if self.btn_2p.clicked(event, mouse):
            self.btn_2p.selected, self.btn_1p.selected = True, False
            self.players = 2
            self.camera_error = ""
        if self.btn_normal.clicked(event, mouse):
            self.btn_normal.selected, self.btn_time.selected = True, False
            self.mode = C.MODE_NORMAL
        if self.btn_time.clicked(event, mouse):
            self.btn_time.selected, self.btn_normal.selected = True, False
            self.mode = C.MODE_TIME
        if self.btn_play.clicked(event, mouse):
            if self.control == C.CTRL_CAMERA and not self._open_camera():
                return                       # se queda en el menú y muestra error
            self.reset_match()
            self.state = INSTRUCTIONS

    # ================================================================ cámara
    def _open_camera(self) -> bool:
        import hand_tracker
        if not hand_tracker.AVAILABLE:
            self.camera_error = "Instala:  pip install opencv-python mediapipe"
            return False
        try:
            self._close_camera()             # reabre con el nº de manos correcto
            self.tracker = hand_tracker.HandTracker(
                num_hands=2 if self.players == 2 else 1)
            self.camera_error = ""
            return True
        except Exception as e:
            self.camera_error = f"No se pudo abrir la cámara ({e})"
            return False

    def _close_camera(self):
        if self.tracker:
            self.tracker.close()
            self.tracker = None

    # ================================================================ update
    def update(self, dt, mouse):
        self.t += dt
        if self.state != PLAYING:
            return

        self.time_notice = max(0.0, self.time_notice - dt)
        pressed = pygame.key.get_pressed()
        if self.tracker:
            self.tracker.update()            # procesa la cámara UNA vez por frame

        # --- control del dispensador (solo la fruta de arriba)
        for board in self.boards:
            if not board.alive:
                continue
            if board.control == C.CTRL_MOUSE:
                board.dropper_x = mouse[0]
            elif board.control == C.CTRL_CAMERA and self.tracker:
                st = self.tracker.hand(board.hand)
                if st.detected:
                    b = board.bounds
                    span = b["right"] - b["left"]
                    lo, hi = board.cam_range
                    t = max(0.0, min(1.0, (st.hand_x - lo) / (hi - lo)))
                    if st.closed:
                        board.dropper_x = b["left"] + t * span
                    if st.release_event:
                        board.drop_fruit()
            elif board.control == C.CTRL_KEYS:
                board.move_with_keys(pressed, dt)

        # --- física y fusiones
        for board in self.boards:
            board.step_physics(dt)

        # --- contenedores que se llenan
        for board in self.boards:
            if board.check_topout(dt):
                board.alive = False

        self._check_match_end(dt)

    def _check_match_end(self, dt):
        # modo contrarreloj: temporizador compartido
        if self.mode == C.MODE_TIME:
            self.time_left -= dt
            self._maybe_switch_music()
            if self.time_left <= 0:
                self.time_left = 0
                self._end_match("¡Se acabó el tiempo!")
                return

        alive = [b for b in self.boards if b.alive]
        if self.players == 2:
            if self.mode == C.MODE_NORMAL:
                dead = [i for i, b in enumerate(self.boards) if not b.alive]
                if dead:                     # el primero que se llena, pierde
                    winner = 2 if dead[0] == 0 else 1
                    self._end_match("¡Un contenedor se llenó!", winner=winner)
            elif not alive:                  # contrarreloj: ambos llenos antes de tiempo
                self._end_match("¡Ambos contenedores se llenaron!")
        elif not alive:
            self._end_match("¡El contenedor se llenó!")

    def _end_match(self, reason, winner=None):
        self._play_end_music()               # bridge1 en las pantallas finales
        self.game_over_reason = reason
        if self.players == 2:
            if winner is None:
                s1, s2 = self.boards[0].score, self.boards[1].score
                winner = 1 if s1 > s2 else 2 if s2 > s1 else 0
            self.winner = winner
        else:
            self.score = self.boards[0].score
            data = SC.save_score(self.mode, self.score)
            self.final_scores = data[self.mode]
            self.best = max(self.best, self.score)
        self.state = GAME_OVER

    # ================================================================ dibujo
    def draw(self, mouse):
        s = self.screen
        s.fill(C.BG_COLOR)
        ui.draw_header(s)

        if self.state == MENU:
            self._draw_menu(mouse)
        elif self.state == INSTRUCTIONS:
            self._draw_instructions(mouse)
        else:
            self._draw_playfield(mouse)
            if self.state == PLAYING:
                self._draw_time_notice()
            if self.state == GAME_OVER:
                self._draw_game_over(mouse)

    # ---------------------------------------------------------------- menú
    def _draw_menu(self, mouse):
        s = self.screen
        cx = C.WIDTH // 2
        ui.decorative_fruits(s, self.t)
        ui.draw_text(s, "FRUTAZO", ui.FONT_XL, ui.TEXT_LIGHT, (cx, 200))
        ui.draw_text(s, "¡Fusiona frutas y llega a la sandía!", ui.FONT_MD,
                     C.PANEL_COLOR, (cx, 290))
        draw_fruit(s, (cx - 390, 200), 51, C.MAX_TIER, self.t)
        draw_fruit(s, (cx + 390, 200), 51, C.MAX_TIER, -self.t)

        ui.draw_text(s, "Control:", ui.FONT_MD, ui.TEXT_LIGHT, (cx, 440))
        self.btn_mouse.draw(s, mouse)
        self.btn_camera.draw(s, mouse)
        ui.draw_text(s, "Jugadores:", ui.FONT_MD, ui.TEXT_LIGHT, (cx, 590))
        self.btn_1p.draw(s, mouse)
        self.btn_2p.draw(s, mouse)
        ui.draw_text(s, "Modo de juego:", ui.FONT_MD, ui.TEXT_LIGHT, (cx, 740))
        self.btn_normal.draw(s, mouse)
        self.btn_time.draw(s, mouse)
        self.btn_play.draw(s, mouse)
        if self.camera_error:
            ui.draw_text(s, self.camera_error, ui.FONT_SM, C.DANGER_COLOR, (cx, 1035))
        elif self.players == 2:
            if self.control == C.CTRL_CAMERA:
                hint = "(Camara: J1 con su mano DERECHA, J2 con su mano IZQUIERDA)"
            else:
                hint = "(2 jugadores usa teclado: A/D/S y flechas)"
            ui.draw_text(s, hint, ui.FONT_SM, C.PANEL_COLOR, (cx, 1035))

    # ---------------------------------------------------------- instrucciones
    def _draw_instructions(self, mouse):
        s = self.screen
        panel = pygame.Rect(0, 0, 1020, 750)
        panel.center = (C.WIDTH // 2, C.HEIGHT // 2 - 15)
        ui.draw_panel(s, panel)
        ui.draw_text(s, "¿Cómo se juega?", ui.FONT_LG, ui.TEXT_DARK,
                     (panel.centerx, panel.y + 70))

        if self.players == 2 and self.control == C.CTRL_CAMERA:
            lines = [
                "Pantalla dividida: ¡el de más puntos gana!",
                "Cada jugador usa UNA mano frente a la camara:",
                "Jugador 1 (izquierda):  su mano DERECHA",
                "Jugador 2 (derecha):  su mano IZQUIERDA",
                "[Puño cerrado] mueve la fruta; [mano abierta] la suelta.",
            ]
        elif self.players == 2:
            lines = [
                "Pantalla dividida: ¡el de más puntos gana!",
                "Jugador 1 (izquierda):  mover  A / D,   soltar  S",
                "Jugador 2 (derecha):  mover  flechas Izq / Der,",
                "                                  soltar  flecha Abajo",
            ]
        elif self.control == C.CTRL_MOUSE:
            lines = [
                "Mueve el mouse para posicionar la fruta.",
                "Clic izquierdo (o ESPACIO) para soltarla.",
            ]
        else:
            lines = [
                "[Puño cerrado] SOSTIENES y mueves la fruta.",
                "[Mano abierta] SUELTAS la fruta.",
                "La mano solo mueve la fruta de arriba.",
            ]
        lines += [
            "",
            "Dos frutas iguales se fusionan en una más grande",
            "y suman puntos. ¡La meta es llegar a la sandía!",
            "Si se apilan sobre la línea roja, se termina.",
        ]
        if self.players == 2 and self.mode == C.MODE_NORMAL:
            lines += ["", "Normal: pierde el primero que llene su contenedor."]
        if self.mode == C.MODE_TIME:
            lines += [
                "",
                "Contrarreloj: máximo puntaje en 3 minutos.",
                "Al último minuto la música cambia y aparece un aviso.",
            ]

        y = panel.y + 150
        for line in lines:
            ui.draw_text(s, line, ui.FONT_SM, ui.TEXT_DARK, (panel.centerx, y), shadow=False)
            y += 42
        self.btn_accept.rect.center = (panel.centerx, panel.bottom - 63)
        self.btn_accept.draw(s, mouse)

    # ------------------------------------------------------------- gameplay
    def _draw_playfield(self, mouse):
        if self.players == 2:
            self._draw_versus()
        else:
            self._draw_single()

    def _draw_container(self, board):
        """Contenedor + línea de peligro + guía + frutas + fruta en el dispensador."""
        s = self.screen
        c = board.bounds
        rect = pygame.Rect(c["left"], c["top"], c["right"] - c["left"], c["bottom"] - c["top"])
        frame = rect.inflate(c["wall"] * 2, c["wall"] * 2)
        bg = scaled_image("background.png", frame.size)
        if bg:
            s.blit(bg, frame.topleft)
        else:
            pygame.draw.rect(s, C.CONTAINER_FILL, rect)
            pygame.draw.rect(s, C.CONTAINER_EDGE, rect, c["wall"])

        # línea de peligro (punteada)
        x = c["left"] + 9
        while x < c["right"] - 9:
            pygame.draw.line(s, C.DANGER_COLOR, (x, board.danger_y),
                             (min(x + 21, c["right"] - 9), board.danger_y), 4)
            x += 39

        # guía vertical del dispensador
        r = C.FRUITS[board.current_tier][1] * board.scale
        gx = int(board.clamp_x(board.dropper_x))
        y = c["top"] - 15
        while y < c["bottom"] - 15:
            pygame.draw.line(s, (120, 90, 60), (gx, y), (gx, y + 12), 3)
            y += 30

        for f in board.fruits:
            f.draw(s)

        # nube del dispensador (detrás de la fruta, estilo Suika); nunca
        # sube más allá del header — con frutas grandes queda tras la fruta
        drop_y = c["top"] - C.DROP_HEIGHT
        if board.alive:
            cloud = scaled_image("player.png", (144, 104))
            if cloud:
                cy = max(drop_y - r - 33, C.HEADER_H + 56)
                s.blit(cloud, cloud.get_rect(center=(gx, cy)))
        if board.alive and board.cooldown <= 0:
            draw_fruit(s, (gx, drop_y), r, board.current_tier)
        if not board.alive:
            veil = pygame.Surface((c["right"] - c["left"], c["bottom"] - c["top"]), pygame.SRCALPHA)
            veil.fill((60, 30, 10, 150))
            s.blit(veil, (c["left"], c["top"]))
            ui.draw_text(s, "¡Lleno!", ui.FONT_LG, C.DANGER_COLOR,
                         ((c["left"] + c["right"]) // 2, (c["top"] + c["bottom"]) // 2))

    def _draw_single(self):
        s = self.screen
        board = self.boards[0]
        self._draw_container(board)

        # HUD izquierda: score + leaderboard
        ui.draw_bubble(s, (262, 315), 142, [
            ("Score", ui.FONT_MD, ui.TEXT_LIGHT),
            (str(board.score), ui.FONT_LG, C.PANEL_COLOR),
            (f"Récord: {self.best}", ui.FONT_SM, ui.TEXT_LIGHT),
        ])
        lb = pygame.Rect(90, 510, 345, 480)
        ui.draw_leaderboard(s, lb, SC.load_scores()[self.mode])

        # HUD derecha: next + evolución
        rx = C.WIDTH - 262
        ui.draw_text(s, "Siguiente", ui.FONT_MD, ui.TEXT_LIGHT, (rx, 195))
        ui.draw_bubble(s, (rx, 345), 112, [])
        draw_fruit(s, (rx, 345), C.FRUITS[board.next_tier][1] * 0.7, board.next_tier)
        ui.draw_evolution_ring(s, (rx, 750))

        # temporizador contrarreloj
        if self.mode == C.MODE_TIME and self.state == PLAYING:
            self._draw_timer(C.WIDTH // 2, 150)

        # indicador de mano (modo cámara)
        if self.control == C.CTRL_CAMERA and self.state == PLAYING:
            if self.tracker and self.tracker.detected:
                txt = "Sosteniendo (puño)" if self.tracker.closed else "Mano abierta"
                col = (90, 200, 90)
            else:
                txt, col = "No detecto tu mano", C.DANGER_COLOR
            ui.draw_text(s, txt, ui.FONT_SM, col, (C.WIDTH // 2, 117))

    def _draw_versus(self):
        s = self.screen
        cx_mid = C.WIDTH // 2
        ui.draw_text(s, "VS", ui.FONT_XL, C.PANEL_COLOR, (cx_mid, 420))

        for i, board in enumerate(self.boards):
            self._draw_container(board)
            c = board.bounds
            cx = (c["left"] + c["right"]) // 2
            ui.draw_text(s, board.label, ui.FONT_MD, board.accent, (cx, 120))
            ui.draw_text(s, f"Score: {board.score}", ui.FONT_MD, ui.TEXT_LIGHT, (cx, 177))
            # siguiente fruta (columna central, bajo el VS / temporizador)
            px = cx_mid - 140 if i == 0 else cx_mid + 140
            ui.draw_text(s, "Sig.", ui.FONT_SM, board.accent, (px, 700))
            draw_fruit(s, (px, 775),
                       C.FRUITS[board.next_tier][1] * 0.55 * board.scale, board.next_tier)
            # recordatorio de controles + estado de la mano (modo cámara)
            if board.control == C.CTRL_CAMERA:
                hint = ("Mano DERECHA - abrir suelta" if board.hand == "Right"
                        else "Mano IZQUIERDA - abrir suelta")
                st = self.tracker.hand(board.hand) if self.tracker else None
                if self.state == PLAYING:
                    if st and st.detected:
                        txt, col = ("Sosteniendo (puño)" if st.closed
                                    else "Mano abierta"), (90, 200, 90)
                    else:
                        txt, col = "No detecto la mano", C.DANGER_COLOR
                    ui.draw_text(s, txt, ui.FONT_SM, col, (cx, 228))
            elif board.keys.get("drop") == pygame.K_s:
                hint = "A / D  -  soltar S"
            else:
                hint = "Flechas  -  soltar Abajo"
            ui.draw_text(s, hint, ui.FONT_SM, ui.TEXT_LIGHT, (cx, 1050))

        if self.mode == C.MODE_TIME and self.state == PLAYING:
            self._draw_timer(cx_mid, 560)

    def _draw_timer(self, cx, cy):
        m, sec = divmod(int(self.time_left), 60)
        color = C.DANGER_COLOR if self.time_left < 15 else ui.TEXT_LIGHT
        ui.draw_text(self.screen, f"{m}:{sec:02d}", ui.FONT_LG, color, (cx, cy))

    def _draw_time_notice(self):
        if self.time_notice <= 0:
            return
        s = self.screen
        pulse = 0.5 + 0.5 * math.sin(self.t * 8)
        box = pygame.Rect(0, 0, 480, 69)
        box.center = (C.WIDTH // 2, C.HEIGHT - 40)
        veil = pygame.Surface(box.size, pygame.SRCALPHA)
        veil.fill((220, 60, 60, int(150 + 80 * pulse)))
        s.blit(veil, box.topleft)
        ui.draw_text(s, "¡Queda 1 minuto!", ui.FONT_MD, ui.TEXT_LIGHT, box.center, shadow=False)

    # ------------------------------------------------------------- game over
    def _draw_game_over(self, mouse):
        if self.players == 2:
            self._draw_versus_over(mouse)
        else:
            self._draw_single_over(mouse)

    def _draw_single_over(self, mouse):
        s = self.screen
        veil = pygame.Surface((C.WIDTH, C.HEIGHT), pygame.SRCALPHA)
        veil.fill((60, 30, 10, 130))
        s.blit(veil, (0, 0))

        panel = pygame.Rect(0, 0, 630, 700)
        panel.center = (C.WIDTH // 2, C.HEIGHT // 2)
        ui.draw_panel(s, panel)
        ui.draw_text(s, "Tu puntaje", ui.FONT_LG, ui.TEXT_DARK, (panel.centerx, panel.y + 80))
        ui.draw_text(s, str(self.score), ui.FONT_XL, C.HEADER_COLOR, (panel.centerx, panel.y + 185))
        ui.draw_text(s, self.game_over_reason, ui.FONT_SM, ui.TEXT_DARK, (panel.centerx, panel.y + 268), shadow=False)
        ui.draw_text(s, f"Mejor puntaje: {self.best}", ui.FONT_MD, ui.TEXT_DARK, (panel.centerx, panel.y + 330))
        if self.score == self.best and self.score > 0:
            ui.draw_text(s, "¡Nuevo récord!", ui.FONT_MD, (200, 120, 20), (panel.centerx, panel.y + 385))

        self.btn_again.rect.center = (panel.centerx, panel.y + 500)
        self.btn_menu.rect.center = (panel.centerx, panel.y + 605)
        self.btn_again.draw(s, mouse)
        self.btn_menu.draw(s, mouse)

    def _draw_versus_over(self, mouse):
        s = self.screen
        veil = pygame.Surface((C.WIDTH, C.HEIGHT), pygame.SRCALPHA)
        veil.fill((60, 30, 10, 150))
        s.blit(veil, (0, 0))

        panel = pygame.Rect(0, 0, 690, 660)
        panel.center = (C.WIDTH // 2, C.HEIGHT // 2)
        ui.draw_panel(s, panel)

        b1, b2 = self.boards
        if self.winner == 0:
            title, col = "¡Empate!", ui.TEXT_DARK
        else:
            win = self.boards[self.winner - 1]
            title, col = f"¡Gana {win.label}!", win.accent
        ui.draw_text(s, title, ui.FONT_LG, col, (panel.centerx, panel.y + 82))
        ui.draw_text(s, self.game_over_reason, ui.FONT_SM, ui.TEXT_DARK,
                     (panel.centerx, panel.y + 150), shadow=False)
        ui.draw_text(s, f"{b1.label}:  {b1.score}", ui.FONT_MD, b1.accent, (panel.centerx, panel.y + 232))
        ui.draw_text(s, f"{b2.label}:  {b2.score}", ui.FONT_MD, b2.accent, (panel.centerx, panel.y + 300))

        self.btn_again.rect.center = (panel.centerx, panel.y + 455)
        self.btn_menu.rect.center = (panel.centerx, panel.y + 565)
        self.btn_again.draw(s, mouse)
        self.btn_menu.draw(s, mouse)
