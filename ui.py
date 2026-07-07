"""
ui.py — Elementos de interfaz: botones, paneles, HUD, menú, instrucciones
y pantalla de game over. Estilo cálido y amigable tipo Suika.
"""
import math
import pygame

from config import (WIDTH, HEIGHT, HEADER_H, HEADER_COLOR, PANEL_COLOR,
                    PANEL_BORDER, TEXT_DARK, TEXT_LIGHT, BTN_COLOR, BTN_HOVER,
                    BTN_TEXT, FRUITS, MAX_TIER, TITLE)
from fruit import draw_fruit, scaled_image

pygame.font.init()
FONT_XL = pygame.font.SysFont("arialrounded, arial", 96, bold=True)
FONT_LG = pygame.font.SysFont("arialrounded, arial", 60, bold=True)
FONT_MD = pygame.font.SysFont("arialrounded, arial", 42, bold=True)
FONT_SM = pygame.font.SysFont("arialrounded, arial", 30)


# ====================================================================== básicos
def draw_text(screen, text, font, color, center, shadow=True):
    if shadow:
        sh = font.render(text, True, (0, 0, 0))
        sh.set_alpha(70)
        screen.blit(sh, sh.get_rect(center=(center[0] + 2, center[1] + 3)))
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(center=center))


def draw_panel(screen, rect, radius=30):
    pygame.draw.rect(screen, PANEL_BORDER, rect.inflate(14, 14), border_radius=radius + 6)
    pygame.draw.rect(screen, PANEL_COLOR, rect, border_radius=radius)


class Button:
    def __init__(self, text, center, size=(360, 86), font=FONT_MD):
        self.text = text
        self.font = font
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center
        self.selected = False

    def hovered(self, mouse):
        return self.rect.collidepoint(mouse)

    def draw(self, screen, mouse):
        color = BTN_HOVER if (self.hovered(mouse) or self.selected) else BTN_COLOR
        shadow = self.rect.move(0, 6)
        pygame.draw.rect(screen, (170, 90, 20), shadow, border_radius=27)
        pygame.draw.rect(screen, color, self.rect, border_radius=27)
        if self.selected:
            pygame.draw.rect(screen, TEXT_LIGHT, self.rect, 4, border_radius=27)
        draw_text(screen, self.text, self.font, BTN_TEXT, self.rect.center, shadow=False)

    def clicked(self, event, mouse):
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.hovered(mouse))


# ====================================================================== HUD
def draw_bubble(screen, center, radius, lines):
    """Burbuja translúcida (marcador / next) con líneas de texto (texto, fuente, color)."""
    img = scaled_image("bubble.png", (radius * 2 + 8, radius * 2 + 8))
    if img:
        screen.blit(img, img.get_rect(center=center))
    else:
        bubble = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(bubble, (255, 255, 255, 60), (radius + 4, radius + 4), radius)
        pygame.draw.circle(bubble, (255, 255, 255, 120), (radius + 4, radius + 4), radius, 3)
        pygame.draw.circle(bubble, (255, 255, 255, 150),
                           (int(radius * 0.55), int(radius * 0.5)), radius // 6)
        screen.blit(bubble, (center[0] - radius - 4, center[1] - radius - 4))
    total = sum(f.get_height() for _, f, _ in lines) + (len(lines) - 1) * 4
    y = center[1] - total // 2
    for text, font, color in lines:
        draw_text(screen, text, font, color, (center[0], y + font.get_height() // 2))
        y += font.get_height() + 4


def draw_evolution_ring(screen, center, ring_radius=142):
    """Anillo con la evolución de las frutas (de menor a mayor, en círculo)."""
    draw_text(screen, "Evolución", FONT_MD, TEXT_LIGHT, (center[0], center[1] - ring_radius - 55))
    img_w = int(ring_radius * 2.55)
    img = scaled_image("evolution.png", (img_w, int(img_w * 400 / 423)))
    if img:
        screen.blit(img, img.get_rect(center=center))
        return
    n = MAX_TIER + 1
    for i in range(n):
        ang = -math.pi / 2 + i * (2 * math.pi / n)
        px = int(center[0] + math.cos(ang) * ring_radius)
        py = int(center[1] + math.sin(ang) * ring_radius)
        size = 15 + i * 3
        draw_fruit(screen, (px, py), size, i)
        if i < n - 1:                                    # flechita entre frutas
            ang2 = ang + (2 * math.pi / n) / 2
            ax = int(center[0] + math.cos(ang2) * ring_radius)
            ay = int(center[1] + math.sin(ang2) * ring_radius)
            pygame.draw.circle(screen, (255, 255, 255, 200), (ax, ay), 4)


def draw_leaderboard(screen, rect, scores):
    """Panel de leaderboard con top 5."""
    draw_panel(screen, rect)
    draw_text(screen, "Leaderboard", FONT_MD, TEXT_DARK, (rect.centerx, rect.y + 50))
    medal_colors = [(250, 200, 60), (150, 180, 250), (210, 150, 100),
                    (170, 170, 170), (150, 150, 150)]
    for i in range(5):
        y = rect.y + 112 + i * 69
        bar = pygame.Rect(rect.x + 27, y, rect.width - 54, 54)
        pygame.draw.rect(screen, medal_colors[i], bar, border_radius=27)
        pygame.draw.circle(screen, (255, 255, 255), (bar.x + 27, bar.centery), 21)
        draw_text(screen, str(i + 1), FONT_SM, TEXT_DARK, (bar.x + 27, bar.centery), shadow=False)
        value = str(scores[i]) if i < len(scores) else "---"
        draw_text(screen, value, FONT_MD, TEXT_LIGHT, bar.center, shadow=False)


def draw_header(screen):
    pygame.draw.rect(screen, HEADER_COLOR, (0, 0, WIDTH, HEADER_H))
    draw_fruit(screen, (WIDTH // 2 - 195, HEADER_H // 2), 24, MAX_TIER)
    draw_text(screen, TITLE.replace(" 🍉", ""), FONT_MD, TEXT_LIGHT,
              (WIDTH // 2 + 15, HEADER_H // 2))


# ====================================================================== pantallas
def decorative_fruits(screen, t):
    """Frutas flotando de fondo en los menús (repartidas a lo ancho)."""
    n = 9
    for i in range(n):
        x = WIDTH * (i + 0.5) / n
        y = HEIGHT - 135 + math.sin(t * 1.5 + i) * 27
        draw_fruit(screen, (int(x), int(y)), 33 + (i % 3) * 12, i % (MAX_TIER + 1))
