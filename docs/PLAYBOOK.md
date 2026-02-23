# OpenClaw Playbook — Complete Setup Guide

**Version:** 1.1 | **Date:** 2026-02-23 | **Hardware:** NVIDIA Jetson Orin Nano 8GB

> This playbook walks you through every step of building and running OpenClaw — a robotic claw controlled by Discord and Slack, powered by a local AI on a Jetson Orin Nano. No prior Linux, hardware, or AI experience is required. Every command is copy-pasteable and every step explains **why** it exists.

---

## Table of Contents

1. [What You Need](#part-1-what-you-need)
2. [Hardware Assembly](#part-2-hardware-assembly)
3. [Flash JetPack 6](#part-3-flash-jetpack-6)
4. [Create Your Discord Bot](#part-4-create-your-discord-bot)
5. [Create Your Slack Bot](#part-5-create-your-slack-bot)
6. [Install OpenClaw](#part-6-install-openclaw)
7. [Using OpenClaw — Practical Examples](#part-7-using-openclaw--practical-examples)
8. [Model Selection Guide](#part-8-model-selection-guide)
9. [Troubleshooting](#part-9-troubleshooting)
10. [Development Guide](#part-10-development-guide)
11. [Appendix A: Complete .env Reference](#appendix-a-complete-env-reference)
12. [Appendix B: GPIO Pinout](#appendix-b-jetson-orin-nano-gpio-pinout)
13. [Appendix C: Docker Commands Cheat Sheet](#appendix-c-docker-commands-cheat-sheet)
14. [Appendix D: Useful Links](#appendix-d-useful-links)

---

## Part 1: What You Need

### Hardware Shopping List

| Item | Model / Spec | Estimated Price (USD) | Notes |
|------|-------------|----------------------|-------|
| **Jetson Orin Nano 8GB** | NVIDIA Jetson Orin Nano 8GB Dev Kit | $199–$249 | Includes carrier board and heatsink |
| **NVMe SSD** | Samsung 980 250GB M.2 2280 PCIe Gen3 | $30–$45 | Critical for fast AI model loading |
| **Power Adapter** | 12V/3A or 19V/2.1A barrel jack (5.5mm/2.1mm) | $10–$15 | Seeed carrier: 9–20V DC input |
| **Servo (lightweight option)** | Tower Pro SG90 9g Micro Servo | $2–$4 | Good for small/desk claws |
| **Servo (heavy duty option)** | Tower Pro MG996R Metal Gear Servo | $8–$12 | More torque, needs external power |
| **Claw Kit** | SG90 Robot Gripper Claw Kit (generic) | $5–$8 | Matches SG90 servo |
| **BEC (5V power converter)** | UBEC 5V 3A Step-Down (RC hobby type) | $3–$5 | Required for MG996R; optional for SG90 |
| **Jumper Wires** | Female-to-Female 20cm Dupont wires | $2–$4 | For servo signal wire to GPIO |
| **microSD Card** | 32GB+ UHS-I Class 10 A1/A2 | $8–$12 | Only needed during initial flash |
| **USB-A to micro-USB cable** | Any standard cable | $0–$5 | For SDK Manager flashing |
| **Ethernet cable** | CAT5e or better | $0–$5 | Needed for first boot/setup |
| **Anti-static wristband** | Any brand | $3–$8 | Mandatory when handling the board |

**Total estimated cost:** $270–$380 USD (hardware only)

> **Cheaper option:** If you already own a Raspberry Pi power supply and microSD card, you can start with just the Jetson kit + NVMe + SG90 servo + claw kit for about $245.

### Software Accounts (Free)

| Account | URL | Purpose |
|---------|-----|---------|
| **Discord account** | discord.com | Required to create the bot |
| **Slack workspace** | slack.com | Required for Slack integration |
| **GitHub account** | github.com | Required to clone the repository |
| **NVIDIA Developer account** | developer.nvidia.com | Required to download JetPack SDK Manager |

All accounts are free. You do NOT need to pay for anything on the software side.

### Time Estimate

| Phase | Estimated Time |
|-------|---------------|
| Hardware assembly | 15–30 minutes |
| JetPack 6 flash (SD card method) | 30–45 minutes |
| JetPack 6 flash (SDK Manager + NVMe) | 60–90 minutes |
| Discord/Slack bot creation | 20–30 minutes |
| OpenClaw install and configuration | 20–30 minutes |
| Ollama model download | 10–20 minutes (depends on internet speed) |
| **Total (SD card path)** | **~2 hours** |
| **Total (NVMe path — recommended)** | **~3 hours** |

---

## Part 2: Hardware Assembly

### Why External Power for the Servo?

The Jetson's GPIO pins output 3.3V at a maximum of 1 mA — far too weak to power a servo. The servo signal wire connects to GPIO pin 33 (which tells the servo the angle to move to), but the servo's actual power must come from an external 5V source. Feeding servo power through the Jetson's 5V pins can draw up to 2.5A and will trigger the board's overcurrent protection or permanently damage it.

### System Architecture

```mermaid
graph LR
    subgraph Jetson["Jetson Orin Nano 40-pin Header"]
        P33["Pin 33 (PWM0) — Signal 3.3V"]
        P34["Pin 34 (GND) — Common Ground"]
    end

    subgraph BEC["External 5V BEC/PSU"]
        BEC5V["5V Output"]
        BECGND["GND Output"]
    end

    subgraph Servo["Servo Motor"]
        SIG["Signal wire (orange/white)"]
        VCC["VCC wire (red)"]
        GND["GND wire (brown/black)"]
    end

    P33 --> SIG
    BEC5V --> VCC
    BECGND --> GND
    P34 --> BECGND

    style P33 fill:#4a90d9,stroke:#fff,color:#fff
    style P34 fill:#50c878,stroke:#fff,color:#fff
    style BEC5V fill:#f39c12,stroke:#fff,color:#fff
    style BECGND fill:#50c878,stroke:#fff,color:#fff
    style SIG fill:#4a90d9,stroke:#fff,color:#fff
    style VCC fill:#f39c12,stroke:#fff,color:#fff
    style GND fill:#50c878,stroke:#fff,color:#fff
```

### Pin-by-Pin Wiring Table

| Pin Number | Pin Name | Connection | Wire Color |
|-----------|----------|------------|------------|
| **33** | PWM0 / GPIO12 | Servo signal input | Orange or White |
| **34** | GND | External BEC GND (common ground) | Black |
| _(external)_ | BEC 5V output | Servo VCC (red wire) | Red |
| _(external)_ | BEC GND output | Servo GND AND Pin 34 | Black |

> **Why Pin 34 for GND?** Pin 34 is the GND pin physically adjacent to Pin 33 (PWM0). By sharing this GND between the Jetson and the external servo power supply, you establish a common electrical reference. Without this, the PWM signal has no reference voltage and the servo will behave erratically or not move at all.

### Step-by-Step Wiring (Power OFF)

> **STOP: Do NOT connect anything while the Jetson is powered on. Always wire first, then power on.**

**Step 1 — Connect BEC output:**
- Plug the BEC's input into your 12V DC power supply (do NOT turn on yet)
- From the BEC's 5V output, run a red wire to the servo's RED wire (VCC)
- From the BEC's GND output, run a black wire to the servo's BLACK/BROWN wire (GND)

**Step 2 — Connect servo signal:**
- Take a female-to-female jumper wire
- Connect one end to the servo's ORANGE or WHITE wire (signal)
- Connect the other end to **Pin 33** on the Jetson's 40-pin header

**Step 3 — Common ground:**
- Take another female-to-female jumper wire
- Connect one end to **Pin 34** on the Jetson (the pin directly to the right of Pin 33 in the same row)
- Connect the other end to the BEC's GND terminal (same GND rail as the servo's black wire)

**Step 4 — Locate Pin 33:**
The 40-pin header is the 2-row connector on the Jetson board. Looking at the header with the board in front of you:
- Pin 1 is in the top-left corner (marked with a small triangle or dot on the board)
- The LEFT column contains odd-numbered pins: 1, 3, 5, 7 ... 39
- The RIGHT column contains even-numbered pins: 2, 4, 6, 8 ... 40
- Pin 33 is in the LEFT column, 17th row (count 16 pairs down, then the left pin)
- Pin 34 is in the RIGHT column of the same row — immediately to the right of Pin 33

> **If in doubt:** See [Appendix B](#appendix-b-jetson-orin-nano-gpio-pinout) for the full GPIO pinout diagram and table.

### Safety Warnings

> **WARNING: Never power the servo from Jetson Pin 2 or Pin 4 (5V power pins).** The on-board 5V rail is limited to ~500 mA shared with USB ports and other peripherals. A single MG996R servo draws up to 2.5A under load, which will trigger the board's overcurrent protection and may reset or damage the Jetson.

> **WARNING: ESD (Static Electricity) can destroy the Jetson module in an instant.** Before touching the board:
> - Wear an anti-static wristband clipped to a metal table leg or power supply chassis
> - Work on an anti-static mat if possible
> - Touch grounded metal before picking up the board

> **WARNING: Never hot-plug GPIO wires** (connect while powered). Always power off the Jetson and the BEC before changing any wiring.

### Verification Before Power-On

Before applying power, verify:

- [ ] Servo signal wire connected to Pin 33 (not Pin 32 or 35)
- [ ] Pin 34 (Jetson GND) connected to BEC GND
- [ ] Servo VCC (red) connected to BEC 5V output — NOT to any Jetson pin
- [ ] Servo GND (black/brown) connected to BEC GND
- [ ] No bare wire ends that could short-circuit
- [ ] BEC input is connected to 12V supply but the 12V supply is OFF

---

## Part 3: Flash JetPack 6

JetPack 6 is NVIDIA's official operating system for Jetson boards. It includes Ubuntu 22.04, CUDA (the GPU computing library that allows AI models to run on the Jetson's built-in graphics processor), TensorRT, and all the drivers needed for OpenClaw to work. You must install this before doing anything else.

### Option A: SD Card Method (Easier, Slower — for first-timers)

**When to use:** You want to get started quickly without a Ubuntu host machine. Acceptable for evaluation, not recommended for production because microSD cards are slow (~25–50 MB/s) — AI model loading will take ~60 seconds each time.

**What you need:** A microSD card (32GB minimum), the Balena Etcher app on your computer, and an internet connection.

**Step 1 — Download the JetPack 6 SD Card image:**
1. Go to the NVIDIA Developer site: `https://developer.nvidia.com/jetson/jetpack`
2. Click "JetPack 6.x" (use the latest 6.x version)
3. Select "Jetson Orin Nano Developer Kit"
4. Download the `.img.gz` file (approximately 6–8 GB)

**Step 2 — Flash the microSD card:**
1. Download Balena Etcher: `https://etcher.balena.io/`
2. Insert your microSD card into your computer
3. Open Etcher
4. Click "Flash from file" and select the `.img.gz` you downloaded
5. Click "Select target" and choose your microSD card
6. Click "Flash!" and wait for it to complete (~10–15 minutes)

> **WARNING: Etcher will erase everything on the microSD card.** Double-check you selected the microSD card and not your computer's internal drive. The target name in Etcher shows the device size — a 32GB card is ~29.7 GiB.

**Step 3 — First boot:**
1. Insert the microSD card into the Jetson's microSD slot (underside of the board)
2. Connect HDMI monitor, USB keyboard, and Ethernet cable
3. Connect power — the Jetson will boot automatically
4. Follow the Ubuntu setup wizard (set username, password, timezone)

> **Tip:** Write down the username and password you set. You will need them in every subsequent step.

**Step 4 — Verify:**
After the desktop loads, open a Terminal (Ctrl+Alt+T) and run:

```bash
tegrastats
```

Expected output (abbreviated):
```
RAM 1234/7772MB (lfb 4x4MB) SWAP 0/8192MB CPU [5%@729,1%@729,...] GPU 0%@306
```

This confirms the Jetson is running correctly. Press Ctrl+C to stop.

---

### Option B: SDK Manager + NVMe (Recommended — faster, better for production)

**When to use:** You want the best performance. NVMe storage reads at ~3500 MB/s vs ~90 MB/s for microSD, which means AI models load in 3–5 seconds instead of 60 seconds.

**What you need:** A computer running Ubuntu 22.04 (or a Ubuntu 22.04 VM), an NVIDIA Developer account, and a USB-A to micro-USB (or USB-C, check your carrier board) cable.

**Step 1 — Install NVMe SSD:**
1. Power off the Jetson
2. Wear your anti-static wristband
3. Locate the M.2 Key M slot (on the carrier board, near the center)
4. Gently insert the NVMe SSD at a 30-degree angle
5. Press down until it lies flat, then secure with the tiny M.2 screw

**Step 2 — Install SDK Manager on your Ubuntu host:**
1. Go to `https://developer.nvidia.com/sdk-manager`
2. Log in with your NVIDIA Developer account
3. Download the `.deb` package for Ubuntu
4. Install it:

```bash
sudo apt-get install ./sdkmanager_*.deb
```

Expected output (abbreviated):
```
Selecting previously unselected package sdkmanager.
Preparing to unpack sdkmanager_2.x.x_amd64.deb ...
Unpacking sdkmanager ...
Setting up sdkmanager ...
```

**Step 3 — Put the Jetson into Recovery Mode:**
1. Disconnect power from the Jetson
2. Locate the "RECOVERY" button on the carrier board (check your carrier board's documentation — on the Seeed Studio carrier it is labeled FC_REC or RECOVERY)
3. Hold the RECOVERY button
4. While holding it, connect the USB cable from the Jetson to your Ubuntu host computer
5. Wait 2 seconds, then release the RECOVERY button

You can verify the Jetson is in recovery mode by running on the host:
```bash
lsusb
```

Expected output contains:
```
Bus 001 Device 005: ID 0955:7523 NVIDIA Corp. APX
```

If you do NOT see `NVIDIA Corp. APX`, the Jetson did not enter recovery mode. Unplug the USB cable, disconnect power, and repeat Step 3.

**Step 4 — Run SDK Manager:**
```bash
sdkmanager
```

1. Log in with your NVIDIA Developer account
2. Select "Jetson Orin Nano"
3. Select "JetPack 6.x" (latest version)
4. Under "Storage Device", select "NVMe" if available, otherwise "SD Card"
5. Click "Continue" and let it run (30–60 minutes)
6. When prompted, set up the first-boot credentials via the wizard on the connected monitor

**Step 5 — Verify NVMe boot:**
After the Jetson reboots, open a terminal and run:

```bash
mount | grep " / "
```

Expected output:
```
/dev/nvme0n1p1 on / type ext4 (rw,relatime,...)
```

If you see `/dev/nvme0n1p1`, the Jetson is booting from NVMe. If you see `/dev/mmcblk0p1` instead, it is still booting from the microSD card — revisit Step 4 and ensure "NVMe" was selected.

**Step 6 — Verify GPU:**

```bash
tegrastats
```

Expected output includes GPU utilization like `GPU 0%@306`. Alternatively:

```bash
cat /sys/bus/platform/drivers/host1x/*/nvpmodel_supported_modes
```

If this file exists and shows output, the GPU and JetPack installation are correct.

### Set Maximum Performance Mode

After first boot, run these two commands to unlock the Jetson's full performance (15W mode with all CPU/GPU cores at maximum clock):

```bash
# Set power mode to MAXN (15W — maximum performance)
sudo nvpmodel -m 0
```

Expected output:
```
NV Power Mode: MAXN
```

```bash
# Lock CPU and GPU clocks to maximum
sudo jetson_clocks
```

Expected output: none (the command runs silently). This is normal.

> **Why is this necessary?** By default, the Jetson starts in an energy-saving mode. `nvpmodel -m 0` enables all 6 CPU cores and the full GPU. `jetson_clocks` locks the frequencies at their maximum values, preventing thermal throttling from reducing AI inference speed.

> **WARNING: These settings do NOT persist across reboots.** You must run both commands again after every restart. To make them permanent, add both commands to `/etc/rc.local` or create a systemd service. The setup script in Part 6 does NOT configure this automatically — you must do it yourself.

---

## Part 4: Create Your Discord Bot

Discord is a chat platform. A "bot" is a special Discord account controlled by code instead of a human. You will create a bot account in the Discord Developer Portal, get a secret token, and invite the bot to your server.

### Why do you need a token?

The bot token is like a password. When OpenClaw starts, it presents this token to Discord's servers to prove "I am the bot called OpenClaw". Discord then lets the bot receive messages and send replies. Without the token, the bot cannot log in.

### Step 1 — Go to the Developer Portal

Open your browser and navigate to:
```
https://discord.com/developers/applications
```

Log in with your Discord account.

### Step 2 — Create a New Application

1. Click the **"New Application"** button in the top-right corner
2. Enter the name: `OpenClaw`
3. Accept the Developer Terms of Service if prompted
4. Click **"Create"**

You are now on the "General Information" page. You will see an "APPLICATION ID" — **this is NOT your bot token**. This is a public identifier, not a secret.

### Step 3 — Create the Bot User

1. In the left sidebar, click **"Bot"**
2. Click **"Add Bot"** (or if it already says "Reset Token", skip to Step 4)
3. Click **"Yes, do it!"** in the confirmation popup

A bot user is now created and associated with your application.

### Step 4 — Copy the Bot Token

1. On the Bot page, find the **TOKEN** section
2. Click **"Reset Token"** (required to see the token for the first time)
3. Confirm with your password or 2FA code if asked
4. Click **"Copy"** to copy the token to your clipboard
5. Paste it somewhere safe (a text file, password manager) — you will need it in Part 6

The token is a long string with two periods in it (three segments). Example structure:
```
<bot-user-id-base64>.<timestamp>.<hmac-signature>
```

> **WARNING: Your bot token is a secret — treat it like a password.** Do NOT share it in Discord, GitHub, email, or chat. If you accidentally expose it, click "Reset Token" immediately to invalidate the old one.

> **Common Mistake:** People copy the "Application ID" (Client ID) from the General Information page instead of the Bot Token. The Application ID is a plain number. The Bot Token is a long string with periods in it, starting with your bot's numeric ID.

### Step 5 — Enable Message Content Intent (CRITICAL)

This step is the most commonly missed. Without it, the bot can see that messages exist but cannot read what they say.

1. Still on the **Bot** page, scroll down to **"Privileged Gateway Intents"**
2. Find **"MESSAGE CONTENT INTENT"** and toggle it **ON** (the toggle should turn blue/green)
3. Click **"Save Changes"** at the bottom of the page

Expected result: The toggle next to "MESSAGE CONTENT INTENT" is blue/active.

> **Why is this needed?** Discord split message reading into "privileged" intents in 2022. Without explicitly enabling `MESSAGE CONTENT INTENT` here AND in the code (OpenClaw already does this), the bot receives an empty string for all message content. Commands like `!claw open` will silently do nothing.

### Step 6 — Generate the OAuth2 Invite URL

Now you will generate a URL that lets you add the bot to your Discord server.

1. In the left sidebar, click **"OAuth2"**
2. Click **"URL Generator"** (it appears as a sub-menu under OAuth2)
3. Under **SCOPES**, check both:
   - `bot` (required — adds the bot user to the server)
   - `applications.commands` (required — enables slash commands)
4. Under **BOT PERMISSIONS**, check:
   - `Send Messages`
   - `Read Messages / View Channels`
   - `Read Message History`
   - `Add Reactions`
5. At the bottom of the page, a **Generated URL** appears automatically
6. Click **"Copy"** to copy this URL

The URL looks like:
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_APP_ID&permissions=68608&scope=bot%20applications.commands
```

### Step 7 — Invite the Bot to Your Server

1. Paste the copied URL into your browser's address bar and press Enter
2. A Discord authorization page opens
3. From the "Add to Server" dropdown, select the server you want the bot in
4. Click **"Continue"**
5. Review the permission list and click **"Authorize"**
6. Complete the CAPTCHA
7. You should see "Authorized!" — the bot is now in your server (shown as offline until OpenClaw connects)

### Step 8 — Verify the Token (Optional)

You can verify your token is valid without running any Python code. Run this from any terminal (replace `YOUR_TOKEN_HERE` with your actual token):

```bash
curl -s -H "Authorization: Bot YOUR_TOKEN_HERE" \
  https://discord.com/api/v10/users/@me | python3 -m json.tool
```

Expected output:
```json
{
  "id": "1167923456789012345",
  "username": "OpenClaw",
  "bot": true,
  ...
}
```

If you see your bot's username, the token is valid and working.

If you see `{"message": "401: Unauthorized", ...}`, the token is wrong or was reset. Go back to Step 4 and copy it again.

---

## Part 5: Create Your Slack Bot

Slack bots use a different setup than Discord. You need TWO tokens: one for connecting to Slack's real-time WebSocket (called Socket Mode), and one for making API calls like sending messages.

**Why Socket Mode?** Unlike Discord which has built-in WebSocket support, Slack normally requires your bot to have a publicly accessible HTTPS URL (webhook). Since your Jetson is behind a home router and does not have a public IP, Socket Mode lets the Jetson establish an outbound connection to Slack instead — no port forwarding needed.

### Step 1 — Go to the Slack API Dashboard

Open your browser and navigate to:
```
https://api.slack.com/apps
```

Log in with your Slack account.

### Step 2 — Create a New App

1. Click **"Create New App"**
2. Select **"From scratch"** (NOT "From an app manifest")
3. In the dialog:
   - **App Name:** `OpenClaw`
   - **Pick a workspace:** Select your Slack workspace
4. Click **"Create App"**

You are now on the app's "Basic Information" page.

### Step 3 — Enable Socket Mode

1. In the left sidebar, click **"Socket Mode"** (under Settings)
2. Toggle **"Enable Socket Mode"** to **ON**
3. A dialog appears asking you to create an App-Level Token:
   - **Token Name:** `openclaw-socket`
   - **Scopes:** `connections:write` is already selected — do not change it
4. Click **"Generate"**
5. Copy the token shown — it starts with `xapp-` — this is your `SLACK_APP_TOKEN`
6. Click **"Done"**

> **Save the xapp- token now.** If you close this dialog, you can find it again under: Basic Information > App-Level Tokens > click the token name.

### Step 4 — Add Bot Token Scopes

1. In the left sidebar, click **"OAuth & Permissions"**
2. Scroll down to the **"Scopes"** section
3. Under **"Bot Token Scopes"**, click **"Add an OAuth Scope"** and add each of these one by one:
   - `chat:write` — lets the bot send messages
   - `app_mentions:read` — lets the bot receive @mentions
   - `im:history` — lets the bot read direct messages
   - `reactions:write` — lets the bot add emoji reactions (the "thinking" indicator)

> **WARNING: If you add scopes after installing the app, you MUST reinstall it for the new scopes to take effect.** Always add all scopes before clicking Install in Step 5.

### Step 5 — Install the App to Your Workspace

1. Still on **"OAuth & Permissions"**, scroll to the very top
2. Click **"Install to Workspace"**
3. Review the permissions and click **"Allow"**
4. You will be redirected back to the same page
5. Copy the **"Bot User OAuth Token"** — it starts with `xoxb-` — this is your `SLACK_BOT_TOKEN`

You now have two tokens:
- `xapp-1-...` — App-Level Token (used for Socket Mode WebSocket connection)
- `xoxb-...` — Bot User OAuth Token (used for API calls: sending messages, reactions)

> **Common Mistake:** Mixing up the two tokens. `xapp-` goes in `SLACK_APP_TOKEN`. `xoxb-` goes in `SLACK_BOT_TOKEN`. Using them in the wrong variable causes a confusing "invalid_auth" error.

### Step 6 — Enable Event Subscriptions

1. In the left sidebar, click **"Event Subscriptions"**
2. Toggle **"Enable Events"** to **ON**
3. There is NO Request URL to configure — Socket Mode handles this automatically
4. Under **"Subscribe to bot events"**, click **"Add Bot User Event"** and add:
   - `app_mention` — fires when someone @mentions the bot in a channel
   - `message.im` — fires when someone sends the bot a direct message
5. Click **"Save Changes"**
6. A yellow banner may appear saying the app needs reinstallation — click **"reinstall your app"** in that banner and click Allow again

> **Why are these events needed?** Without subscribing to events, the bot receives nothing at all. It connects to Slack via Socket Mode but no messages are delivered. `app_mention` is what fires when you type `@OpenClaw open claw` in a channel.

### Step 7 — Invite the Bot to a Channel

The bot can only receive messages from channels it has been invited to.

1. Open your Slack workspace
2. Navigate to the channel where you want OpenClaw to work
3. Type in the message box:
   ```
   /invite @OpenClaw
   ```
4. Press Enter

Expected result:
```
OpenClaw was added to #channel-name by you
```

---

## Part 6: Install OpenClaw

Now that the hardware is wired and you have your bot tokens, it is time to install OpenClaw on the Jetson.

### Step 1 — Connect to the Jetson

Option A (with monitor): Use the Jetson directly with keyboard and monitor.

Option B (headless/SSH): If you know the Jetson's IP address, SSH from your computer:
```bash
ssh YOUR_JETSON_USERNAME@YOUR_JETSON_IP
```

Replace `YOUR_JETSON_USERNAME` with the username you set during first boot (e.g., `jetson`) and `YOUR_JETSON_IP` with the Jetson's IP address.

To find the Jetson's IP address from another computer on the same network:
```bash
# On Linux/Mac:
ping jetson-ubuntu.local
```

Expected output (look for the IP in parentheses):
```
PING jetson-ubuntu.local (192.168.1.42): 56 data bytes
```

Or check your router's DHCP client list. Look for a device named `jetson-ubuntu` or the hostname you set during first boot.

### Step 2 — Clone the Repository

All the following commands are run on the Jetson (either in the local terminal or via SSH).

```bash
git clone https://github.com/rhuanssauro/jetson-openclaw.git
cd jetson-openclaw
```

Expected output:
```
Cloning into 'jetson-openclaw'...
remote: Enumerating objects: 47, done.
remote: Counting objects: 100% (47/47), done.
remote: Compressing objects: 100% (30/30), done.
Receiving objects: 100% (47/47), 18.34 KiB | 1.05 MiB/s, done.
Resolving deltas: 100% (8/8), done.
```

> **Tip:** After `cd jetson-openclaw`, your terminal prompt will show you are inside the project folder. All remaining commands in Part 6 must be run from this folder. If you close the terminal and open a new one, re-run `cd ~/jetson-openclaw` before continuing.

### Step 3 — Run the Setup Script

The setup script (`scripts/setup.sh`) automates the system configuration. It does the following:
1. Installs Ansible, curl, and git via apt (Ansible is a tool that runs a checklist of setup steps)
2. Runs the Ansible playbook which:
   - Updates the system packages
   - Installs Docker (the container runtime that runs OpenClaw)
   - Installs the NVIDIA Container Runtime (lets Docker access the GPU)
   - Adds your user to the `docker` and `gpio` groups (allows running Docker and accessing GPIO without root)
   - Installs GPIO udev rules (allows non-root GPIO access)
   - Creates an 8GB swap file (virtual memory on disk, critical for stable LLM operation)
3. Pulls and starts the Docker Compose stack

Run it:
```bash
chmod +x scripts/setup.sh
sudo ./scripts/setup.sh
```

Expected output (takes 5–15 minutes):
```
=== OpenClaw: Starting Setup on Jetson Orin Nano ===
--> Installing dependencies...
...
PLAY [Setup Jetson Orin Nano for OpenClaw] *****
...
TASK [Update apt cache and upgrade system] *** ok
TASK [Install essential packages] *** changed
TASK [Configure Docker group] *** changed
TASK [Ensure NVIDIA Container Runtime is setup] *** changed
TASK [Setup swap file (essential for 8GB RAM + LLM)] *** changed
...
PLAY RECAP: localhost ok=12 changed=8 unreachable=0 failed=0
=== Setup Complete! ===
```

The important line is `failed=0` in the PLAY RECAP. If you see `failed=1` or higher, there was an error. Scroll up to find the `TASK [...] *** FAILED` line for details.

> **WARNING: After the setup script finishes, you must log out and log back in** (or reconnect via SSH) before Docker commands will work. The script adds your user to the `docker` group, but the group change only takes effect in new login sessions. See [Problem 10](#problem-10-docker-command-not-found-after-setup) if you forget.

> **If the Ansible playbook fails with "No module named ansible"**, install it manually first:
> ```bash
> sudo apt-get install -y ansible
> ```
> Then re-run the setup script.

> **If Docker Compose fails to start**, check the logs in Step 7.

### Step 4 — Configure the .env File

The `.env` file is where you put your secret bot tokens. It is a plain text file that the application reads on startup. It is never committed to git — your secrets stay on the Jetson only.

```bash
cp .env.example .env
nano .env
```

You will see a file like this — replace the placeholder values with your actual tokens:

```ini
# === Discord ===
# Your bot token from discord.com/developers/applications > Bot > TOKEN
DISCORD_TOKEN=YOUR_DISCORD_TOKEN_HERE

# === Slack ===
# Bot User OAuth Token from api.slack.com/apps > OAuth & Permissions
SLACK_BOT_TOKEN=xoxb-YOUR-SLACK-BOT-TOKEN-HERE

# App-Level Token from api.slack.com/apps > Basic Information > App-Level Tokens
SLACK_APP_TOKEN=xapp-YOUR-SLACK-APP-TOKEN-HERE

# === LLM Configuration ===
# Do NOT change OLLAMA_HOST — this is the hostname inside Docker networking
OLLAMA_HOST=http://ollama:11434

# The AI model to use. The default is best for this hardware.
OLLAMA_MODEL=llama3:8b-instruct-q4_K_M
```

Save and exit nano: Press `Ctrl+X`, then `Y`, then `Enter`.

> **Note on OLLAMA_HOST:** The value `http://ollama:11434` uses the Docker Compose service name `ollama` as the hostname. Inside Docker's internal network, containers can reach each other by service name. Do NOT change this to `localhost` or `127.0.0.1` — it will fail to connect to the AI model.

> **If you only want Discord** (no Slack), leave the `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` lines empty or remove them. OpenClaw will start with only Discord.

> **If you only want Slack** (no Discord), leave `DISCORD_TOKEN` empty. OpenClaw requires at least one bot token to be configured — if all tokens are missing, it will print an error and exit.

### Step 5 — Pull the LLM Model

The AI model must be downloaded before it can be used. The model file is large (~4.7 GB), so this will take several minutes depending on your internet connection.

First, confirm the Docker stack started (it should have started automatically at the end of Step 3):
```bash
docker ps
```

Expected output (two containers running):
```
CONTAINER ID   IMAGE                  COMMAND               STATUS
a1b2c3d4e5f6   ollama/ollama:latest   "/bin/ollama serve"   Up 2 minutes
b2c3d4e5f6a1   jetson-openclaw-...    "python3 -u src/..."  Up 2 minutes
```

If you see `Up X minutes` in the STATUS column, the containers are running. If the output is empty, run:
```bash
docker compose -f docker/docker-compose.yml up -d
```

Now pull the model:
```bash
docker exec openclaw-ollama ollama pull llama3:8b-instruct-q4_K_M
```

Expected output (the bar fills as it downloads):
```
pulling manifest
pulling 00e1317cbf74... ████████████████ 100% 4.7 GB
pulling 4fa551d4f938... ████████████████ 100% 12 KB
verifying sha256 digest
writing manifest
success
```

This downloads the model into a Docker volume called `ollama_data` which persists across container restarts — you only need to do this once.

> **WARNING: This download requires ~5 GB of free disk space.** Check available space before pulling:
> ```bash
> df -h /
> ```
> Look for the `Avail` column on the line for `/`. You need at least 6 GB free.

### Step 6 — Start the Full Stack

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

What this does:
- `up` — starts the services
- `-d` — runs them in the background (detached), so they keep running after you close the terminal
- `--build` — builds the `openclaw` container from the Dockerfile.jetson

Expected output:
```
[+] Building 45.3s (12/12) FINISHED
[+] Running 2/2
 ✔ Container openclaw-ollama   Started
 ✔ Container openclaw-bot      Started
```

### Step 7 — Verify Everything is Running

**Check container status:**
```bash
docker ps
```

Expected output (two containers running):
```
CONTAINER ID   IMAGE                  COMMAND               STATUS
a1b2c3d4e5f6   ollama/ollama:latest   "/bin/ollama serve"   Up 3 minutes
b2c3d4e5f6a1   jetson-openclaw-...    "python3 -u src/..."  Up 2 minutes
```

**Check the bot logs:**
```bash
docker logs openclaw-bot
```

Expected output:
```
2026-02-23 10:00:01 | INFO | Initializing OpenClaw System...
2026-02-23 10:00:01 | INFO | Hardware initialized (GPIO)
2026-02-23 10:00:03 | INFO | Connected to local LLM (Ollama)
2026-02-23 10:00:04 | INFO | Starting Discord Bot...
2026-02-23 10:00:05 | INFO | Starting Slack Bot (Socket Mode)...
2026-02-23 10:00:06 | INFO | Discord Bot connected as OpenClaw#1234
```

If you see "Connected to local LLM (Ollama)" and "Discord Bot connected as OpenClaw", the system is fully operational.

> **If you see "Could not connect to Ollama. AI features will be limited."**, wait 30 seconds and check again — Ollama may still be loading. Run `docker logs openclaw-ollama` to see if it is ready. See [Problem 1](#problem-1-could-not-connect-to-ollama-ai-features-will-be-limited) for detailed steps.

> **If the bot logs show hardware in MOCK mode** (`Hardware initialized (MOCK)`), this is expected when running on a non-Jetson machine or when the GPIO devices are not accessible. On the actual Jetson with the udev rules installed, it should show `Hardware initialized (GPIO)`. See [Problem 4](#problem-4-hardware-initialized-mock-in-logs-but-i-have-a-servo-connected) if you expected real GPIO.

> **If you see "No bot tokens provided!"**, your `.env` file is either missing or all token variables are empty. Re-check Step 4.

---

## Part 7: Using OpenClaw — Practical Examples

### Discord Usage

OpenClaw responds to two types of messages in Discord:
1. **Prefix commands** starting with `!claw ` (note the space after `claw`) — these control hardware
2. **Mentions** (`@OpenClaw message`) or **direct messages (DMs)** — these go to the AI

#### Example 1: Open the Claw

Type in any Discord channel where the bot is present:
```
!claw open
```

Expected bot response:
```
Claw is now OPEN
```

The servo motor will move to the open position (7.5% duty cycle, ~1500µs pulse).

#### Example 2: Close the Claw

```
!claw close
```

Expected bot response:
```
Claw is now CLOSED
```

The servo motor will move to the closed position (2.5% duty cycle, ~500µs pulse).

#### Example 3: Check Current Status

```
!claw status
```

Expected bot response:
```
Status: OPEN
```

The status reflects the last command sent (OPEN, CLOSED, or UNKNOWN if no command has been issued yet in this session).

#### Example 4: Ask the AI a Question (Mention)

```
@OpenClaw What is the capital of France?
```

Expected bot response sequence:

Step 1 — appears immediately while the AI processes:
```
Thinking...
```

Step 2 — appears a few seconds later:
```
The capital of France is Paris. It has been the capital since the 10th century and is home to iconic landmarks such as the Eiffel Tower and the Louvre.
```

> **Why does it say "Thinking..." first?** The local AI model on the Jetson takes 2–5 seconds to generate a response. The "Thinking..." message appears immediately so you know your question was received.

#### Example 5: DM Conversation

Send a direct message (DM) to OpenClaw in Discord — you do NOT need to @mention it in DMs.

```
You: Tell me a joke about robots
OpenClaw: Why did the robot go on vacation? Because it needed to recharge its batteries!
```

```
You: What can you actually do?
OpenClaw: I'm OpenClaw, your personal AI assistant running on a Jetson Orin Nano!
I can chat with you, answer questions, and control a physical robotic claw.
Try typing !claw open or !claw close in the main channel to control the hardware.
```

#### Tips for Getting Good Responses from the Local AI

- **Be specific:** "Explain how Docker containers work in simple terms" gives better results than "what is docker"
- **Be patient:** The first response after a cold start (Ollama was idle for a while) takes 30–60 seconds while the model loads into memory. Subsequent responses are much faster.
- **Keep prompts under 500 words:** Very long inputs slow down response time on 8GB RAM
- **The AI has no memory between conversations:** Each message is independent. The AI does not remember what you asked before.
- **Use DMs for private questions:** DMs work identically to channel mentions — both go to the AI

---

### Slack Usage

In Slack, OpenClaw responds to:
1. **@mentions** in channels where it has been invited
2. **Direct messages (DMs)**

For hardware commands, include "open claw" or "close claw" in your @mention. For AI questions, mention the bot with any other text.

#### Example 1: Open the Claw via Slack

In a channel where OpenClaw has been invited, type:
```
@OpenClaw open claw
```

Expected bot response:
```
Claw is now OPEN
```

#### Example 2: Close the Claw via Slack

```
@OpenClaw close claw
```

Expected bot response:
```
Claw is now CLOSED
```

#### Example 3: Ask the AI a Question via Slack

```
@OpenClaw Explain Docker in one sentence
```

Expected bot behavior:
1. OpenClaw adds a `:thinking_face:` emoji reaction to your message (appears immediately)
2. A few seconds later, it sends:
   ```
   @YourName Docker is a platform that packages applications and their dependencies into portable containers that run consistently across different computing environments.
   ```
3. The `:thinking_face:` emoji is removed

#### Example 4: Slack DM

Open a DM with OpenClaw (click its name > "Message"):
```
You: What is Python?
OpenClaw: Python is a high-level, interpreted programming language known for its clean and readable syntax...
```

#### Example 5: Get Hardware Status in Slack

There is no prefix command for status in Slack. Ask the AI instead:
```
@OpenClaw what is the status of the claw?
```

The AI will respond with a description based on its last known state. For the authoritative hardware state, use Discord's `!claw status` command.

#### Slack Command Summary

| What you type | What happens |
|---------------|-------------|
| `@OpenClaw open claw` | Servo moves to open position |
| `@OpenClaw close claw` | Servo moves to closed position |
| `@OpenClaw <any question>` | AI generates a response |
| DM to OpenClaw | AI generates a response |

---

## Part 8: Model Selection Guide

The "model" is the AI brain that generates responses. Different models use different amounts of memory and produce different quality responses. On the Jetson Orin Nano 8GB, memory is the primary constraint.

### Model Comparison Table

| Model Name | Parameters | RAM Usage | Speed (tokens/sec) | Quality | Best For |
|-----------|-----------|-----------|-------------------|---------|----------|
| `llama3:8b-instruct-q4_K_M` | 8B | ~5.0 GB | 8–12 | ★★★★☆ | **Default — best balance** |
| `mistral:7b-instruct-q4_K_M` | 7B | ~4.5 GB | 10–15 | ★★★★☆ | Slightly faster, similar quality |
| `llama3.2:3b` | 3B | ~2.2 GB | 20–25 | ★★★☆☆ | Fast responses, lower quality |
| `phi3:mini-q4_K_M` | 3.8B | ~2.5 GB | 20–30 | ★★★☆☆ | Small, efficient |
| `gemma2:2b` | 2B | ~1.8 GB | 25–35 | ★★☆☆☆ | Fastest, basic responses |
| `tinyllama:1.1b` | 1.1B | ~0.8 GB | 40+ | ★☆☆☆☆ | Testing only — poor coherence |

> **WARNING: Do NOT use these models — they will crash the system:**
> - `llama3:8b-instruct-q8_0` — requires ~8.5 GB RAM, exceeds the Jetson's 8GB unified memory
> - Any model larger than 8B parameters at Q4 quantization
>
> The Jetson uses unified memory shared between CPU and GPU. There is no separate GPU VRAM. If the model plus operating system exceed 8GB total, the system will kill the Ollama process mid-response.

### Recommended Model Per Use Case

| Use Case | Recommended Model | Reason |
|----------|------------------|--------|
| General assistant / chat | `llama3:8b-instruct-q4_K_M` | Best instruction-following quality |
| Quick responses (snappy UX) | `llama3.2:3b` | 2x faster responses |
| Code help | `mistral:7b-instruct-q4_K_M` | Good at structured output |
| Very limited RAM / running heavy workloads | `phi3:mini-q4_K_M` | Frees up ~2.5 GB more RAM |

### How to Switch Models (Step by Step)

**Step 1 — Pull the new model** (if you have not already):
```bash
docker exec openclaw-ollama ollama pull mistral:7b-instruct-q4_K_M
```

Wait for the download to complete. You can check available models:
```bash
docker exec openclaw-ollama ollama list
```

Expected output:
```
NAME                            ID              SIZE      MODIFIED
llama3:8b-instruct-q4_K_M      a6990ed6be10    4.7 GB    2 hours ago
mistral:7b-instruct-q4_K_M     61e88e884507    4.1 GB    1 minute ago
```

**Step 2 — Edit the .env file:**
```bash
cd ~/jetson-openclaw
nano .env
```

Change the `OLLAMA_MODEL` line:
```ini
OLLAMA_MODEL=mistral:7b-instruct-q4_K_M
```

Save: `Ctrl+X`, `Y`, `Enter`.

**Step 3 — Restart only the bot container** (Ollama does not need to restart):
```bash
docker compose -f docker/docker-compose.yml restart openclaw
```

Expected output:
```
[+] Restarting 1/1
 ✔ Container openclaw-bot  Started
```

**Step 4 — Verify the new model is being used:**
```bash
docker logs openclaw-bot --tail 20
```

You should see the bot reconnecting. Test it by sending a message in Discord or Slack.

### How to Roll Back to the Previous Model

If the new model performs poorly, revert in 2 commands:
```bash
# Change .env back
sed -i 's/^OLLAMA_MODEL=.*/OLLAMA_MODEL=llama3:8b-instruct-q4_K_M/' .env

# Restart the bot
docker compose -f docker/docker-compose.yml restart openclaw
```

The old model is already on disk — switching back takes only a few seconds.

### How to Try a Brand New Model

```bash
# 1. Find a model at ollama.com/library
# 2. Pull it (check the size first — must fit in ~5 GB for safe operation)
docker exec openclaw-ollama ollama pull MODEL_NAME_HERE

# 3. Update .env
nano .env  # Change OLLAMA_MODEL=MODEL_NAME_HERE

# 4. Restart the bot
docker compose -f docker/docker-compose.yml restart openclaw

# 5. If it fails or uses too much memory, roll back
sed -i 's/^OLLAMA_MODEL=.*/OLLAMA_MODEL=llama3:8b-instruct-q4_K_M/' .env
docker compose -f docker/docker-compose.yml restart openclaw
```

---

## Part 9: Troubleshooting

### Diagnostic Commands Cheat Sheet

```bash
# View real-time logs for both containers (press Ctrl+C to stop)
docker logs -f openclaw-bot
docker logs -f openclaw-ollama

# Check what containers are running
docker ps

# Check all containers including stopped ones
docker ps -a

# Monitor Jetson CPU, GPU, RAM, and power draw (press Ctrl+C to stop)
tegrastats

# Check disk space (important for model storage)
df -h

# Check RAM and swap usage
free -h

# Restart all services
docker compose -f docker/docker-compose.yml restart

# Stop all services
docker compose -f docker/docker-compose.yml down

# Start all services
docker compose -f docker/docker-compose.yml up -d
```

---

### Problem 1: "Could not connect to Ollama. AI features will be limited."

**Symptom:** You see this warning in `docker logs openclaw-bot`.

**Cause:** The Ollama container is not ready when the bot starts, or Ollama is still loading.

**Fix:**
```bash
# Check if Ollama is running
docker ps | grep ollama
```

Expected output (shows the container is running):
```
a1b2c3d4e5f6   ollama/ollama:latest   "/bin/ollama serve"   Up 5 minutes
```

If the output is empty, the Ollama container stopped. Check why:
```bash
docker logs openclaw-ollama --tail 50
```

If Ollama is running, test the API directly:
```bash
curl http://localhost:11434/
```

Expected output:
```
Ollama is running
```

If that works, the issue was a timing race — the bot started before Ollama was ready. Restart the bot:
```bash
docker compose -f docker/docker-compose.yml restart openclaw
```

---

### Problem 2: The bot is online in Discord but `!claw open` does nothing

**Symptom:** The bot appears online (green dot) but does not respond to commands.

**Cause A — Message Content Intent not enabled.**

Fix: Go to Discord Developer Portal > Your App > Bot > Privileged Gateway Intents > Enable "MESSAGE CONTENT INTENT" > Save Changes > Restart the bot container:
```bash
docker compose -f docker/docker-compose.yml restart openclaw
```

**Cause B — Wrong command prefix.**

The prefix is `!claw ` (with a space after `claw`). Make sure you type `!claw open`, not `!clawopen` or `!open`.

---

### Problem 3: Slack bot does not respond to @mentions

**Symptom:** You mention `@OpenClaw` in a channel but nothing happens.

**Cause A — Bot not invited to the channel.**

Fix: Type this in the Slack channel:
```
/invite @OpenClaw
```

**Cause B — Event Subscriptions not configured.**

Fix: Go to api.slack.com/apps > Your App > Event Subscriptions > Enable Events > Add `app_mention` and `message.im` events > Save Changes > Reinstall app.

**Cause C — Wrong token in .env.**

Fix: Open `.env` and double-check:
- `SLACK_BOT_TOKEN` must start with `xoxb-`
- `SLACK_APP_TOKEN` must start with `xapp-`

They are often swapped. Check the bot logs for "invalid_auth":
```bash
docker logs openclaw-bot | grep -i "invalid\|slack\|error"
```

---

### Problem 4: "Hardware initialized (MOCK)" in logs but I have a servo connected

**Symptom:** The servo does not move even though it is wired correctly. Logs show MOCK mode.

**Cause:** The bot container cannot access the GPIO devices on the host system.

**Fix — Check udev rules are installed:**
```bash
ls /etc/udev/rules.d/99-openclaw-gpio.rules
```

Expected output (the file path is printed, confirming it exists):
```
/etc/udev/rules.d/99-openclaw-gpio.rules
```

If you see "No such file or directory", install the rules:
```bash
sudo cp hardware/udev/99-openclaw-gpio.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

**Fix — Check your user is in the gpio group:**
```bash
groups $USER
```

Expected output (includes `gpio` in the list):
```
YOUR_USERNAME adm dialout cdrom sudo audio video plugdev gpio docker
```

If `gpio` is not listed:
```bash
sudo usermod -aG gpio $USER
# Then log out and log back in for the group change to take effect
exit
```

**Fix — Verify GPIO devices exist:**
```bash
ls -la /dev/gpiochip*
```

Expected output:
```
crw-rw---- 1 root gpio 254, 0 Feb 23 10:00 /dev/gpiochip0
crw-rw---- 1 root gpio 254, 1 Feb 23 10:00 /dev/gpiochip1
```

If no `gpiochip` devices exist, JetPack is not installed correctly or the system is not running on real Jetson hardware. Re-flash using Part 3.

---

### Problem 5: "OOM killed" or Ollama crashes mid-response

**Symptom:** Ollama container stops unexpectedly during inference. Running `dmesg | grep OOM` shows killed processes.

**Cause:** Out of memory — the 8GB unified RAM is exhausted.

**Fix — Verify swap is active:**
```bash
free -h
```

Expected output (look for a non-zero Swap row):
```
               total        used        free      shared  buff/cache   available
Mem:           7.5Gi       5.2Gi       512Mi       128Mi       1.7Gi       2.0Gi
Swap:          8.0Gi       1.2Gi       6.8Gi
```

If the Swap total shows `0B`, re-enable it:
```bash
sudo swapon /swapfile
```

If `/swapfile` does not exist, re-run the Ansible playbook to recreate it:
```bash
sudo ansible-playbook ansible/setup_jetson.yml
```

**Fix — Use a smaller model:**

Switch to `llama3.2:3b` or `phi3:mini-q4_K_M` which use ~2–3 GB less RAM. See [How to Switch Models](#how-to-switch-models-step-by-step) in Part 8.

---

### Problem 6: Docker build fails with "manifest for dustynv/l4t-python:3.10-r36.4.0 not found"

**Symptom:** `docker compose up --build` fails with a manifest error.

**Cause:** The `dustynv/l4t-python` base image for the Jetson is large (~5 GB) and the pull may have failed, or the tag has changed.

**Fix — Pull the base image explicitly first:**
```bash
docker pull dustynv/l4t-python:3.10-r36.4.0
```

Expected output (image layers downloading):
```
3.10-r36.4.0: Pulling from dustynv/l4t-python
...
Status: Downloaded newer image for dustynv/l4t-python:3.10-r36.4.0
```

Then rebuild:
```bash
docker compose -f docker/docker-compose.yml up -d --build
```

If the tag is no longer available (the image was removed from Docker Hub), check `https://hub.docker.com/r/dustynv/l4t-python/tags` for the latest tag matching JetPack 6 (L4T r36.x). Update the `FROM` line in `docker/Dockerfile.jetson` to use the new tag.

---

### Problem 7: Slow AI responses (taking 30+ seconds for every message)

**Symptom:** Every message to the AI takes 30–60 seconds, not just the first one.

**Cause:** `OLLAMA_KEEP_ALIVE` is not set — the model is being unloaded from memory between requests.

**Fix — Verify the environment variable is set in docker-compose.yml:**
```bash
grep -A5 "ollama:" docker/docker-compose.yml | grep KEEP_ALIVE
```

Expected output:
```
      - OLLAMA_KEEP_ALIVE=24h
```

If the output is empty, the value is missing from your docker-compose.yml. Add it under the `ollama` service's `environment` section:
```yaml
environment:
  - OLLAMA_KEEP_ALIVE=24h
```

Then restart:
```bash
docker compose -f docker/docker-compose.yml restart ollama
```

---

### Problem 8: Servo vibrates/jitters but does not move to position

**Symptom:** The servo makes a buzzing/vibrating sound but does not move cleanly.

**Cause A — No common ground.**

Fix: Verify Pin 34 (Jetson GND) is connected to the BEC's GND terminal. If you have a multimeter, measure the voltage between Jetson GND (Pin 34) and BEC GND — it should read 0V. Any non-zero reading means the grounds are not shared. See [Appendix B](#appendix-b-jetson-orin-nano-gpio-pinout) for the Pin 34 location.

**Cause B — Signal voltage too weak.**

Most modern servos accept 3.3V signal. Some older MG995/MG996R clones require 5V signal.

Fix: Add a 3.3V-to-5V logic level shifter between Pin 33 and the servo signal wire. These are available online for under $5.

**Cause C — Duty cycle values need calibration.**

Different servo models respond to slightly different duty cycle ranges.

Fix: Modify the values in `src/hardware/claw_controller.py`:
- `open_claw()`: Try values between 5.0 and 10.0 for `ChangeDutyCycle`
- `close_claw()`: Try values between 2.0 and 5.0

After changing the file, rebuild and restart:
```bash
docker compose -f docker/docker-compose.yml up -d --build
```

---

### Problem 9: git clone fails or "Permission denied (publickey)"

**Symptom:** `git clone` fails with a key error.

**Cause:** You may have accidentally used an SSH URL. The repository uses HTTPS by default, but GitHub may present the SSH URL in some contexts.

**Fix — Use HTTPS instead:**
```bash
git clone https://github.com/rhuanssauro/jetson-openclaw.git
```

HTTPS requires no SSH key and works from any machine.

---

### Problem 10: "docker: command not found" after setup

**Symptom:** After the setup script runs, `docker` commands fail with "command not found" or "permission denied".

**Cause:** The setup script added your user to the `docker` group but the change requires starting a new login session.

**Fix:**
```bash
# Option A: Re-login (closes current session)
exit
ssh YOUR_JETSON_USERNAME@YOUR_JETSON_IP

# Option B: Apply the group change in the current terminal without re-login
newgrp docker
```

> **WARNING: Option B (`newgrp docker`) only fixes the current terminal window.** If you open a new terminal, you will need to run `newgrp docker` again in that window, until you fully log out and log back in once.

Verify Docker works:
```bash
docker ps
```

Expected output (no error, just the container list or empty table):
```
CONTAINER ID   IMAGE   COMMAND   CREATED   STATUS   PORTS   NAMES
```

---

## Part 10: Development Guide

### Running Locally on a Laptop (Mock Mode)

You do not need a Jetson to develop OpenClaw. On any computer without the `Jetson.GPIO` library, the hardware automatically enters mock mode — all GPIO operations become no-ops and the servo state is tracked in memory only.

**Step 1 — Create a virtual environment:**

A virtual environment is an isolated Python installation for this project. It prevents the packages you install here from conflicting with other Python projects on your computer. Think of it as a clean workspace that only contains what OpenClaw needs.

```bash
cd ~/jetson-openclaw
python3 -m venv .venv
source .venv/bin/activate
```

After running `source .venv/bin/activate`, your terminal prompt will change to show `(.venv)` at the start — this means the virtual environment is active:
```
(.venv) you@computer:~/jetson-openclaw$
```

> **WARNING: You must activate the virtual environment (`source .venv/bin/activate`) every time you open a new terminal** before running the application or tests. If you see "No module named discord" or similar import errors, the virtual environment is likely not active.

**Step 2 — Install dependencies:**
```bash
pip install -r requirements.txt
```

Expected output (many packages installing):
```
Collecting discord.py>=2.3.0
  Downloading discord.py-2.3.2-py3-none-any.whl (1.1 MB)
...
Successfully installed discord.py-2.3.2 loguru-0.7.2 ...
```

Or with `uv` (faster — 10x quicker than pip):
```bash
uv pip install -r requirements.txt
```

**Step 3 — Create a local .env:**
```bash
cp .env.example .env
nano .env
```

Set `OLLAMA_HOST=http://localhost:11434` for local development (if you have Ollama running locally), or leave it pointing to the default — AI features will gracefully degrade with a warning if Ollama is not reachable.

**Step 4 — Run the application:**
```bash
python src/main.py
```

Expected startup logs:
```
INFO | Initializing OpenClaw System...
WARNING | Jetson.GPIO not found, running in MOCK mode
INFO | Hardware initialized (MOCK)
INFO | Connected to local LLM (Ollama)
INFO | Starting Discord Bot...
INFO | Discord Bot connected as OpenClaw#1234
```

Hardware commands (`!claw open`) will respond correctly but will not move any physical servo — the state is tracked in memory only.

---

### Running Tests

Tests are in the `tests/` folder and use the `pytest` framework.

```bash
# From the project root, with virtual environment activated
uvx pytest
```

Expected output:
```
======================== test session starts =========================
platform linux -- Python 3.10.x, pytest-8.x.x
collected 3 items

tests/test_claw.py::TestClawController::test_initial_state PASSED  [ 33%]
tests/test_claw.py::TestClawController::test_open_claw PASSED      [ 66%]
tests/test_claw.py::TestClawController::test_close_claw PASSED     [100%]

========================= 3 passed in 0.05s ==========================
```

All 3 tests must pass before submitting a contribution.

Additional test options:
```bash
# Verbose output — shows each test name and assertion
uvx pytest -v

# Short traceback on failure — easier to read errors
uvx pytest --tb=short
```

---

### Code Structure Walkthrough

```
jetson-openclaw/
├── src/
│   ├── main.py                 # Entry point — starts all services
│   ├── bot/
│   │   ├── discord_bot.py      # Discord commands and message handling
│   │   └── slack_bot.py        # Slack Socket Mode event handling
│   ├── hardware/
│   │   └── claw_controller.py  # GPIO/PWM servo control (mock-capable)
│   └── llm/
│       └── ollama_client.py    # Async HTTP client for Ollama API
├── tests/
│   └── test_claw.py            # Unit tests for ClawController
├── docker/
│   ├── Dockerfile              # Dev/CI image (x86_64, no GPIO)
│   ├── Dockerfile.jetson       # Production image (ARM64 + CUDA)
│   └── docker-compose.yml      # Orchestrates ollama + openclaw
├── ansible/
│   └── setup_jetson.yml        # Jetson OS provisioning playbook
├── hardware/
│   └── udev/
│       └── 99-openclaw-gpio.rules  # Non-root GPIO access rules
└── scripts/
    ├── setup.sh                # First-time setup (runs Ansible + Docker)
    └── update.sh               # Pull latest code and rebuild
```

**How a message flows through the system:**

```mermaid
sequenceDiagram
    participant User as User (Discord/Slack)
    participant Bot as Bot Layer
    participant HW as ClawController
    participant LLM as OllamaClient
    participant Servo as Servo Motor

    User->>Bot: "!claw open" (Discord prefix command)
    Bot->>HW: open_claw()
    HW->>Servo: PWM signal 7.5% duty cycle
    HW-->>Bot: "Claw is now OPEN"
    Bot-->>User: "Claw is now OPEN"

    User->>Bot: "@OpenClaw explain gravity" (mention/DM)
    Bot->>LLM: chat("explain gravity")
    LLM->>LLM: POST /api/generate to Ollama
    LLM-->>Bot: "Gravity is a fundamental force..."
    Bot-->>User: "Gravity is a fundamental force..."
```

---

### How to Add a New Discord Command

This example adds a `!claw wave` command that opens and closes the claw twice.

**Step 1 — Open the Discord bot file:**
```bash
nano ~/jetson-openclaw/src/bot/discord_bot.py
```

**Step 2 — Find the `ClawCommands` class and add a new method:**

Look for this block:
```python
@commands.command(name="close")
async def claw_close(self, ctx: commands.Context) -> None:
    result = self.hardware.close_claw()
    await ctx.send(result)
```

Add the new command directly below it:
```python
@commands.command(name="wave")
async def claw_wave(self, ctx: commands.Context) -> None:
    import asyncio
    await ctx.send("Waving...")
    self.hardware.open_claw()
    await asyncio.sleep(1)
    self.hardware.close_claw()
    await asyncio.sleep(1)
    self.hardware.open_claw()
    await asyncio.sleep(1)
    self.hardware.close_claw()
    await ctx.send("Wave complete!")
```

> **Why `asyncio.sleep(1)`?** The servo takes about 1 second to reach its position (controlled by `claw_controller.py`). Without the sleep, all four position changes would be sent in rapid succession and the servo would only reach the final position, skipping the intermediate ones.

**Step 3 — Rebuild and restart the bot:**
```bash
docker compose -f docker/docker-compose.yml up -d --build openclaw
```

Expected output:
```
[+] Building 12.4s (12/12) FINISHED
[+] Running 1/1
 ✔ Container openclaw-bot  Started
```

**Step 4 — Test it in Discord:**
```
!claw wave
```

Expected responses (with servo movement in between):
```
Waving...
Wave complete!
```

---

### How to Contribute (Fork, Branch, PR)

**Step 1 — Fork the repository:**

Go to `https://github.com/rhuanssauro/jetson-openclaw` and click "Fork" in the top-right. This creates a copy of the repository under your own GitHub account.

**Step 2 — Clone your fork:**
```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/jetson-openclaw.git
cd jetson-openclaw
```

Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username.

**Step 3 — Create a feature branch:**
```bash
git checkout -b feat/my-new-feature
```

Expected output:
```
Switched to a new branch 'feat/my-new-feature'
```

A branch is an isolated copy of the code where you can make changes without affecting the main version.

**Step 4 — Make your changes, then run linting and tests:**
```bash
# Format and lint (automatically fixes style issues)
uvx ruff check . --fix
uvx ruff format .

# Run tests
uvx pytest
```

Expected output for tests: `3 passed` (or more if you added tests). If any test fails, fix it before continuing.

**Step 5 — Commit with a descriptive message:**
```bash
git add .
git commit -m "feat: add !claw wave command"
```

Expected output:
```
[feat/my-new-feature abc1234] feat: add !claw wave command
 1 file changed, 10 insertions(+)
```

**Step 6 — Push and create a Pull Request:**
```bash
git push origin feat/my-new-feature
```

Expected output:
```
Enumerating objects: 5, done.
...
remote: Create a pull request for 'feat/my-new-feature' on GitHub by visiting:
remote:   https://github.com/YOUR_GITHUB_USERNAME/jetson-openclaw/pull/new/feat/my-new-feature
To https://github.com/YOUR_GITHUB_USERNAME/jetson-openclaw.git
 * [new branch]      feat/my-new-feature -> feat/my-new-feature
```

Then go to your fork on GitHub and click "Compare & pull request".

---

## Appendix A: Complete .env Reference

Every environment variable that OpenClaw recognizes, with examples and explanations.

| Variable | Required | Example Value | Description |
|----------|----------|---------------|-------------|
| `DISCORD_TOKEN` | Conditional (at least one bot token required) | `YOUR-DISCORD-BOT-TOKEN-HERE` | Discord bot token. Get from discord.com/developers > App > Bot > Token. |
| `SLACK_BOT_TOKEN` | Conditional (both Slack tokens required together) | `xoxb-your-token` | Slack Bot User OAuth Token. Get from api.slack.com/apps > OAuth & Permissions. Always starts with `xoxb-`. |
| `SLACK_APP_TOKEN` | Conditional (both Slack tokens required together) | `xapp-1-...` | Slack App-Level Token for Socket Mode. Get from api.slack.com/apps > Basic Information > App-Level Tokens. Always starts with `xapp-`. |
| `OLLAMA_HOST` | No (has default) | `http://ollama:11434` | URL of the Ollama API. Default `http://ollama:11434` uses Docker's internal network hostname. Change to `http://localhost:11434` only when running outside Docker. |
| `OLLAMA_MODEL` | No (has default) | `llama3:8b-instruct-q4_K_M` | The Ollama model name used for all AI responses. Must exactly match the model name shown in `ollama list`. Default is the recommended model for 8GB Jetson. |

**Full .env example:**
```ini
# ============================================
# OpenClaw Configuration
# Copy this file to .env and fill in values
# NEVER commit .env to version control
# ============================================

# Discord Bot Token (from discord.com/developers)
DISCORD_TOKEN=YOUR-DISCORD-BOT-TOKEN-HERE

# Slack Bot User OAuth Token (starts with xoxb-)
SLACK_BOT_TOKEN=xoxb-YOUR-SLACK-BOT-TOKEN-HERE

# Slack App-Level Token for Socket Mode (starts with xapp-)
SLACK_APP_TOKEN=xapp-YOUR-SLACK-APP-TOKEN-HERE

# Ollama API endpoint (use Docker service name inside Compose)
OLLAMA_HOST=http://ollama:11434

# AI Model (must be pulled with: docker exec openclaw-ollama ollama pull <model>)
OLLAMA_MODEL=llama3:8b-instruct-q4_K_M
```

---

## Appendix B: Jetson Orin Nano GPIO Pinout

The Jetson Orin Nano 40-pin header is physically identical in layout to a Raspberry Pi header. **Only Pin 33 (PWM0) and Pin 34 (GND) are used by OpenClaw.**

```mermaid
graph TB
    subgraph Header["40-Pin GPIO Header (BOARD Numbering)"]
        subgraph Col1["Left Column (Odd Pins 1–39)"]
            P1["1: 3.3V"]
            P3["3: I2C1_SDA"]
            P5["5: I2C1_SCL"]
            P7["7: GPIO09"]
            P9["9: GND"]
            P11["11: GPIO17"]
            P13["13: GPIO11"]
            P15["15: GPIO05"]
            P17["17: 3.3V"]
            P19["19: SPI0_MOSI"]
            P21["21: SPI0_MISO"]
            P23["23: SPI0_CLK"]
            P25["25: GND"]
            P27["27: I2C0_SDA"]
            P29["29: GPIO06"]
            P31["31: GPIO12"]
            P33["33: PWM0 — SERVO SIGNAL"]
            P35["35: GPIO19"]
            P37["37: GPIO26"]
            P39["39: GND"]
        end
        subgraph Col2["Right Column (Even Pins 2–40)"]
            P2["2: 5V"]
            P4["4: 5V"]
            P6["6: GND"]
            P8["8: UART1_TX"]
            P10["10: UART1_RX"]
            P12["12: I2S0_CLK"]
            P14["14: GND"]
            P16["16: GPIO08"]
            P18["18: GPIO25"]
            P20["20: GND"]
            P22["22: GPIO24"]
            P24["24: SPI0_CS0_N"]
            P26["26: SPI0_CS1_N"]
            P28["28: I2C0_SCL"]
            P30["30: GND"]
            P32["32: GPIO13"]
            P34["34: GND — COMMON GROUND"]
            P36["36: GPIO16"]
            P38["38: I2S0_DIN"]
            P40["40: I2S0_DOUT"]
        end
    end

    style P33 fill:#f39c12,stroke:#fff,color:#fff
    style P34 fill:#50c878,stroke:#fff,color:#fff
```

| Pin | Function | OpenClaw Use |
|-----|----------|-------------|
| **33** | **PWM0 (Hardware PWM)** | **Servo signal — connected here** |
| **34** | **GND** | **Common ground — connected here** |
| 1 | 3.3V Power | Do not use for servo power |
| 2, 4 | 5V Power | Do not use for servo power — see [Part 2 Safety Warnings](#safety-warnings) |

**PWM Signal Parameters (for reference):**

| Parameter | Value |
|-----------|-------|
| Frequency | 50 Hz (20ms period) |
| Open position duty cycle | 7.5% (1500µs pulse) |
| Close position duty cycle | 2.5% (500µs pulse) |
| Signal voltage | 3.3V |

---

## Appendix C: Docker Commands Cheat Sheet

All commands assume you are in the `jetson-openclaw` directory. If you are not sure, run `cd ~/jetson-openclaw` first.

```bash
# ---- Starting and Stopping ----

# Start all services in the background
docker compose -f docker/docker-compose.yml up -d

# Start and rebuild the openclaw container (use after code changes)
docker compose -f docker/docker-compose.yml up -d --build

# Stop all services (containers are removed but volumes are kept)
docker compose -f docker/docker-compose.yml down

# Restart all services
docker compose -f docker/docker-compose.yml restart

# Restart only the bot (picks up .env changes or code changes)
docker compose -f docker/docker-compose.yml restart openclaw

# Restart only Ollama
docker compose -f docker/docker-compose.yml restart ollama

# ---- Logs ----

# Tail logs for the bot (live, Ctrl+C to stop)
docker logs -f openclaw-bot

# Last 50 lines from Ollama
docker logs openclaw-ollama --tail 50

# ---- Inspection ----

# List running containers with status
docker ps

# List all containers including stopped ones
docker ps -a

# Show disk usage by Docker (images, containers, volumes)
docker system df

# ---- Ollama Model Management ----

# List downloaded models
docker exec openclaw-ollama ollama list

# Pull a new model
docker exec openclaw-ollama ollama pull MODEL_NAME

# Run a one-shot test prompt (useful for testing a model before switching)
docker exec openclaw-ollama ollama run MODEL_NAME "Hello, what can you do?"

# Delete a model (frees disk space)
docker exec openclaw-ollama ollama rm MODEL_NAME

# ---- Cleanup ----

# Remove stopped containers
docker container prune

# Remove all unused images (keeps ones in use)
docker image prune

# Full cleanup of unused data (WARNING: also removes unused volumes — model data)
docker system prune --volumes
```

> **WARNING: `docker system prune --volumes` will delete downloaded AI models** stored in the `ollama_data` volume. You will need to re-download them with `docker exec openclaw-ollama ollama pull MODEL_NAME` after running this command.

---

## Appendix D: Useful Links

| Resource | URL | Purpose |
|----------|-----|---------|
| NVIDIA Jetson Download Center | https://developer.nvidia.com/jetson/jetpack | JetPack 6 download, SDK Manager |
| JetPack 6 Release Notes | https://developer.nvidia.com/embedded/jetpack-sdk-61 | What's new in JetPack 6 |
| Jetson Orin Nano Developer Guide | https://developer.nvidia.com/embedded/learn/jetson-orin-nano-devkit-user-guide | Official hardware guide |
| JetsonHacks bootFromExternalStorage | https://github.com/jetsonhacks/bootFromExternalStorage | NVMe boot setup scripts |
| Ollama Model Library | https://ollama.com/library | Browse available AI models |
| Discord Developer Portal | https://discord.com/developers/applications | Create and manage Discord bots |
| Discord.py Documentation | https://discordpy.readthedocs.io/en/stable/ | Python Discord library docs |
| Slack API Dashboard | https://api.slack.com/apps | Create and manage Slack apps |
| Slack SDK for Python | https://slack.dev/python-slack-sdk/ | Python Slack library docs |
| OpenClaw Repository | https://github.com/rhuanssauro/jetson-openclaw | Source code, issues, PRs |
| Jetson Community Forums | https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-embedded-systems/jetson-orin-nano/486 | NVIDIA official support forum |
| r/Jetson on Reddit | https://reddit.com/r/Jetson | Community discussions |

---

*Playbook version 1.1 — Updated 2026-02-23*
*For issues and improvements, open a GitHub issue at https://github.com/rhuanssauro/jetson-openclaw/issues*
