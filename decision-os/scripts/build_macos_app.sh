#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DIST_DIR="$ROOT_DIR/artifacts/mac_app"
APP_DIR="$DIST_DIR/Decision OS.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
LAUNCHER_PATH="$MACOS_DIR/decision_os_launcher"
COMMAND_PATH="$DIST_DIR/Launch Decision OS.command"

mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

cat > "$CONTENTS_DIR/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleExecutable</key>
  <string>decision_os_launcher</string>
  <key>CFBundleIdentifier</key>
  <string>com.chihvane.decisionos</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>Decision OS</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0</string>
  <key>CFBundleVersion</key>
  <string>1</string>
  <key>LSMinimumSystemVersion</key>
  <string>12.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
EOF

cat > "$LAUNCHER_PATH" <<EOF
#!/bin/zsh
set -euo pipefail
PROJECT_ROOT="$ROOT_DIR"
exec /usr/bin/env python3 "\$PROJECT_ROOT/scripts/run_local_app.py"
EOF

cat > "$COMMAND_PATH" <<EOF
#!/bin/zsh
set -euo pipefail
PROJECT_ROOT="$ROOT_DIR"
exec /usr/bin/env python3 "\$PROJECT_ROOT/scripts/run_local_app.py"
EOF

chmod +x "$LAUNCHER_PATH" "$COMMAND_PATH"

echo "Built app bundle:"
echo "  $APP_DIR"
echo "Built one-click command launcher:"
echo "  $COMMAND_PATH"
