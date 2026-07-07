"""
hand_tracker.py — Control por cámara con MediaPipe (1 o 2 manos).

Gestos:
  ✊ Mano cerrada  -> sostener la fruta (mueve el dispensador con la mano)
  🖐 Mano abierta  -> soltar la fruta

En modo 2 jugadores se detectan dos manos a la vez y se identifican por
lateralidad: la mano DERECHA controla al Jugador 1 y la IZQUIERDA al
Jugador 2 (MediaPipe clasifica cada mano; como procesamos la imagen ya
espejeada, las etiquetas corresponden a la mano real de la persona).

La captura y el procesamiento corren en un HILO aparte: `cap.read()` bloquea
hasta que la webcam entrega imagen (~33 ms) y MediaPipe con dos manos puede
tardar más que un frame del juego, así que hacerlo en el bucle principal
congela el juego constantemente. El hilo mantiene el último estado detectado
y `update()` solo copia ese snapshot; el gesto de soltar queda "latcheado"
hasta que el juego lo consume, para no perder sueltas entre frames.

Importa de forma segura: si opencv/mediapipe no están instalados, el juego
sigue funcionando solo con mouse/teclado.
"""
import threading
import time

try:
    import cv2
    import mediapipe as mp
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


class HandState:
    """Estado de una mano: posición, gesto y evento de soltar."""

    def __init__(self):
        self.hand_x = 0.5          # posición horizontal normalizada (0-1)
        self.closed = False        # ¿puño cerrado?
        self.detected = False      # ¿se ve esta mano en cámara?
        self.release_event = False # True solo el frame en que abre la mano
        self._was_closed = False
        self._pending_release = False  # soltar detectado por el hilo, aún no consumido


class HandTracker:
    """Lee la webcam en segundo plano y expone el estado de cada mano.

    - `hand()` o `hand(None)`  -> primera mano detectada (modo 1 jugador)
    - `hand("Right")`          -> mano derecha (Jugador 1 en versus)
    - `hand("Left")`           -> mano izquierda (Jugador 2 en versus)

    Mantiene además los atributos planos (hand_x, closed, detected,
    release_event) de la primera mano por compatibilidad.
    """

    def __init__(self, cam_index: int = 0, num_hands: int = 1):
        if not AVAILABLE:
            raise RuntimeError("mediapipe/opencv no instalados")
        self.cap = self._open_capture(cam_index)
        self.hands = mp.solutions.hands.Hands(
            max_num_hands=num_hands,
            model_complexity=0,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5,
        )
        # _raw: estados que escribe el hilo · states: snapshot que lee el juego
        self._raw   = {"any": HandState(), "Right": HandState(), "Left": HandState()}
        self.states = {"any": HandState(), "Right": HandState(), "Left": HandState()}
        self.hand_x = 0.5
        self.closed = False
        self.detected = False
        self.release_event = False

        self._lock = threading.Lock()
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    @staticmethod
    def _open_capture(cam_index):
        # En Windows el backend DirectShow abre y lee más rápido que MSMF
        cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(cam_index)
        if not cap.isOpened():
            cap.release()
            raise RuntimeError("no se encontró la webcam")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        return cap

    # ------------------------------------------------------------------
    def hand(self, label=None) -> HandState:
        return self.states[label or "any"]

    # ------------------------------------------------------------------
    @staticmethod
    def _update_state(st: HandState, lm):
        st.detected = True
        # posición: centro de la palma (landmark 9 = base del dedo medio)
        st.hand_x = min(1.0, max(0.0, lm[9].x))

        # puño cerrado: puntas de los dedos por DEBAJO (más cerca) de sus nudillos
        # dedos: índice(8/6), medio(12/10), anular(16/14), meñique(20/18)
        folded = 0
        for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
            if lm[tip].y > lm[pip].y:        # punta más abajo que el nudillo
                folded += 1
        now_closed = folded >= 3

        # evento de soltar: estaba cerrada y ahora abrió
        if st._was_closed and not now_closed:
            st._pending_release = True
        st._was_closed = now_closed
        st.closed = now_closed

    # ------------------------------------------------------------------ hilo
    def _capture_loop(self):
        """Corre en segundo plano al ritmo de la webcam, no del juego."""
        while self._running:
            try:
                ok, frame = self.cap.read()
                if not ok:
                    time.sleep(0.05)
                    continue
                frame = cv2.flip(frame, 1)               # espejo natural
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = self.hands.process(rgb)
            except Exception:
                time.sleep(0.05)     # un frame malo no debe tumbar el juego
                continue

            seen = set()
            with self._lock:
                if result.multi_hand_landmarks:
                    handedness = result.multi_handedness or []
                    for i, lms in enumerate(result.multi_hand_landmarks):
                        label = (handedness[i].classification[0].label
                                 if i < len(handedness) else "Right")
                        targets = []
                        if "any" not in seen:
                            targets.append("any")
                        if label not in seen:
                            targets.append(label)
                        for t in targets:
                            self._update_state(self._raw[t], lms.landmark)
                            seen.add(t)
                for name, st in self._raw.items():
                    if name not in seen:
                        st.detected = False
                        st._was_closed = False   # evita soltar fantasma al reaparecer

    # ------------------------------------------------------------------
    def update(self):
        """Copia el último estado del hilo de cámara. Llamar UNA vez por frame."""
        with self._lock:
            for name, raw in self._raw.items():
                st = self.states[name]
                st.hand_x = raw.hand_x
                st.closed = raw.closed
                st.detected = raw.detected
                st.release_event = raw._pending_release
                raw._pending_release = False

        # compatibilidad: atributos planos = primera mano detectada
        any_st = self.states["any"]
        self.hand_x = any_st.hand_x
        self.closed = any_st.closed
        self.detected = any_st.detected
        self.release_event = any_st.release_event

    # ------------------------------------------------------------------
    def close(self):
        self._running = False
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
        self.hands.close()
