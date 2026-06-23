#!/usr/bin/env python3
"""
utils/commands.py
─────────────────
Low-level subprocess helpers.

All public functions return (success: bool, output: str).
Never raise exceptions to the caller — errors are surfaced in the output string.
"""

import shutil
import subprocess
import os
from typing import Optional


def run_command(
    cmd: list[str],
    timeout: int = 60,
    env: Optional[dict] = None,
) -> tuple[bool, str]:
    """
    Run a command and return (success, stdout/stderr).

    Args:
        cmd:     Command + arguments as a list, e.g. ["pacman", "-Qq"]
        timeout: Seconds before the process is killed (default 60).
        env:     Optional environment dict to pass to the subprocess.

    Returns:
        (True, stdout)  on returncode == 0
        (False, stderr) on non-zero exit or any exception
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env or os.environ.copy(),
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, (result.stderr.strip() or result.stdout.strip())

    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout}s: {' '.join(cmd)}"
    except PermissionError:
        return False, f"Permission denied: {' '.join(cmd)}"
    except Exception as exc:
        return False, str(exc)


def run_privileged(
    cmd: list[str],
    terminal: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Run a privileged command (needs sudo/root) in a graphical context.

    Strategy:
      1. Try pkexec  (PolicyKit — works in most desktop environments)
      2. Fall back to launching a visible terminal emulator so the user
         can enter their password naturally.

    Args:
        cmd:      Command to run as root, e.g. ["pacman", "-S", "vim"]
        terminal: Override terminal emulator (e.g. "kitty", "alacritty").
                  Auto-detected if None.

    Returns:
        (True, "")        if the process exits successfully
        (False, message)  on failure or if no suitable method is found
    """
    # --- Try pkexec first ---
    if tool_available("pkexec"):
        return run_command(["pkexec"] + cmd, timeout=300)

    # --- Fall back to a terminal emulator ---
    detected_terminal = terminal or _detect_terminal()
    if not detected_terminal:
        return (
            False,
            "No privilege escalation method found.\n"
            "Install pkexec (polkit) or a terminal emulator.",
        )

    shell_cmd = "sudo " + " ".join(cmd)

    try:
        if detected_terminal == "kitty":
            args = ["kitty", "--", "bash", "-c", shell_cmd + "; read -p 'Press Enter to close...'"]
        elif detected_terminal == "alacritty":
            args = ["alacritty", "-e", "bash", "-c", shell_cmd + "; read -p 'Press Enter to close...'"]
        elif detected_terminal == "gnome-terminal":
            args = ["gnome-terminal", "--", "bash", "-c", shell_cmd + "; read -p 'Press Enter to close...'"]
        else:
            args = [detected_terminal, "-e", "bash", "-c", shell_cmd + "; read -p 'Press Enter to close...'"]

        proc = subprocess.run(args, timeout=600)
        return (proc.returncode == 0), ""
    except Exception as exc:
        return False, str(exc)


def run_in_terminal(
    cmd: list[str],
    title: str = "rofi-package-manager",
    terminal: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Run a command that needs interactive terminal I/O (e.g. yay -S which
    asks questions). Opens a visible terminal window.

    Returns immediately after launching; the terminal runs in the foreground
    and the user interacts with it directly.
    """
    detected_terminal = terminal or _detect_terminal()
    if not detected_terminal:
        return False, "No terminal emulator found."

    shell_cmd = " ".join(cmd) + "; echo ''; read -p 'Done. Press Enter to close...'"

    try:
        if detected_terminal == "kitty":
            args = ["kitty", "--title", title, "--", "bash", "-c", shell_cmd]
        elif detected_terminal == "alacritty":
            args = ["alacritty", "--title", title, "-e", "bash", "-c", shell_cmd]
        elif detected_terminal == "gnome-terminal":
            args = ["gnome-terminal", "--title", title, "--", "bash", "-c", shell_cmd]
        else:
            args = [detected_terminal, "-e", "bash", "-c", shell_cmd]

        subprocess.run(args, check=True)
        return True, ""
    except subprocess.CalledProcessError as exc:
        return False, f"Terminal exited with error: {exc}"
    except Exception as exc:
        return False, str(exc)


def tool_available(name: str) -> bool:
    """Return True if `name` is an executable found on PATH."""
    return shutil.which(name) is not None


def get_aur_helper() -> Optional[str]:
    """
    Return the first available AUR helper from the preferred list,
    or None if none are installed.
    """
    for helper in ("yay", "paru", "trizen", "aurman"):
        if tool_available(helper):
            return helper
    return None


# ── Internal helpers ──────────────────────────────────────────────────────────

def _detect_terminal() -> Optional[str]:
    """Return the name of the first terminal emulator found on PATH."""
    for term in ("kitty", "alacritty", "xterm", "gnome-terminal", "konsole", "xfce4-terminal"):
        if tool_available(term):
            return term
    return None
