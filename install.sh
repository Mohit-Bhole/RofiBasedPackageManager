#!/usr/bin/env bash
# install.sh
# ──────────
# Install rofi-package-manager to the system.
# Run as your normal user (sudo is requested only when needed).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$SCRIPT_DIR/rofi_package_manager"
INSTALL_DIR="/usr/local/lib/rofi-package-manager"
BIN_LINK="/usr/local/bin/rofi-package-manager"
CONFIG_DIR="$HOME/.config/rofi-package-manager"

echo "╔══════════════════════════════════════════╗"
echo "║   Rofi Package Manager — Installer       ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── Checks ────────────────────────────────────────────────────
command -v python3 >/dev/null || { echo "ERROR: python3 not found"; exit 1; }
command -v rofi    >/dev/null || { echo "ERROR: rofi not found. Install it first."; exit 1; }

echo "✔ python3 found: $(python3 --version)"
echo "✔ rofi found:    $(rofi -version | head -1)"

# Optional tools (warn, don't fail)
for tool in yay paru flatpak checkupdates pactree expac; do
    if command -v "$tool" &>/dev/null; then
        echo "✔ $tool found"
    else
        echo "  (optional) $tool not found — related features will be disabled"
    fi
done
echo ""

# ── Copy files ────────────────────────────────────────────────
echo "→ Installing to $INSTALL_DIR …"
sudo mkdir -p "$INSTALL_DIR"
sudo cp -r "$PKG_DIR/"* "$INSTALL_DIR/"

# ── Launcher ──────────────────────────────────────────────────
echo "→ Creating launcher at $BIN_LINK …"
sudo chmod +x "$INSTALL_DIR/rofi-package-manager"
sudo ln -sf "$INSTALL_DIR/rofi-package-manager" "$BIN_LINK"

# ── Config directory ──────────────────────────────────────────
echo "→ Creating config directory at $CONFIG_DIR …"
mkdir -p "$CONFIG_DIR"

# Write default config only if it doesn't already exist
if [[ ! -f "$CONFIG_DIR/config.json" ]]; then
    cat > "$CONFIG_DIR/config.json" <<'EOF'
{
  "aur_helper": "yay",
  "show_descriptions": true,
  "confirm_removal": true,
  "confirm_install": true,
  "cache_ttl_seconds": 300,
  "theme": "default",
  "terminal": null
}
EOF
    echo "✔ Default config written to $CONFIG_DIR/config.json"
else
    echo "  Config already exists — skipping (your settings are preserved)"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Installation complete!                 ║"
echo "║                                          ║"
echo "║   Run:  rofi-package-manager             ║"
echo "║   Or add it to your Rofi modi list.      ║"
echo "╚══════════════════════════════════════════╝"
