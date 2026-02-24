# Jetson OpenClaw Project Context

## Project Overview
**Project Name:** `jetson-openclaw`
**Status:** Production-ready (v1.0)

OpenClaw is an agentic Personal AI Assistant running on NVIDIA Jetson Orin Nano 8GB. It provides Discord and Slack chat interfaces to control a physical servo-based robotic claw via GPIO/PWM and interact with a local LLM through Ollama — completely offline and privacy-first.

## Architecture & Tech Stack

- **Hardware Platform:** NVIDIA Jetson Orin Nano 8GB (JetPack 6, Ubuntu 22.04)
- **Primary Language:** Python 3.10
- **Key Libraries:**
  - `Jetson.GPIO` for hardware control (mock-capable for development)
  - `discord.py` for Discord bot (Cog pattern)
  - `slack-sdk` for Slack bot (Socket Mode)
  - `aiohttp` for async HTTP to Ollama
  - `loguru` for structured logging
- **Containerization:** Docker Compose with NVIDIA runtime
- **Provisioning:** Ansible for Jetson host setup

## Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Quick start and overview |
| [CLAUDE.md](CLAUDE.md) | AI assistant project context (architecture, conventions, commands) |
| [docs/PLAYBOOK.md](docs/PLAYBOOK.md) | Complete implementation guide — hardware to production (1900 lines) |

## Development Standards

### 1. Hardware Safety
- **Mock First:** All hardware interfaces have software mocks. Development works without physical hardware.
- **Safety Limits:** Servo duty cycles calibrated per servo; external power supply required.

### 2. Code Quality
- **Type hints:** All source files annotated (`from __future__ import annotations`)
- **Linting:** Ruff (line-length 100, double quotes, isort)
- **Testing:** pytest + pytest-asyncio (35 tests, 65% coverage)
- **CI:** GitHub Actions — lint (ruff) + test (pytest with coverage)

### 3. Git Workflow
- **Commits:** Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`)
- **Branches:** Feature branches with squash-merge PRs to `main`
