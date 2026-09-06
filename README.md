# Space Invaders — Python/Pygame Implementation

![Space Invaders](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-purple.svg)
![Architecture](https://img.shields.io/badge/Architecture-OOP%20%7C%20Component-orange.svg)

A production-grade, highly polished clone of the arcade classic, *Space Invaders*. 

Developed by [@azeemsher788](https://github.com/azeemsher788).

This project was built as a portfolio piece to demonstrate advanced **Object-Oriented Programming (OOP) design patterns**, **game-loop optimization**, and **clean architectural separation of concerns** in Python.

---

## 🏗️ Architecture & Code Quality

The codebase strictly adheres to object-oriented principles, modularizing the game into cleanly decoupled components. Rendering logic is entirely separated from physics and state updates.

### Core Modules

* **`engine.py` (GameEngine)**: The central orchestrator. Owns the canonical fixed-step game loop, manages state transitions (`TITLE` → `PLAYING` → `GAME_OVER`), delegates collision passes, and dispatches non-blocking keyboard input.
* **`entities.py` (Entity Base & Actors)**: Defines the base `Entity` class and concrete implementations (`PlayerShip`, `Alien`, `UFO`, `Projectile`, `BunkerTile`). Entities own their logical state (position, health) but delegate rendering.
* **`fleet.py` (AlienFleet)**: The state machine managing the alien armada as a cohesive grid. 
* **`sprites.py` (Surface Factory)**: A purely procedural sprite generator using anti-aliased polygons and pixel-art bitmasks. **Zero external image dependencies**.
* **`bunker.py` (Bunker)**: Manages destructible defensive barriers via a binary occupancy grid of `BunkerTile` blocks.
* **`hud.py` (HUD)**: A strictly read-only overlay renderer (score, lives, level).
* **`vfx.py` (VFXManager)**: Manages transient particle effects like starburst explosions and floating score popups.
* **`constants.py`**: The single source of truth for all game-wide tunables.

---

## 👾 Game Mechanics & State Machines

### 1. Fleet Dynamics & State Machine
The `AlienFleet` operates on a three-phase tick-based state machine:
1. `HORIZONTAL`: Shift all alive aliens by `±dx` pixels.
2. `CHECK_EDGE`: If the left/right screen bounds are intersected, schedule a drop.
3. `DROP`: Shift the entire grid down by `dy` pixels and invert horizontal direction.

### 2. Dynamic Difficulty Scaling
To replicate the legendary "heartbeat" acceleration of the arcade original, the fleet's movement interval scales dynamically based on the surviving alien count. As aliens are destroyed, the delay between fleet ticks decreases linearly from `ALIEN_MOVE_INTERVAL_MAX` to `ALIEN_MOVE_INTERVAL_MIN`.

### 3. Combat & Firing Logic
* **Alien Targeting**: Only the "front-line" (bottom-most alive alien in each column) is eligible to drop bombs, calculated dynamically each frame.
* **Cooldowns**: Player weapon firing is gated by a timestamp-based cooldown to prevent projectile spamming, governed by `constants.PLAYER_LASER_COOLDOWN`.

### 4. Collision Math (AABB)
Collision detection is optimized using a **Two-Phase Bounding-Box (AABB)** approach:
* **Broad Phase**: Projectiles are grouped and filtered by category (Lasers vs Aliens, Bombs vs Bunkers).
* **Narrow Phase**: Exact overlap testing via `pygame.Rect.colliderect()`, operating in $O(1)$ time per check. The bunker collision systematically tests active projectile rectangles against the destructible `BunkerTile` sub-grid.

---

## 🎮 Rendering & Controls

* **Decoupled Game Loop**: The engine limits updates using `pygame.time.Clock.tick(FPS)` to pass a delta-time (`dt`) to entity updates. This guarantees deterministic physics logic regardless of frame-rate fluctuations.
* **Zero Input Latency**: Input is handled via non-blocking key-state polling (`KEYDOWN` and `KEYUP` flag toggling) rather than event-driven callbacks. This totally bypasses OS-level key repeat latency, allowing for responsive, simultaneous movement and firing.
* **Procedural VFX**: The `background.py` parallax starfield and the `vfx.py` explosion effects are generated entirely through dynamic draw calls, requiring no external `.png` assets while providing a rich visual aesthetic.

---

## 🚀 Setup & Execution

### Prerequisites
* Python 3.9+
* `pygame` (Version 2.0.0 or higher)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/azeemsher788/space-invaders-oop.git
   cd space-invaders-oop/95
   ```
2. Install the required dependencies:
   ```bash
   pip install pygame
   ```

### Running the Game
Launch the entry point script:
```bash
python main.py
```

### Controls
* **Movement**: `Left / Right Arrows` or `A / D`
* **Fire**: `Spacebar` or `Up Arrow` or `W`
* **Pause**: `P`
* **Confirm / Restart**: `Enter`

---

## 💼 For Recruiters & Clients

This repository highlights a focus on:
- **Clean Architecture & SOLID Principles**: Code is modular, highly decoupled, and easy to extend.
- **Strong Typing**: Fully PEP-484 compliant type hinting across the entire codebase.
- **Maintainability**: Extensive docstrings, clean variable naming, and configuration abstraction (via `constants.py`).
- **Optimization**: Efficient state handling, memory-friendly procedural asset generation, and O(n) collision polling without the overhead of heavy ECS (Entity Component System) libraries where inappropriate.

Feel free to explore the source code to review the implementation details!
