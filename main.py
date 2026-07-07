"""
main.py — Punto de entrada de FRUTAZO ^^ (juego tipo Suika).

Requisitos:
    pip install pygame pymunk
Opcional (para control por cámara):
    pip install opencv-python mediapipe

El juego se dibuja siempre a la resolución lógica (C.WIDTH x C.HEIGHT) y pygame
la escala a pantalla completa con SCALED (mantiene proporción y traduce el mouse).
ESC = salir · F11 = alternar pantalla completa / ventana.
"""
import os

# filtro de alta calidad al escalar la ventana a la resolución del monitor
# (debe fijarse ANTES de pygame.init)
os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "best")

import pygame

import config as C
from game import Game


def main():
    pygame.init()
    try:
        screen = pygame.display.set_mode((C.WIDTH, C.HEIGHT),
                                         pygame.SCALED | pygame.FULLSCREEN, vsync=1)
    except pygame.error:                          # respaldo: ventana escalable
        screen = pygame.display.set_mode((C.WIDTH, C.HEIGHT), pygame.SCALED)
    pygame.display.set_caption(C.TITLE)
    clock = pygame.time.Clock()

    game = Game(screen)
    running = True
    while running:
        dt = clock.tick(C.FPS) / 1000.0
        dt = min(dt, 1 / 30)                     # evita saltos de física
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            else:
                game.handle_event(event, mouse)

        game.update(dt, mouse)
        game.draw(mouse)
        pygame.display.flip()

    if game.tracker:
        game.tracker.close()
    pygame.quit()


if __name__ == "__main__":
    main()
