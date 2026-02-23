# Jetson OpenClaw Project Context

## Project Overview
**Project Name:** `jetson-openclaw`
**Status:** Initialization / Empty Repository

This project appears to be focused on robotic manipulation (specifically a "claw" or gripper mechanism) running on the NVIDIA Jetson platform. As the repository is currently empty, this document serves as the foundational context and architectural guide for future development.

## Inferred Architecture & Tech Stack
Based on the project name, the following stack is recommended:
- **Hardware Platform:** NVIDIA Jetson (Nano, Xavier, Orin)
- **Primary Language:** Python 3.8+ (for rapid prototyping/ML) or C++ (for real-time control)
- **Key Libraries:**
  - `Jetson.GPIO` or `periphery` for hardware control
  - `opencv-python` for vision-based grasping
  - `ros2` (Humble/Iron) if integrating with a larger robot system
- **Containerization:** Docker (highly recommended for Jetson reproducibility)

## Recommended Directory Structure
Adopting a standard robotics project structure from the start:

```
jetson-openclaw/
├── src/                    # Source code
│   ├── driver/             # Hardware interface for the claw (PWM/Serial/GPIO)
│   ├── vision/             # Computer vision pipelines (if applicable)
│   ├── control/            # High-level logic & state machines
│   └── main.py             # Entry point
├── tests/                  # Unit and integration tests
├── hardware/               # 3D models (STL/STEP), schematics, wiring diagrams
├── docker/                 # Dockerfiles for development/deployment
├── scripts/                # Utility scripts (setup, install, flash)
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## Development Standards & Mandates

### 1. Hardware Safety
- **Mock First:** All hardware interfaces MUST have software mocks. Development should be possible without physical hardware attached.
- **Safety Limits:** Implement software limits for servo ranges/motor torque to prevent hardware damage.

### 2. Code Quality
- **Typing:** Enforce strict type hinting in Python (`mypy`).
- **Linting:** Use `ruff` or `flake8` for linting and `black` for formatting.
- **Testing:** Use `pytest`. All hardware drivers must be unit-testable via mocks.

### 3. Git Workflow
- **Commits:** Follow conventional commits (e.g., `feat: add pwm driver`, `fix: servo jitter`).
- **Branches:** Use feature branches; never commit directly to `main` for significant changes.

## Next Steps
1.  Initialize the project structure (create `src`, `tests`, `README.md`).
2.  Define the hardware interface requirements.
3.  Set up the development environment (Docker or venv).
