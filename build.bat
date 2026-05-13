@echo off
echo Iniciando empacotamento do GlassPrinter v1.1.1...

:: Comando para gerar o executável
pyinstaller --noconsole --onefile --name="GlassPrinter_v1.1.1" ^
    --icon="assets/logo.ico" ^
    --add-data "assets;assets" ^
    --add-data "layouts;layouts" ^
    --add-data "core;core" ^
    main.py

echo.
echo Processo concluido! O executavel esta na pasta "dist".
echo Lembre-se de mover o executavel para a pasta onde deseja que ele opere.
pause