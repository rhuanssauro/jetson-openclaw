# OpenClaw - Jetson Orin Nano Personal AI Assistant

OpenClaw is an agentic Personal AI Assistant designed to run locally on the NVIDIA Jetson Orin Nano (8GB + NVMe). It provides a unified interface across Discord and Slack to control physical hardware (a robotic claw) and interact with a local Large Language Model (LLM).

## Features

*   **Local LLM Inference:** Runs `Llama-3` or `Mistral` locally using Ollama, optimized for Jetson's GPU.
*   **Multi-Platform Chat:** Talk to your assistant via Discord and Slack.
*   **Hardware Control:** Controls a servo-based claw via GPIO/PWM.
*   **Privacy First:** All data stays local on your Jetson.

## Architecture

*   **Hardware:** NVIDIA Jetson Orin Nano 8GB
*   **OS:** JetPack 6 (Ubuntu 22.04)
*   **AI Engine:** Ollama (running inside Docker with NVIDIA Runtime)
*   **Application:** Python 3.10 + Discord.py + Slack SDK + Jetson.GPIO
*   **Deployment:** Docker Compose + Ansible

## Installation

### Prerequisites

1.  Flash your Jetson Orin Nano with JetPack 6.
2.  Ensure you have an NVMe SSD mounted (recommended 128GB+).
3.  Clone this repository:
    ```bash
    git clone https://github.com/rhuanssauro/jetson-openclaw.git
    cd jetson-openclaw
    ```

### 1. System Setup (Automated)

We provide a script to handle everything (Ansible + Docker + Swap).

```bash
sudo chmod +x scripts/setup.sh
sudo ./scripts/setup.sh
```

### 2. Configuration

Create a `.env` file in the root directory:

```bash
cp .env.example .env
nano .env
```

Fill in your tokens:

```ini
# Bot Tokens
DISCORD_TOKEN=your_discord_bot_token
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_APP_TOKEN=xapp-your-slack-app-token

# LLM Configuration
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama3:8b-instruct-q4_K_M
```

### 3. Updates

To pull the latest code and rebuild:

```bash
chmod +x scripts/update.sh
./scripts/update.sh
```

## Usage

### Discord
*   **Chat:** Mention the bot `@OpenClaw` or DM it to chat with the LLM.
*   **Commands:**
    *   `!claw open`: Opens the claw.
    *   `!claw close`: Closes the claw.
    *   `!claw status`: Checks hardware status.

### Slack
*   **Chat:** Mention `@OpenClaw` to chat.
*   **Commands:** Just say "open claw" or "close claw" in a mention.

## Documentation

For the **complete step-by-step guide** — from unboxing the Jetson to daily usage — see:

**[docs/PLAYBOOK.md](docs/PLAYBOOK.md)** — The OpenClaw Implementation Playbook

Covers hardware assembly, JetPack flashing, Discord/Slack bot creation, model selection, troubleshooting, and development workflow. No prior experience required.

## Development

To run locally (on your laptop) with mocked hardware:

```bash
python3 -m venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
python src/main.py
```

### Testing

```bash
uvx pytest -v              # Run all 35 tests
uvx pytest --cov=src       # With coverage report
```

### Linting

```bash
uvx ruff check .           # Lint
uvx ruff format --check .  # Format check
```

## License

MIT
