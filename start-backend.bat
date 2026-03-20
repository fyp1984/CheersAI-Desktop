@echo off
set PATH=%PATH%;C:\Users\33814\AppData\Roaming\Python\Python313\Scripts
cd /d E:\CheersAI-Desktop\api
uv run flask run --host 0.0.0.0 --port=5001 --debug
pause
