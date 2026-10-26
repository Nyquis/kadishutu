@echo off
where pixi >nul 2>nul
if errorlevel 1 (
    echo pixi is required. Install it from https://pixi.sh
    exit /b 1
)
pixi install
