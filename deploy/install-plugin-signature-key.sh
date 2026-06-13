#!/usr/bin/env sh
set -eu

PUBLIC_KEY_SOURCE="${1:-deploy/plugin-signature-keys/cheersai-plugin-signing.public.pem}"
TARGET_DIR="${PLUGIN_SIGNATURE_KEY_DIR:-/etc/dify/plugin-signatures}"
TARGET_KEY="${TARGET_DIR}/cheersai-plugin-signing.public.pem"
ENV_FILE="${PLUGIN_SIGNATURE_ENV_FILE:-/etc/dify/plugin-signature.env}"

if [ ! -f "$PUBLIC_KEY_SOURCE" ]; then
  echo "ERROR: public key not found: $PUBLIC_KEY_SOURCE" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"
install -m 0644 "$PUBLIC_KEY_SOURCE" "$TARGET_KEY"

cat > "$ENV_FILE" <<EOF
THIRD_PARTY_SIGNATURE_VERIFICATION_ENABLED=true
THIRD_PARTY_SIGNATURE_VERIFICATION_PUBLIC_KEYS=$TARGET_KEY
FORCE_VERIFYING_SIGNATURE=true
ENFORCE_LANGGENIUS_PLUGIN_SIGNATURES=false
EOF

echo "Installed plugin signature public key:"
echo "  $TARGET_KEY"
echo "Generated plugin-daemon env file:"
echo "  $ENV_FILE"

if command -v openssl >/dev/null 2>&1; then
  echo "Public key fingerprint:"
  openssl pkey -pubin -in "$TARGET_KEY" -outform DER 2>/dev/null | openssl dgst -sha256
else
  echo "openssl not found; skipped public key fingerprint check."
fi

echo
echo "Next step: load $ENV_FILE in the plugin-daemon service and restart plugin-daemon."
echo "Do not only add these variables to API/web; signature verification runs in plugin-daemon."
