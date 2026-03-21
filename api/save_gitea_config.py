"""Save Gitea configuration to .env file."""
import os

# Gitea configuration from Web UI
GITEA_CONFIG = {
    'GITEA_URL': 'http://localhost:8080',
    'GITEA_OWNER': 'root',
    'GITEA_REPO': 'cheersAI',
    'GITEA_TOKEN': '75f275e486de374ed6c6b8696ea69cf25d86d21f',
}

env_file = '.env'

print("Saving Gitea configuration to .env file...")
print("=" * 50)

# Read existing .env file
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
else:
    lines = []

# Remove existing Gitea configuration
new_lines = []
skip_next = False
for line in lines:
    if line.strip().startswith('# Gitea Configuration'):
        skip_next = True
        continue
    if skip_next and line.strip().startswith('GITEA_'):
        continue
    skip_next = False
    new_lines.append(line)

# Add new Gitea configuration
if new_lines and not new_lines[-1].endswith('\n'):
    new_lines.append('\n')

new_lines.append('\n# Gitea Configuration\n')
for key, value in GITEA_CONFIG.items():
    new_lines.append(f'{key}={value}\n')

# Write back to .env file
with open(env_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✓ Gitea configuration saved to .env file")
print("\nConfiguration:")
for key, value in GITEA_CONFIG.items():
    if key == 'GITEA_TOKEN':
        print(f"  {key}={'*' * 10}...{value[-4:]}")
    else:
        print(f"  {key}={value}")

print("\n" + "=" * 50)
print("Next steps:")
print("1. Restart the backend service (Ctrl+C and restart)")
print("2. Run: python test_gitea_direct.py")
print("3. Refresh browser and test file picker")
