"""
main.py — Punto de entrada de Frutti Merge (juego tipo Suika).

Requisitos:
    pip install pygame pymunk
Opcional (para control por cámara):
    pip install opencv-python mediapipe
"""
import pygame

import config as C
from game import Game


def main():
    pygame.init()
    screen = pygame.display.set_mode((C.WIDTH, C.HEIGHT))
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
