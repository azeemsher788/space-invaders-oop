# Architecture Overview

## Problem Being Solved
Classic arcade games like Space Invaders often struggle with maintainability when rewritten by modern developers due to tightly coupled logic and presentation. This project demonstrates how to build a robust, Pygame-based 2D shooter using Object-Oriented Principles (OOP) to cleanly separate physics, state management, and rendering.

## Core Use Cases
- A user can play a classic game of Space Invaders.
- The game loop maintains deterministic physics regardless of monitor refresh rate.
- Enemies scale dynamically in speed based on their surviving numbers.
- Destructible environments (bunkers) accurately reflect projectile damage.

## MVP Features
- Player movement and firing mechanics.
- Alien fleet movement (horizontal shifts and vertical drops).
- Collision detection between projectiles, player, aliens, and bunkers.
- Scoring system and level progression.

## Future Features
- SQLite-based high-score persistence.
- Audio engine for SFX and background music.
- Multiple alien types with unique attack patterns.

## Recommended Technology Stack
- **Language**: Python 3.9+
- **Graphics/Input**: Pygame 2.0+
- **Tooling**: Pytest (Testing), Black/Isort (Formatting), Mypy (Type checking), Pylint (Linting)

## Architecture
The application uses a cleanly decoupled architectural approach:
- **GameEngine**: The central loop orchestrator. Separates standard tick processing from rendering.
- **Entity Component**: Base entities own their logical state but delegate rendering, preventing tight coupling between visual sprites and logical position.
- **State Machine**: Both the overarching game (`GameState`) and the alien fleet (`FleetState`) operate via deterministic state machines.

This architecture ensures testability (logic can be tested without Pygame drawing surfaces) and maintainability.

## Database Requirements
Currently, the application relies solely on in-memory state. For high-scores (planned), a localized `sqlite3` database will be implemented as it provides file-based persistence without the need for external database infrastructure, keeping the project extremely portable.

## Authentication and Authorization
Not applicable for this standalone local client application.

## External Integrations
Not applicable.

## Deployment Approach
The game is distributed as a source package or installable module via `pip`. 
