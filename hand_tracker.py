"""
hand_tracker.py — Control por cámara con MediaPipe.

Gestos:
  ✊ Mano cerrada  -> sostener la fruta (mueve el dispensador con la mano)
  🖐 Mano abierta  -> soltar la fruta

Importa de forma segura: si opencv/mediapipe no están instalados, el juego
sigue funcionando solo con mouse.
"""

try:
    import cv2
    import mediapipe as mp
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


class HandTracker:
    """Lee la webcam y expone: x normalizada (0-1), mano cerrada o abierta,
    y el evento de 'soltar' (transición cerrada -> abierta)."""

    def __init__(self, cam_index: int = 0):
        if not AVAILABLE:
            raise RuntimeError("mediapipe/opencv no instalados")
        self.cap = cv2.VideoCapture(cam_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.hands = mp.solutions.hands.Hands(
            max_num_hands=1,
            model_complexity=0,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5,
        )
        self.hand_x = 0.5          # posición horizontal normalizada
        self.closed = False        # ¿puño cerrado?
        self.detected = False      # ¿hay mano en cámara?
        self._was_closed = False
        self.release_event = False # True solo el frame en que abre la mano

    # ------------------------------------------------------------------
    def update(self):
        """Procesa un frame. Llamar una vez por frame del juego."""
        self.release_event = False
        if not self.cap.isOpened():
            self.detected = False
            return

        ok, frame = self.cap.read()
        if not ok:
            self.detected = False
            return

        frame = cv2.flip(frame, 1)                       # espejo natural
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        if not result.multi_hand_landmarks:
            self.detected = False
            return

        self.detected = True
        lm = result.multi_hand_landmarks[0].landmark

        # posición: centro de la palma (landmark 9 = base del dedo medio)
        self.hand_x = min(1.0, max(0.0, lm[9].x))

        # puño cerrado: puntas de los dedos por DEBAJO (más cerca) de sus nudillos
        # dedos: índice(8/6), medio(12/10), anular(16/14), meñique(20/18)
        folded = 0
        for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
            if lm[tip].y > lm[pip].y:        # punta más abajo que el nudillo
                folded += 1
        now_closed = folded >= 3

        # evento de soltar: estaba cerrada y ahora abrió
        if self._was_closed and not now_closed:
            self.release_event = True

        self._was_closed = now_closed
        self.closed = now_closed

    # ------------------------------------------------------------------
    def close(self):
        if self.cap:
            self.cap.release()
        self.hands.close()
