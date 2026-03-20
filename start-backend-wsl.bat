@echo off
chcp 65001 >nul
echo === Installing uv in WSL ===
wsl -d Ubuntu -e /bin/bash -c "export PATH=$HOME/.local/bin:$HOME/.cargo/bin:$PATH && if ! command -v uv &>/dev/null; then echo 'Installing uv...' && curl -LsSf https://astral.sh/uv/install.sh | sh; fi && uv --version"
echo.
echo === Installing Python dependencies ===
wsl -d Ubuntu -e /bin/bash -c "export PATH=$HOME/.local/bin:$HOME/.cargo/bin:$PATH && cd /mnt/e/CheersAI-Desktop/api && uv sync --python 3.12 2>&1 | tail -5"
echo.
echo === Running database migration ===
wsl -d Ubuntu -e /bin/bash -c "export PATH=$HOME/.local/bin:$HOME/.cargo/bin:$PATH && cd /mnt/e/CheersAI-Desktop/api && uv run flask db upgrade 2>&1"
echo.
echo === Starting Backend API ===
wsl -d Ubuntu -e /bin/bash -c "export PATH=$HOME/.local/bin:$HOME/.cargo/bin:$PATH && cd /mnt/e/CheersAI-Desktop/api && uv run flask run --host 0.0.0.0 --port=5001 --no-reload"
pause
