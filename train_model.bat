@echo off
setlocal enabledelayedexpansion

echo ==================================================
echo   Smarty-Reco Food-101 Classifier Training Helper
echo ==================================================
echo.

REM Ensure backend\data exists
if not exist "backend\data" (
    echo Creating backend\data directory...
    mkdir "backend\data"
)

REM Move food-101.tar.gz if it is in the root directory
if exist "food-101.tar.gz" (
    echo Found food-101.tar.gz in workspace root.
    echo Moving food-101.tar.gz to backend\data\...
    
    REM Remove the potentially corrupt/partial download if present
    if exist "backend\data\food-101.tar.gz" (
        del /f /q "backend\data\food-101.tar.gz"
    )
    
    move "food-101.tar.gz" "backend\data\"
    if errorlevel 1 (
        echo Error: Failed to move food-101.tar.gz to backend\data\
        pause
        exit /b 1
    )
    echo Dataset moved successfully.
) else (
    if exist "backend\data\food-101.tar.gz" (
        echo food-101.tar.gz is already in backend\data\.
    ) else (
        echo Warning: food-101.tar.gz was not found in the root directory or backend\data\.
        echo The PyTorch training script will attempt to download it automatically.
    )
)

echo.
echo Activating virtual environment...
if exist "backend\venv\Scripts\activate.bat" (
    call backend\venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment at backend\venv not found. Using system python.
)

echo.
echo Starting ResNet18 Food-101 training...
python backend\scripts\train_food101.py --epochs 12

if errorlevel 1 (
    echo.
    echo Training failed. Please check the logs.
) else (
    echo.
    echo Training complete! Weights saved to backend\weights\resnet18_food101.pth
)

pause
