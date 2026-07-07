# FRUTAZO ^^ (juego tipo Suika) — Python + Pygame + Pymunk

Juego de fusión de frutas con físicas reales, control por **mouse**, por **cámara** (gestos de mano con MediaPipe) o **dos jugadores** en teclado, dos modos de juego, música dinámica y leaderboard persistente. Corre en **pantalla completa** (se escala manteniendo proporción).

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

Teclas globales: **ESC** = salir · **F11** = alternar pantalla completa / ventana.

## Cómo se juega

- **Menú (Fase 1):** elige control (Mouse / Cámara), jugadores (1 / 2) y modo (Normal / Contrarreloj 3:00), luego ¡JUGAR!
- **Instrucciones (Fase 2):** pantalla explicativa; presiona "¡Entendido, a jugar!" o ENTER.
- **Juego (Fase 3):**
  - **Mouse:** mueve para posicionar, clic izquierdo o ESPACIO para soltar.
  - **Cámara:** ✊ puño cerrado = sostener/mover la fruta; 🖐 abrir la mano = soltarla.
    La mano SOLO controla la fruta del dispensador — nunca las que ya cayeron.
  - **2 jugadores (pantalla dividida):** Jugador 1 → mover `A`/`D`, soltar `S`.
    Jugador 2 → mover `←`/`→`, soltar `↓`. Gana quien tenga más puntos (en Normal,
    pierde el primero que llene su contenedor).
  - **2 jugadores + cámara:** una sola webcam detecta ambas manos a la vez.
    Jugador 1 usa su mano **derecha** (mitad izquierda de la cámara) y
    Jugador 2 su mano **izquierda** (mitad derecha). Puño = mover, abrir = soltar.
- Dos frutas iguales se fusionan en la siguiente de la evolución y suman puntos.
- Si una fruta queda apilada sobre la línea roja punteada ~2 segundos → fin de partida.
- **Contrarreloj:** 3 minutos; al quedar 1 minuto la música cambia y aparece un aviso.
- Al terminar: pantalla de puntaje, se guarda en `scores.json` y aparece en el
  leaderboard (top 5 por modo), con botones de "Volver a jugar" y "Menú".

## Música (en `Assets/music/`)

- `musica5` → pantalla de título / instrucciones.
- `musica1`, `musica3`, `musica4`, `musica6` → una al azar en cada partida nueva.
- `musica2` → último minuto del contrarreloj.
- `bridge1` → pantallas finales (game over).
- `pop.wav` → efecto de fusión.

## Imágenes (en `Assets/imagenes/`)

- `0.png` … `10.png` → sprites de las frutas (cereza → sandía). El círculo del
  cuerpo se detecta automáticamente desde el canal alpha para que el dibujo
  coincida exactamente con el hitbox de física.
- `background.png` → contenedor · `bubble.png` → burbujas del HUD ·
  `evolution.png` → anillo de evolución · `player.png` → nube del dispensador.
- Si falta algún PNG, el juego usa el dibujo procedural original como respaldo.

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
