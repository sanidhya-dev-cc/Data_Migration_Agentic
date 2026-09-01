@echo off
REM Oracle Migration POC - Setup Script for Windows
REM This script sets up the development environment

echo ==========================================
echo Oracle Migration POC - Setup
echo ==========================================
echo.

REM Check if .env exists
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo [32m✓[0m .env file created
    echo.
    echo [33m⚠️  IMPORTANT: Please edit .env and add your Azure OpenAI credentials[0m
    echo.
) else (
    echo [32m✓[0m .env file already exists
    echo.
)

REM Check Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [31m❌ Docker is not installed. Please install Docker first.[0m
    echo    Visit: https://docs.docker.com/get-docker/
    exit /b 1
)

where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo [31m❌ Docker Compose is not installed. Please install Docker Compose first.[0m
    echo    Visit: https://docs.docker.com/compose/install/
    exit /b 1
)

echo [32m✓[0m Docker and Docker Compose are installed
echo.

REM Create logs directory
echo Creating logs directory...
if not exist logs mkdir logs
echo [32m✓[0m Logs directory created
echo.

REM Build and start containers
echo Building Docker containers...
docker-compose build

echo.
echo Starting containers...
docker-compose up -d

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Services:
echo   - Frontend: http://localhost:3000
echo   - Backend API: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo.
echo To view logs:
echo   docker-compose logs -f
echo.
echo To stop services:
echo   docker-compose down
echo.
echo [33m⚠️  Don't forget to configure your Azure OpenAI credentials in .env[0m
echo.

pause
