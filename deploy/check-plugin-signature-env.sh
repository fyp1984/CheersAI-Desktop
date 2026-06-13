#!/usr/bin/env sh
set -eu

SERVICE_NAME="${1:-}"
PID="${2:-}"

print_value() {
  key="$1"
  value="${2:-}"
  if [ -z "$value" ]; then
    echo "  $key=<missing>"
  else
    echo "  $key=$value"
  fi
}

if [ -n "$SERVICE_NAME" ] && command -v systemctl >/dev/null 2>&1; then
  PID="$(systemctl show "$SERVICE_NAME" --property MainPID --value 2>/dev/null || true)"
fi

if [ -z "$PID" ] || [ "$PID" = "0" ]; then
  echo "Usage:"
  echo "  $0 <plugin-daemon-systemd-service>"
  echo "  $0 '' <plugin-daemon-pid>"
  echo
  echo "ERROR: plugin-daemon process was not found." >&2
  exit 1
fi

ENV_PATH="/proc/$PID/environ"
if [ ! -r "$ENV_PATH" ]; then
  echo "ERROR: cannot read $ENV_PATH. Try running with sudo." >&2
  exit 1
fi

TMP_ENV="$(mktemp)"
trap 'rm -f "$TMP_ENV"' EXIT
tr '\0' '\n' < "$ENV_PATH" > "$TMP_ENV"

get_env() {
  grep "^$1=" "$TMP_ENV" | sed "s/^$1=//" | tail -n 1
}

ENABLED="$(get_env THIRD_PARTY_SIGNATURE_VERIFICATION_ENABLED || true)"
PUBLIC_KEYS="$(get_env THIRD_PARTY_SIGNATURE_VERIFICATION_PUBLIC_KEYS || true)"
FORCE_VERIFYING="$(get_env FORCE_VERIFYING_SIGNATURE || true)"
ENFORCE_LANGGENIUS="$(get_env ENFORCE_LANGGENIUS_PLUGIN_SIGNATURES || true)"

echo "plugin-daemon PID: $PID"
echo "Signature environment:"
print_value THIRD_PARTY_SIGNATURE_VERIFICATION_ENABLED "$ENABLED"
print_value THIRD_PARTY_SIGNATURE_VERIFICATION_PUBLIC_KEYS "$PUBLIC_KEYS"
print_value FORCE_VERIFYING_SIGNATURE "$FORCE_VERIFYING"
print_value ENFORCE_LANGGENIUS_PLUGIN_SIGNATURES "$ENFORCE_LANGGENIUS"

if [ "$ENABLED" != "true" ]; then
  echo "ERROR: third-party signature verification is not enabled in the running plugin-daemon process." >&2
  exit 2
fi

if [ "$FORCE_VERIFYING" != "true" ]; then
  echo "ERROR: FORCE_VERIFYING_SIGNATURE is not true in the running plugin-daemon process." >&2
  exit 3
fi

if [ -z "$PUBLIC_KEYS" ]; then
  echo "ERROR: public key path is missing." >&2
  exit 4
fi

OLD_IFS="$IFS"
IFS=","
for key in $PUBLIC_KEYS; do
  if [ ! -f "$key" ]; then
    echo "ERROR: configured public key does not exist: $key" >&2
    exit 5
  fi
  if command -v openssl >/dev/null 2>&1; then
    openssl pkey -pubin -in "$key" -noout >/dev/null 2>&1 || {
      echo "ERROR: invalid public key PEM: $key" >&2
      exit 6
    }
  fi
done
IFS="$OLD_IFS"

echo "OK: plugin-daemon is running with plugin signature verification configured."
