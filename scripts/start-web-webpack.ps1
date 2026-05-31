Set-Location 'E:\CheersAI-Desktop\web'
Add-Content 'E:\CheersAI-Desktop\logs\next-webpack-wrapper.log' "[$(Get-Date -Format s)] starting"
& 'C:\Program Files\nodejs\node.exe' 'node_modules\next\dist\bin\next' dev --webpack -H 0.0.0.0 -p 3000 *> 'E:\CheersAI-Desktop\logs\next-webpack.log'
Add-Content 'E:\CheersAI-Desktop\logs\next-webpack-wrapper.log' "[$(Get-Date -Format s)] exited $LASTEXITCODE"
