@echo off
set PATH=%PATH%;C:\Users\33814\AppData\Roaming\Python\Python313\Scripts
set NUMEXPR_MAX_THREADS=1
cd /d E:\CheersAI-Desktop\api
echo Starting backend API...
uv run flask run --host 0.0.0.0 --port=5001 --no-reload
pause
