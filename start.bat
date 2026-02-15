@echo off
echo Starting Finance Bot...
python main.py
if errorlevel 1 (
    echo.
    echo Бот не запущено. Можливо вже працює інший екземпляр.
    echo Зупиніть його (Ctrl+C у іншому вікні) та спробуйте знову.
)
pause

