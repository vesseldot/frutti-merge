# Frutti Merge (juego tipo Suika) — Python + Pygame + Pymunk

Juego de fusión de frutas con físicas reales, control por **mouse** o por **cámara** (gestos de mano con MediaPipe), dos modos de juego y leaderboard persistente.

## Instalación

```bash
python -m pip install pygame pymunk
```

Para el modo cámara (opcional):

```bash
python -m pip install opencv-python mediapipe
```

> Nota: usa `python -m pip install` (como ya sabes por tu setup de Git Bash 😉).
> Si mediapipe no está instalado, el juego funciona igual solo con mouse.

## Ejecutar

```bash
python main.py
```

## Cómo se juega

- **Menú (Fase 1):** elige control (Mouse / Cámara) y modo (Normal / Contrarreloj 2:00), luego ¡JUGAR!
- **Instrucciones (Fase 2):** pantalla explicativa; presiona "¡Entendido, a jugar!" o ENTER.
- **Juego (Fase 3):**
  - **Mouse:** mueve para posicionar, clic izquierdo o ESPACIO para soltar.
  - **Cámara:** ✊ puño cerrado = sostener/mover la fruta; 🖐 abrir la mano = soltarla.
    La mano SOLO controla la fruta del dispensador — nunca las que ya cayeron.
- Dos frutas iguales se fusionan en la siguiente de la evolución y suman puntos.
- Si una fruta queda apilada sobre la línea roja punteada ~2 segundos → fin de partida.
- Al terminar: pantalla de puntaje, se guarda en `scores.json` y aparece en el
  leaderboard (top 5 por modo), con botones de "Volver a jugar" y "Menú".

## Evolución de frutas (11 niveles)

Cereza → Fresa → Uva → Mandarina → Naranja → Manzana → Pera → Durazno → Piña → Melón → Sandía

## Estructura del proyecto

| Archivo | Responsabilidad |
|---|---|
| `main.py` | Punto de entrada y game loop |
| `game.py` | Máquina de estados, física, fusiones, modos |
| `fruit.py` | Clase `Fruit` (pymunk) + dibujo kawaii procedural |
| `ui.py` | Botones, paneles, HUD, leaderboard, anillo de evolución |
| `hand_tracker.py` | Gestos de mano con MediaPipe (import opcional) |
| `scores.py` | Persistencia del top 5 en JSON |
| `config.py` | Todas las constantes ajustables |

## Ajustes rápidos (config.py)

- `GRAVITY`, `ELASTICITY`, `FRICTION` — sensación de la física
- `DROP_COOLDOWN` — tiempo entre lanzamientos
- `DANGER_TIME` — segundos de tolerancia sobre la línea roja
- `TIME_ATTACK_SECONDS` — duración del contrarreloj
- `FRUITS` — nombres, tamaños, colores y puntos de cada nivel
