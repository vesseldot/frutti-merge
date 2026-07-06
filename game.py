"""
game.py — Lógica principal: máquina de estados (menú, instrucciones, juego,
game over), física, fusiones, modos de juego y control mouse/cámara.
"""
import random
import pygame
import pymunk

import config as C
import scores as SC
import ui
from fruit import Fruit, draw_fruit, FRUIT_COLLISION_TYPE

# Estados
MENU, INSTRUCTIONS, PLAYING, GAME_OVER = "menu", "instrucciones", "jugando", "fin"


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.state = MENU
        self.mode = C.MODE_NORMAL
        self.control = C.CTRL_MOUSE
        self.tracker = None                  # HandTracker (si eligen cámara)
        self.t = 0.0                         # reloj global para animaciones

        # ---------------- botones del menú
        cx = C.WIDTH // 2
        self.btn_mouse  = ui.Button("Mouse",  (cx - 140, 360))
        self.btn_camera = ui.Button("Camara", (cx + 140, 360))
        self.btn_normal = ui.Button("Modo Normal",       (cx - 140, 470))
        self.btn_time   = ui.Button("Contrarreloj 2:00", (cx + 140, 470))
        self.btn_play   = ui.Button("¡ JUGAR !", (cx, 580), size=(280, 66), font=ui.FONT_LG)
        self.btn_mouse.selected = True
        self.btn_normal.selected = True

        self.btn_accept = ui.Button("¡Entendido, a jugar!", (cx, 620), size=(340, 60))
        self.btn_again  = ui.Button("Volver a jugar", (cx, 0))   # y se ajusta al dibujar
        self.btn_menu   = ui.Button("Menú", (cx, 0), size=(200, 50))

        self.camera_error = ""
        self.reset_match()

    # ================================================================ partida
    def reset_match(self):
        self.space = pymunk.Space()
        self.space.gravity = C.GRAVITY
        self._build_walls()
        self.space.on_collision(FRUIT_COLLISION_TYPE, FRUIT_COLLISION_TYPE,
                                begin=self._on_fruit_collision)

        self.fruits: list[Fruit] = []
        self.pending_merges = []             # [(fruta_a, fruta_b)]
        self.score = 0
        self.best = SC.best_score(self.mode)
        self.dropper_x = C.WIDTH // 2
        self.current_tier = self._random_tier()
        self.next_tier = self._random_tier()
        self.cooldown = 0.0
        self.time_left = C.TIME_ATTACK_SECONDS
        self.game_over_reason = ""
        self.final_scores = []
        self.holding = True                  # (cámara) puño cerrado = sosteniendo

    def _build_walls(self):
        c = C.CONTAINER
        w = c["wall"]
        segs = [
            pymunk.Segment(self.space.static_body, (c["left"],  c["top"] - 200), (c["left"],  c["bottom"]), w),
            pymunk.Segment(self.space.static_body, (c["right"], c["top"] - 200), (c["right"], c["bottom"]), w),
            pymunk.Segment(self.space.static_body, (c["left"],  c["bottom"]),    (c["right"], c["bottom"]), w),
        ]
        for s in segs:
            s.elasticity = C.ELASTICITY
            s.friction = 0.9
        self.space.add(*segs)

    @staticmethod
    def _random_tier():
        return random.randint(0, C.DROPPABLE_TIERS - 1)

    # ================================================================ fusiones
    def _on_fruit_collision(self, arbiter, space, data):
        a, b = arbiter.shapes
        fa, fb = getattr(a, "fruit", None), getattr(b, "fruit", None)
        if fa and fb and fa.tier == fb.tier and fa.tier < C.MAX_TIER:
            pair = (fa, fb)
            flat = [f for p in self.pending_merges for f in p]
            if fa not in flat and fb not in flat:
                self.pending_merges.append(pair)

    def _apply_merges(self):
        for fa, fb in self.pending_merges:
            if fa not in self.fruits or fb not in self.fruits:
                continue
            nx = (fa.pos.x + fb.pos.x) / 2
            ny = (fa.pos.y + fb.pos.y) / 2
            new_tier = fa.tier + 1
            fa.remove(); fb.remove()
            self.fruits.remove(fa); self.fruits.remove(fb)
            merged = Fruit(self.space, nx, ny, new_tier)
            self.fruits.append(merged)
            self.score += C.FRUITS[new_tier][4]
        self.pending_merges.clear()

    # ================================================================ soltar
    def _drop_fruit(self):
        if self.cooldown > 0:
            return
        c = C.CONTAINER
        r = C.FRUITS[self.current_tier][1]
        x = max(c["left"] + r + 14, min(c["right"] - r - 14, self.dropper_x))
        self.fruits.append(Fruit(self.space, x, c["top"] - 60, self.current_tier))
        self.current_tier = self.next_tier
        self.next_tier = self._random_tier()
        self.cooldown = C.DROP_COOLDOWN

    # ================================================================ eventos
    def handle_event(self, event, mouse):
        if self.state == MENU:
            self._menu_events(event, mouse)
        elif self.state == INSTRUCTIONS:
            if self.btn_accept.clicked(event, mouse) or \
               (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
                self.state = PLAYING
        elif self.state == PLAYING:
            if self.control == C.CTRL_MOUSE:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._drop_fruit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self._drop_fruit()
        elif self.state == GAME_OVER:
            if self.btn_again.clicked(event, mouse):
                self.reset_match()
                self.state = PLAYING
            if self.btn_menu.clicked(event, mouse):
                self._close_camera()
                self.reset_match()
                self.state = MENU

    def _menu_events(self, event, mouse):
        if self.btn_mouse.clicked(event, mouse):
            self.btn_mouse.selected, self.btn_camera.selected = True, False
            self.control = C.CTRL_MOUSE
            self.camera_error = ""
        if self.btn_camera.clicked(event, mouse):
            self.btn_camera.selected, self.btn_mouse.selected = True, False
            self.control = C.CTRL_CAMERA
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
            self.tracker = hand_tracker.HandTracker()
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

        self.cooldown = max(0.0, self.cooldown - dt)

        # --- control del dispensador (SOLO controla la fruta de arriba,
        #     nunca toca las que ya cayeron al contenedor)
        if self.control == C.CTRL_MOUSE:
            self.dropper_x = mouse[0]
        elif self.tracker:
            self.tracker.update()
            if self.tracker.detected:
                c = C.CONTAINER
                span = (c["right"] - c["left"])
                if self.tracker.closed:      # ✊ sosteniendo: la mano mueve la fruta
                    self.dropper_x = c["left"] + self.tracker.hand_x * span
                if self.tracker.release_event:   # 🖐 abrió la mano: suelta
                    self._drop_fruit()

        # --- física (sub-pasos para estabilidad)
        for _ in range(2):
            self.space.step(dt / 2)
        self._apply_merges()
        for f in self.fruits:
            f.update(dt)

        # --- límite superior: fruta quieta sobre la línea => game over
        for f in self.fruits:
            over = f.pos.y - f.radius < C.DANGER_Y
            if over and f.is_settled(C.SETTLE_SPEED):
                f.danger_timer += dt
                if f.danger_timer >= C.DANGER_TIME:
                    self._end_game("¡El contenedor se llenó!")
                    return
            else:
                f.danger_timer = 0.0

        # --- modo contrarreloj
        if self.mode == C.MODE_TIME:
            self.time_left -= dt
            if self.time_left <= 0:
                self.time_left = 0
                self._end_game("¡Se acabó el tiempo!")

    def _end_game(self, reason):
        self.game_over_reason = reason
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
            if self.state == GAME_OVER:
                self._draw_game_over(mouse)

    # ---------------------------------------------------------------- menú
    def _draw_menu(self, mouse):
        s = self.screen
        cx = C.WIDTH // 2
        ui.decorative_fruits(s, self.t)
        ui.draw_text(s, "Frutti Merge", ui.FONT_XL, ui.TEXT_LIGHT, (cx, 150))
        ui.draw_text(s, "¡Fusiona frutas y llega a la sandía!", ui.FONT_MD,
                     C.PANEL_COLOR, (cx, 215))
        draw_fruit(s, (cx - 260, 150), 34, C.MAX_TIER, self.t)
        draw_fruit(s, (cx + 260, 150), 34, C.MAX_TIER, -self.t)

        ui.draw_text(s, "Control:", ui.FONT_MD, ui.TEXT_LIGHT, (cx, 315))
        self.btn_mouse.draw(s, mouse)
        self.btn_camera.draw(s, mouse)
        ui.draw_text(s, "Modo de juego:", ui.FONT_MD, ui.TEXT_LIGHT, (cx, 425))
        self.btn_normal.draw(s, mouse)
        self.btn_time.draw(s, mouse)
        self.btn_play.draw(s, mouse)
        if self.camera_error:
            ui.draw_text(s, self.camera_error, ui.FONT_SM, C.DANGER_COLOR, (cx, 645))

    # ---------------------------------------------------------- instrucciones
    def _draw_instructions(self, mouse):
        s = self.screen
        panel = pygame.Rect(0, 0, 660, 470)
        panel.center = (C.WIDTH // 2, C.HEIGHT // 2 - 20)
        ui.draw_panel(s, panel)
        ui.draw_text(s, "¿Cómo se juega?", ui.FONT_LG, ui.TEXT_DARK,
                     (panel.centerx, panel.y + 50))

        if self.control == C.CTRL_MOUSE:
            lines = [
                "Mueve el mouse para posicionar la fruta.",
                "Clic izquierdo (o ESPACIO) para soltarla.",
            ]
        else:
            lines = [
                "[Puño cerrado] SOSTIENES y mueves la fruta.",
                "[Mano abierta] SUELTAS la fruta.",
                "La mano solo mueve la fruta de arriba,",
                "no puede tocar las que ya cayeron.",
            ]
        lines += [
            "",
            "Dos frutas iguales se fusionan en una más grande",
            "y suman puntos. ¡La meta es llegar a la sandía!",
            "",
            "OJO: si las frutas se apilan sobre la línea roja,",
            "se termina la partida.",
        ]
        if self.mode == C.MODE_TIME:
            lines += ["", "Contrarreloj: haz el máximo puntaje en 2 minutos."]

        y = panel.y + 105
        for line in lines:
            ui.draw_text(s, line, ui.FONT_SM, ui.TEXT_DARK, (panel.centerx, y), shadow=False)
            y += 28
        self.btn_accept.rect.center = (panel.centerx, panel.bottom - 45)
        self.btn_accept.draw(s, mouse)

    # ------------------------------------------------------------- gameplay
    def _draw_playfield(self, mouse):
        s = self.screen
        c = C.CONTAINER

        # contenedor
        rect = pygame.Rect(c["left"], c["top"], c["right"] - c["left"], c["bottom"] - c["top"])
        pygame.draw.rect(s, C.CONTAINER_FILL, rect)
        pygame.draw.rect(s, C.CONTAINER_EDGE, rect, c["wall"])
        # línea de peligro (punteada)
        x = c["left"] + 6
        while x < c["right"] - 6:
            pygame.draw.line(s, C.DANGER_COLOR, (x, C.DANGER_Y), (min(x + 14, c["right"] - 6), C.DANGER_Y), 3)
            x += 26

        # guía vertical del dispensador
        r = C.FRUITS[self.current_tier][1]
        gx = max(c["left"] + r + 14, min(c["right"] - r - 14, int(self.dropper_x)))
        y = c["top"] - 10
        while y < c["bottom"] - 10:
            pygame.draw.line(s, (120, 90, 60), (gx, y), (gx, y + 8), 2)
            y += 20

        # frutas
        for f in self.fruits:
            f.draw(s)

        # fruta en el dispensador (bloqueada durante cooldown)
        if self.cooldown <= 0:
            draw_fruit(s, (gx, c["top"] - 60), r, self.current_tier)

        # ---------------- HUD izquierda: score + leaderboard
        ui.draw_bubble(s, (160, 210), 95, [
            ("Score", ui.FONT_MD, ui.TEXT_LIGHT),
            (str(self.score), ui.FONT_LG, C.PANEL_COLOR),
            (f"Récord: {self.best}", ui.FONT_SM, ui.TEXT_LIGHT),
        ])
        lb = pygame.Rect(45, 340, 230, 320)
        ui.draw_leaderboard(s, lb, SC.load_scores()[self.mode])

        # ---------------- HUD derecha: next + evolución
        ui.draw_text(s, "Siguiente", ui.FONT_MD, ui.TEXT_LIGHT, (845, 130))
        ui.draw_bubble(s, (845, 230), 75, [])
        draw_fruit(s, (845, 230), C.FRUITS[self.next_tier][1] * 0.7, self.next_tier)
        ui.draw_evolution_ring(s, (845, 500))

        # modo contrarreloj: temporizador
        if self.mode == C.MODE_TIME and self.state == PLAYING:
            m, sec = divmod(int(self.time_left), 60)
            color = C.DANGER_COLOR if self.time_left < 15 else ui.TEXT_LIGHT
            ui.draw_text(s, f"{m}:{sec:02d}", ui.FONT_LG, color, (C.WIDTH // 2, 100))

        # indicador de mano (modo cámara)
        if self.control == C.CTRL_CAMERA and self.state == PLAYING:
            if self.tracker and self.tracker.detected:
                txt = "Sosteniendo (puño)" if self.tracker.closed else "Mano abierta"
                col = (90, 200, 90)
            else:
                txt, col = "No detecto tu mano", C.DANGER_COLOR
            ui.draw_text(s, txt, ui.FONT_SM, col, (C.WIDTH // 2, 78))

    # ------------------------------------------------------------- game over
    def _draw_game_over(self, mouse):
        s = self.screen
        veil = pygame.Surface((C.WIDTH, C.HEIGHT), pygame.SRCALPHA)
        veil.fill((60, 30, 10, 130))
        s.blit(veil, (0, 0))

        panel = pygame.Rect(0, 0, 420, 380)
        panel.center = (C.WIDTH // 2, C.HEIGHT // 2)
        ui.draw_panel(s, panel)
        ui.draw_text(s, "Tu puntaje", ui.FONT_LG, ui.TEXT_DARK, (panel.centerx, panel.y + 55))
        ui.draw_text(s, str(self.score), ui.FONT_XL, C.HEADER_COLOR, (panel.centerx, panel.y + 125))
        ui.draw_text(s, self.game_over_reason, ui.FONT_SM, ui.TEXT_DARK, (panel.centerx, panel.y + 180), shadow=False)
        ui.draw_text(s, f"Mejor puntaje: {self.best}", ui.FONT_MD, ui.TEXT_DARK, (panel.centerx, panel.y + 220))
        if self.score == self.best and self.score > 0:
            ui.draw_text(s, "¡Nuevo récord!", ui.FONT_MD, (200, 120, 20), (panel.centerx, panel.y + 255))

        self.btn_again.rect.center = (panel.centerx, panel.bottom - 90)
        self.btn_menu.rect.center = (panel.centerx, panel.bottom - 35)
        self.btn_again.draw(s, mouse)
        self.btn_menu.draw(s, mouse)
