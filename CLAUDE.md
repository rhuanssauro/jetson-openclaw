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
- **CI:** GitHub Actions (lint: ruff check + format, test: pytest with coverage)
- **Container:** Docker + Docker Compose with NVIDIA runtime
- **Config mgmt:** Ansible for Jetson host provisioning

## Directory Structure

```
src/
  main.py                       # Entry point, asyncio loop, signal handling
  bot/
    discord_bot.py              # OpenClawDiscord(commands.Bot) + ClawCommands(Cog)
    slack_bot.py                # OpenClawSlack (Socket Mode, cached bot_user_id)
  hardware/
    claw_controller.py          # ClawController (GPIO/PWM, mock-capable)
  llm/
    ollama_client.py            # OllamaClient (async context manager, SSRF guard)
tests/
  test_claw.py                  # ClawController tests (3 tests)
  test_ollama_client.py         # OllamaClient tests (12 tests)
  test_discord_bot.py           # Discord bot tests (9 tests)
  test_slack_bot.py             # Slack bot tests (11 tests)
docker/
  Dockerfile                    # Dev image (python:3.10-slim-buster, non-root)
  Dockerfile.jetson             # Jetson-native L4T base image
  docker-compose.yml            # ollama + openclaw services
ansible/
  setup_jetson.yml              # Full Jetson provisioning playbook
hardware/
  udev/99-openclaw-gpio.rules   # Non-root GPIO/PWM access
scripts/
  setup.sh                      # Bootstrap (Ansible + Docker)
  update.sh                     # Pull + rebuild
docs/
  PLAYBOOK.md                   # Complete implementation guide (1900 lines)
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

## Remaining Improvement Opportunities

1. **Empty `__init__.py` files** — could export public APIs
2. **No REST API** — fastapi/uvicorn removed from deps; could be re-added if REST endpoints are needed
3. **No conversation context** — LLM calls are stateless (no chat history)
4. **Test coverage at 65%** — `src/main.py` has 0% coverage (hard to test signal handling)
5. **No mypy CI step** — type hints are present but not validated in CI yet
