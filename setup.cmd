@echo off
REM Quick start script for the Car Rental API - Windows version

echo ========================================
echo    Car Rental API - Setup Script
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [92m Criando ambiente virtual...[0m
    python -m venv venv
    if errorlevel 1 (
        echo [91mErro ao criar ambiente virtual. Verifique se Python esta instalado.[0m
        pause
        exit /b 1
    )
)

echo [92m Ativando ambiente virtual...[0m
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [91mErro ao ativar ambiente virtual.[0m
    pause
    exit /b 1
)

echo [92m Instalando dependencias...[0m
pip install -r requirements.txt
if errorlevel 1 (
    echo [91mErro ao instalar dependencias.[0m
    pause
    exit /b 1
)

echo [92m Executando migrations...[0m
python manage.py migrate
if errorlevel 1 (
    echo [91mErro ao executar migrations.[0m
    pause
    exit /b 1
)

echo [92m Carregando dados de exemplo...[0m
python manage.py shell < init_data.py
if errorlevel 1 (
    echo [91mErro ao carregar dados de exemplo.[0m
    pause
    exit /b 1
)

echo.
echo [92m Setup completo![0m
echo.
echo Para iniciar o servidor, execute:
echo   python manage.py runserver
echo.
echo Para executar testes:
echo   python manage.py test rentals
echo   # ou
echo   pytest
echo.
echo API estara disponivel em: http://localhost:8000/api/
echo Admin panel em: http://localhost:8000/admin/
echo.

pause

