# 🍉 FRUTAZO ^^ — Juego de fusión de frutas 

Proyecto universitario para la materia de **Graficación** (Verano 2026).

Juego 2D estilo *Suika Game* desarrollado en **Python** con **Pygame** (gráficos) y
**Pymunk** (motor de física). El jugador deja caer frutas dentro de un contenedor;
cuando dos frutas iguales chocan se **fusionan** en la fruta del siguiente nivel y
suman puntos. La partida termina si las frutas se apilan por encima de la línea
de peligro.

Incluye control por **mouse**, por **cámara** (detección de gestos de mano con
MediaPipe) y modo **2 jugadores** en pantalla dividida (teclado o dos manos con
una sola webcam), dos modos de juego, música dinámica y tabla de puntajes
persistente.

---

## 📋 Índice

1. [Características](#-características)
2. [Requisitos e instalación](#-requisitos-e-instalación)
3. [Ejecución](#-ejecución)
4. [Cómo se juega](#-cómo-se-juega)
5. [Controles](#-controles)
6. [Arquitectura del proyecto](#-arquitectura-del-proyecto)
7. [Detalles técnicos](#-detalles-técnicos)
8. [Recursos (Assets)](#-recursos-assets)
9. [Configuración y ajustes](#-configuración-y-ajustes)
10. [Tecnologías utilizadas](#-tecnologías-utilizadas)

---

## ✨ Características

- **Física realista**: gravedad, rebote, fricción y rotación simuladas con Pymunk
  (motor basado en Chipmunk2D).
- **11 niveles de fruta**: Cereza → Fresa → Uva → Mandarina → Naranja → Manzana →
  Pera → Durazno → Piña → Melón → Sandía.
- **3 esquemas de control**: mouse, gestos de mano por cámara y teclado (versus).
- **Visión por computadora**: MediaPipe detecta la mano en tiempo real;
  ✊ puño cerrado = mover la fruta, 🖐 mano abierta = soltarla.
- **Modo 2 jugadores** en pantalla dividida, con soporte para **dos manos
  simultáneas** usando una sola webcam.
- **2 modos de juego**: Normal (sobrevive lo más posible) y Contrarreloj (3:00 min).
- **Música dinámica**: pista distinta por pantalla, rotación aleatoria en partida
  y cambio de música en el último minuto del contrarreloj.
- **Leaderboard persistente**: top 5 por modo guardado en JSON.
- **Sprites con respaldo procedural**: si falta algún PNG, la fruta se dibuja por
  código con primitivas de Pygame (círculos, arcos, polígonos).
- **Pantalla completa 1080p**: resolución lógica de 1920×1080 escalada al monitor
  manteniendo la proporción (modo `SCALED` de Pygame).

## 📦 Requisitos e instalación

- **Python 3.10 o superior**
- Dependencias obligatorias:

```bash
python -m pip install pygame pymunk
```

- Dependencias opcionales (solo para el control por cámara):

```bash
python -m pip install opencv-python mediapipe
```

> Si `opencv`/`mediapipe` no están instalados, el juego funciona igual con mouse
> y teclado: la importación es segura y el botón de cámara muestra un aviso.

## ▶️ Ejecución

Desde la carpeta del proyecto:

```bash
python main.py
```

El juego abre en pantalla completa. Teclas globales:

| Tecla | Acción |
|---|---|
| `ESC` | Salir del juego |
| `F11` | Alternar pantalla completa / ventana |

## 🎮 Cómo se juega

El juego tiene 4 pantallas (máquina de estados):

1. **Menú**: elige control (Mouse / Cámara), jugadores (1 / 2) y modo
   (Normal / Contrarreloj 3:00), luego presiona **¡JUGAR!**.
2. **Instrucciones**: resumen de controles; presiona "¡Entendido, a jugar!" o `ENTER`.
3. **Juego**: deja caer frutas dentro del contenedor.
   - Dos frutas del **mismo nivel** que chocan se fusionan en la siguiente de la
     evolución y otorgan puntos (a mayor nivel, más puntos).
   - Solo los primeros 5 niveles salen del dispensador; los grandes se obtienen
     únicamente fusionando.
   - Si una fruta queda **quieta sobre la línea roja punteada** durante ~2 segundos,
     el contenedor se declara lleno y la partida termina.
   - **Contrarreloj**: al quedar 1 minuto la música cambia y aparece un aviso;
     al agotarse el tiempo gana el puntaje acumulado.
   - **2 jugadores**: gana quien tenga más puntos; en modo Normal pierde
     inmediatamente el primero que llene su contenedor.
4. **Fin de partida**: muestra el puntaje, lo guarda en `scores.json` y despliega
   el leaderboard (top 5 por modo), con botones "Volver a jugar" y "Menú".

## 🕹️ Controles

### 1 jugador

| Control | Mover | Soltar |
|---|---|---|
| **Mouse** | mover el cursor | clic izquierdo o `ESPACIO` |
| **Cámara** | ✊ puño cerrado (arrastra el dispensador) | 🖐 abrir la mano |

> En modo cámara la mano **solo** controla la fruta del dispensador, nunca las
> que ya cayeron.

### 2 jugadores (pantalla dividida)

| Jugador | Mover | Soltar |
|---|---|---|
| **Jugador 1** (teclado) | `A` / `D` | `S` |
| **Jugador 2** (teclado) | `←` / `→` | `↓` |

Con **cámara**, una sola webcam detecta ambas manos a la vez: el Jugador 1 usa su
mano **derecha** (mitad izquierda de la imagen) y el Jugador 2 su mano
**izquierda** (mitad derecha). Los gestos son los mismos: puño = mover,
abrir = soltar.

## 🗂️ Arquitectura del proyecto

```
frutti_merge/
├── main.py            # Punto de entrada y game loop
├── game.py            # Máquina de estados, tableros, física y fusiones
├── fruit.py           # Clase Fruit (cuerpo físico) y dibujo de sprites
├── ui.py              # Botones, paneles, HUD, leaderboard
├── hand_tracker.py    # Detección de gestos de mano (MediaPipe)
├── scores.py          # Persistencia del leaderboard en JSON
├── config.py          # Todas las constantes ajustables del juego
├── scores.json        # Puntajes guardados (se genera solo)
└── Assets/
    ├── imagenes/      # Sprites de frutas y elementos de la interfaz
    └── music/         # Pistas de música y efectos de sonido
```

| Módulo | Responsabilidad |
|---|---|
| `main.py` | Inicializa Pygame, crea la ventana escalada (`SCALED + FULLSCREEN`) y ejecuta el bucle principal a 60 FPS: eventos → `update` → `draw`. |
| `game.py` | Contiene `Game` (máquina de estados: menú → instrucciones → jugando → fin) y `Board` (un contenedor con su propio espacio de física, frutas, puntaje y dispensador). En 1 jugador hay un tablero centrado; en 2 jugadores, dos tableros independientes lado a lado. |
| `fruit.py` | Clase `Fruit`: cuerpo circular de Pymunk con masa proporcional a su área. Dibuja cada fruta con su sprite PNG (rotado según el ángulo físico, con caché de rotaciones) o, si falta la imagen, con un dibujo procedural kawaii. |
| `ui.py` | Componentes de interfaz: botones con estado hover/selección, paneles, burbujas del HUD, anillo de evolución y tabla de puntajes. |
| `hand_tracker.py` | Encapsula OpenCV + MediaPipe. Clasifica cada mano por lateralidad (izquierda/derecha), calcula su posición horizontal normalizada y detecta el gesto de puño/mano abierta. Importación segura: si las librerías no existen, el resto del juego no se ve afectado. |
| `scores.py` | Carga y guarda el top 5 de cada modo en `scores.json`, tolerante a archivos corruptos o inexistentes. |
| `config.py` | Constantes centralizadas: resolución, colores, dimensiones del contenedor, física, definición de las 11 frutas, modos, música y archivos. |

## 🔧 Detalles técnicos

### Física (Pymunk)

- Cada tablero tiene su propio `pymunk.Space` con gravedad vertical; las paredes
  del contenedor son segmentos estáticos con fricción y elasticidad propias.
- Cada fruta es un círculo dinámico cuya **masa crece con el área** (`r²·0.02`),
  de modo que las frutas grandes "pesan" y compactan a las pequeñas.
- La simulación corre con **4 sub-pasos por frame** para que las pilas altas de
  frutas sean estables, y con un **tope de velocidad** (`MAX_SPEED`) que evita
  expulsiones violentas cuando una fruta nueva aparece superpuesta a otra.
- Al soltar, la fruta recibe un pequeño **jitter horizontal** y rotación
  aleatoria: sin él, dos frutas perfectamente alineadas forman torres verticales
  antinaturales.

### Fusiones

- Un *callback* de colisión de Pymunk detecta el contacto entre dos frutas del
  mismo nivel y las encola en `pending_merges` (no se puede modificar el espacio
  dentro del callback).
- Tras el paso de física, cada pareja se reemplaza por **una fruta del siguiente
  nivel en el punto medio** de ambas, se suman los puntos y suena el efecto *pop*.

### Condición de derrota

- Una fruta cuenta como "en peligro" si sobresale de la línea roja **y** está
  quieta (velocidad bajo `SETTLE_SPEED`). Si permanece así `DANGER_TIME` segundos
  (2.0 s), el contenedor se declara lleno. Esto evita perder por frutas que solo
  pasan de largo al caer.

### Visión por computadora (MediaPipe)

- Se procesa la imagen de la webcam **espejeada** para que el movimiento sea
  natural, a 640×480 con el modelo ligero (`model_complexity=0`) para no afectar
  los FPS del juego.
- **Detección de puño**: se cuenta cuántas puntas de dedo (índice, medio, anular,
  meñique) están por debajo de su nudillo; con 3 o más plegadas la mano se
  considera cerrada.
- El evento de **soltar** se dispara solo en el frame de transición
  cerrada → abierta, evitando soltar frutas por error.
- En versus, MediaPipe clasifica cada mano por lateralidad y cada tablero lee
  únicamente la suya, con franjas de cámara ligeramente solapadas para dar
  margen de movimiento a ambos jugadores.

### Gráficos y escalado

- Todo se dibuja a una **resolución lógica fija de 1920×1080**; Pygame (`SCALED`)
  la escala al monitor real manteniendo la proporción y traduciendo las
  coordenadas del mouse automáticamente.
- Los sprites de fruta se alinean con su cuerpo físico: el **círculo del cuerpo se
  detecta automáticamente desde el canal alfa** del PNG, de modo que el dibujo
  coincide exactamente con el hitbox. Las rotaciones se guardan en caché
  (cuantizadas) para no re-escalar imágenes cada frame.
- Las frutas usan una **escala por tablero**: `SOLO_FRUIT_SCALE` (0.80) en
  1 jugador para que quepan más frutas en el contenedor, y `VERSUS_FRUIT_SCALE`
  (0.88) en los contenedores más angostos del modo versus.

## 🖼️ Recursos (Assets)

### Imágenes (`Assets/imagenes/`)

- `0.png` … `10.png` — sprites de las frutas (cereza → sandía).
- `background.png` — contenedor · `bubble.png` — burbujas del HUD ·
  `evolution.png` — anillo de evolución · `player.png` — nube del dispensador.
- Si falta cualquier PNG, el juego usa su dibujo procedural como respaldo.

### Música (`Assets/music/`)

| Pista | Uso |
|---|---|
| `musica5.mp3` | Pantalla de título e instrucciones |
| `musica1/3/4/6.mp3` | Una al azar en cada partida (rotan al terminar) |
| `musica2.mp3` | Último minuto del contrarreloj |
| `bridge1.mp3` | Pantalla de fin de partida |
| `pop.wav` | Efecto de fusión |

## ⚙️ Configuración y ajustes

Todas las constantes viven en [`config.py`](config.py); las más útiles:

| Constante | Efecto |
|---|---|
| `GRAVITY`, `ELASTICITY`, `FRICTION` | Sensación general de la física |
| `DROP_COOLDOWN` | Tiempo mínimo entre lanzamientos (0.55 s) |
| `DANGER_TIME` | Segundos de tolerancia sobre la línea roja (2.0 s) |
| `TIME_ATTACK_SECONDS` | Duración del contrarreloj (180 s) |
| `SOLO_FRUIT_SCALE` | Tamaño de las frutas en 1 jugador (0.80 = 20 % más chicas) |
| `VERSUS_FRUIT_SCALE` | Tamaño de las frutas en modo versus (0.88) |
| `FRUITS` | Nombre, radio, colores y puntos de cada uno de los 11 niveles |
| `DROPPABLE_TIERS` | Cuántos niveles bajos puede lanzar el dispensador (5) |

## 🛠️ Tecnologías utilizadas

| Tecnología | Uso en el proyecto |
|---|---|
| [Python 3](https://www.python.org/) | Lenguaje del proyecto |
| [Pygame](https://www.pygame.org/) | Ventana, render 2D, eventos, audio |
| [Pymunk](https://www.pymunk.org/) | Motor de física 2D (Chipmunk2D) |
| [OpenCV](https://opencv.org/) | Captura y procesamiento de la webcam |
| [MediaPipe](https://developers.google.com/mediapipe) | Detección de manos y landmarks en tiempo real |

---

*Inspirado en Suika Game (スイカゲーム). Proyecto con fines educativos.*
