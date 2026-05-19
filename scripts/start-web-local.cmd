@echo off
cd /d E:\CheersAI-Desktop\web
echo [%date% %time%] starting local web > E:\CheersAI-Desktop\logs\web-local-cmd.log
call C:\Users\33814\AppData\Roaming\npm\pnpm.cmd dev -H 0.0.0.0 -p 3000 >> E:\CheersAI-Desktop\logs\web-local-cmd.log 2>&1
echo [%date% %time%] exited with %errorlevel% >> E:\CheersAI-Desktop\logs\web-local-cmd.log
pause
