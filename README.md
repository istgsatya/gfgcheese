# 🚀 GFG Course Automation Bot

An **OS-agnostic automation tool** that completely clears GeeksforGeeks courses — including **videos, articles, and quizzes**.

Just clone, run, and let the bot handle everything.
It auto-installs dependencies, bypasses annoying UI interruptions, and saves your login session so you only need to log in once.

---

## ✨ Features

* **🌍 OS-Agnostic**
  Works seamlessly on **Windows, macOS, and Linux**

* **⚙️ Auto Dependency Installer**
  No manual `pip` setup required — installs missing packages automatically

* **🎯 Popup Handler**
  Detects and handles random GFG popups (e.g., feedback prompts) that usually break automation

* **🔐 Persistent Login Session**
  Uses a local Chrome profile — log in once, and you're good forever

* **📉 Bottom-Up Processing Engine**
  Completes course sections in descending order for better stability

---

## ⚠️ Prerequisites

Make sure the following are installed:

1. **Google Chrome**
   https://www.google.com/chrome/

2. **Python 3.x**
   https://www.python.org/downloads/
   *(Windows users: ensure "Add Python to PATH" is checked during installation)*

---

## 🖥️ How to Run (Windows)

### Step 1 — Install Git (if not installed)

Open **PowerShell (Admin)**:

```powershell
winget install --id Git.Git -e --source winget
```

Restart PowerShell after installation.

---

### Step 2 — Clone & Run

```bash
git clone https://github.com/istgsatya/gfgcheese.git
cd gfgcheese
py gfgmkb.py
```

If `py` doesn’t work:

```bash
python gfgmkb.py
```

---

## 🐧 How to Run (Linux / macOS)

### Step 1 — Install Dependencies

**Arch Linux**

```bash
sudo pacman -S git python python-pip
```

**Ubuntu / Debian**

```bash
sudo apt install git python3 python3-pip
```

**macOS (Homebrew)**

```bash
brew install git python
```

---

### Step 2 — Clone & Run

```bash
git clone https://github.com/istgsatya/gfgcheese.git
cd gfgcheese
python3 gfgmkb.py
```

---

## 🛑 Critical Rules (Read Before Running)

### ⏳ 120-Second Login Window

On first run, a Chrome window will open.
You have **120 seconds** to log in manually.
After that, the bot takes over.

---

### 🖥️ Do NOT Minimize Chrome

Keep the browser window visible.
Minimizing it can pause video playback and break automation timing.

---

### 🖱️ Hands Off

Once the bot starts running, **do not interact** with the browser window.

---

### 📱 Avoid Multiple Sessions

Do NOT log into the same GFG account on:

* phone
* another browser
* another device

This can cause session conflicts and break the bot.

---

## ⚡ Summary

* Clone → Run → Login once → Done
* No manual setup 
* Fully automated course completion

---

## ⚠️ Disclaimer
make sure faculties never get to know about this 
---

just let it run overnight problem solving will be there soon  
