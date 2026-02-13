@echo off
REM Docker Deploy Script for CodeCraftIDE-4gl (Windows)
REM This script builds, tags, and pushes images to Docker registry

REM Configuration
IF "%DOCKER_REGISTRY_USER%"=="" (
    SET DOCKER_REGISTRY_USER=your-dockerhub-username
    echo WARNING: DOCKER_REGISTRY_USER not set, using default: %DOCKER_REGISTRY_USER%
    echo Please set it with: set DOCKER_REGISTRY_USER=your-username
    echo.
    pause
)

SET IMAGE_PREFIX=%DOCKER_REGISTRY_USER%/codecraftide-4gl
IF "%1"=="" (
    SET VERSION=latest
) ELSE (
    SET VERSION=%1
)

echo ==========================================
echo CodeCraftIDE-4gl Docker Deploy Script
echo ==========================================
echo Registry: %DOCKER_REGISTRY_USER%
echo Version: %VERSION%
echo.

REM Build backend image
echo Building backend image...
docker build -t %IMAGE_PREFIX%-backend:%VERSION% -f Dockerfile .
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build backend image
    pause
    exit /b 1
)
echo [OK] Backend image built
echo.

REM Tag as latest if version is specified
IF NOT "%VERSION%"=="latest" (
    docker tag %IMAGE_PREFIX%-backend:%VERSION% %IMAGE_PREFIX%-backend:latest
)

REM Build studio image
echo Building studio image...
docker build -t %IMAGE_PREFIX%-studio:%VERSION% -f studio/Dockerfile ./studio
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build studio image
    pause
    exit /b 1
)
echo [OK] Studio image built
echo.

REM Tag as latest if version is specified
IF NOT "%VERSION%"=="latest" (
    docker tag %IMAGE_PREFIX%-studio:%VERSION% %IMAGE_PREFIX%-studio:latest
)

REM Push images to registry
echo.
echo Pushing images to Docker registry...
echo.

echo Pushing backend image ^(%VERSION%^)...
docker push %IMAGE_PREFIX%-backend:%VERSION%
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to push backend image
    pause
    exit /b 1
)

IF NOT "%VERSION%"=="latest" (
    echo Pushing backend image ^(latest^)...
    docker push %IMAGE_PREFIX%-backend:latest
)

echo.
echo Pushing studio image ^(%VERSION%^)...
docker push %IMAGE_PREFIX%-studio:%VERSION%
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to push studio image
    pause
    exit /b 1
)

IF NOT "%VERSION%"=="latest" (
    echo Pushing studio image ^(latest^)...
    docker push %IMAGE_PREFIX%-studio:latest
)

echo.
echo ==========================================
echo [OK] All images pushed successfully!
echo ==========================================
echo.
echo Images pushed:
echo   - %IMAGE_PREFIX%-backend:%VERSION%
echo   - %IMAGE_PREFIX%-studio:%VERSION%
IF NOT "%VERSION%"=="latest" (
    echo   - %IMAGE_PREFIX%-backend:latest
    echo   - %IMAGE_PREFIX%-studio:latest
)
echo.
echo To deploy on another server:
echo   1. Copy docker-compose.production.yml to the server
echo   2. Set DOCKER_REGISTRY_USER environment variable
echo   3. Run: docker-compose -f docker-compose.production.yml pull
echo   4. Run: docker-compose -f docker-compose.production.yml up -d
echo.
pause
