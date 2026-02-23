# CLAUDE.md - OpenClaw: Jetson Orin Nano Personal AI Assistant

## Project Overview

OpenClaw is an agentic Personal AI Assistant running locally on NVIDIA Jetson Orin Nano (8GB + NVMe). It provides a unified chat interface (Discord + Slack) that controls a physical servo-based robotic claw via GPIO/PWM and runs local LLM inference through Ollama — completely offline, privacy-first.

**Repository:** `github.com/rhuanssauro/jetson-openclaw`
**License:** MIT

## Architecture

```
User (Discord/Slack) --> Bot Layer --> LLM (Ollama, local)
                                  --> Hardware (Claw via GPIO/PWM)
```

| Layer | Technology | File |
|-------|-----------|------|
| Entry point | asyncio event loop | `src/main.py` |
| Discord bot | discord.py (prefix: `!claw `) | `src/bot/discord_bot.py` |
| Slack bot | slack-sdk (Socket Mode) | `src/bot/slack_bot.py` |
| LLM client | aiohttp -> Ollama `/api/generate` | `src/llm/ollama_client.py` |
| Hardware | Jetson.GPIO (PWM on pin 33, 50Hz) | `src/hardware/claw_controller.py` |
| Deployment | Docker Compose (ollama + openclaw) | `docker/docker-compose.yml` |
| Provisioning | Ansible (local Jetson setup) | `ansible/setup_jetson.yml` |

## Hardware Target

- **Board:** NVIDIA Jetson Orin Nano 8GB
- **OS:** JetPack 6 (Ubuntu 22.04)
- **Servo:** PWM0 on GPIO pin 33 (BOARD numbering), 50Hz
- **Duty cycles:** 7.5% = open, 2.5% = close (calibrate per servo)
- **Mock mode:** Auto-enabled when `Jetson.GPIO` import fails (CI, laptops)

## Tech Stack

- **Language:** Python 3.10
- **Async:** asyncio (all I/O is async)
- **Linter/Formatter:** Ruff (`ruff.toml`, line-length 100, double quotes)
- **Tests:** pytest (`pytest.ini`, pythonpath=src, testpaths=tests)
- **CI:** GitHub Actions (lint-only: `uvx ruff check .` + `uvx ruff format --check .`)
- **Container:** Docker + Docker Compose with NVIDIA runtime
- **Config mgmt:** Ansible for Jetson host provisioning

## Directory Structure

```
src/
  main.py                       # Entry point, asyncio loop, signal handling
  bot/
    discord_bot.py              # OpenClawDiscord(commands.Bot)
    slack_bot.py                # OpenClawSlack (Socket Mode)
  hardware/
    claw_controller.py          # ClawController (GPIO/PWM, mock-capable)
  llm/
    ollama_client.py            # OllamaClient (async HTTP to Ollama)
tests/
  test_claw.py                  # ClawController tests (mock mode)
docker/
  Dockerfile                    # python:3.10-slim-buster
  docker-compose.yml            # ollama + openclaw services
ansible/
  setup_jetson.yml              # Full Jetson provisioning playbook
hardware/
  udev/99-openclaw-gpio.rules   # Non-root GPIO/PWM access
scripts/
  setup.sh                      # Bootstrap (Ansible + Docker)
  update.sh                     # Pull + rebuild
docs/                           # Reserved (empty)
```

## Development Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt

# Run (mock mode on non-Jetson)
python src/main.py

# Lint
uvx ruff check .
uvx ruff check . --fix
uvx ruff format .
uvx ruff format --check .

# Test
uvx pytest
uvx pytest -v
uvx pytest --tb=short

# Docker (on Jetson)
docker compose -f docker/docker-compose.yml up -d --build
docker compose -f docker/docker-compose.yml logs -f
```

## Environment Variables

Defined in `.env` (copy from `.env.example`):

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `DISCORD_TOKEN` | At least one bot | - | Discord bot token |
| `SLACK_BOT_TOKEN` | At least one bot | - | Slack bot token (xoxb-) |
| `SLACK_APP_TOKEN` | With Slack | - | Slack app token (xapp-) |
| `OLLAMA_HOST` | No | `http://ollama:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | No | `llama3:8b-instruct-q4_K_M` | LLM model name |

## Coding Conventions

- **Line length:** 100 characters
- **Quotes:** Double quotes
- **Imports:** isort-compatible (enforced by Ruff `I` rule)
- **Logging:** `loguru.logger` (not stdlib `logging`)
- **Async:** All I/O operations must be async
- **Hardware abstraction:** All hardware code must work in mock mode (no Jetson.GPIO = no-op)
- **Type hints:** Use throughout (target: mypy strict in future)
- **Error handling:** Log with loguru, never crash silently, graceful degradation

## Known Gaps (Improvement Opportunities)

1. **Test coverage is minimal** — only 3 tests for ClawController; no tests for OllamaClient, Discord bot, or Slack bot
2. **Dockerfile base image** — uses `python:3.10-slim-buster`, not a Jetson-native L4T image
3. **Unused dependencies** — `fastapi` and `uvicorn` in requirements.txt but not used
4. **No type hints** — source files lack type annotations
5. **aiohttp session management** — `OllamaClient.session` created but never properly closed
6. **docker-compose version key** — `version: "3.8"` is deprecated in modern Docker Compose
7. **Empty `__init__.py` files** — could export public APIs
8. **No REST API** — fastapi listed but no endpoints implemented
9. **No conversation context** — LLM calls are stateless (no chat history)
10. **Slack `auth_test` called per message** — should be cached
