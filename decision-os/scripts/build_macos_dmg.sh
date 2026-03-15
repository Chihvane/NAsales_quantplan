#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DIST_DIR="$ROOT_DIR/artifacts/mac_app"
APP_DIR="$DIST_DIR/Decision OS.app"
DMG_PATH="$DIST_DIR/Decision-OS.dmg"
STAGING_DIR="$DIST_DIR/dmg_staging"

"$ROOT_DIR/scripts/build_macos_app.sh"

rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"
cp -R "$APP_DIR" "$STAGING_DIR/"
ln -s /Applications "$STAGING_DIR/Applications"
rm -f "$DMG_PATH"

hdiutil create -volname "Decision OS" -srcfolder "$STAGING_DIR" -ov -format UDZO "$DMG_PATH" >/dev/null

echo "Built dmg:"
echo "  $DMG_PATH"
