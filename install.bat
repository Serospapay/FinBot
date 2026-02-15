@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
if not exist .env (
    echo Creating .env from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env and add your BOT_TOKEN from BotFather!
) else (
    echo .env already exists.
)
echo.
echo Installation complete!
pause

