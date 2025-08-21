@echo off
echo ========================================
echo    Post Service 실행 스크립트
echo ========================================
echo.

echo 1. 도커 설치 확인 중...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] 도커가 설치되지 않았습니다.
    echo Docker Desktop을 먼저 설치해주세요: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
echo [성공] 도커가 설치되어 있습니다.
echo.

echo 2. Post Service 이미지 로드 중...
docker load -i post-service-image.tar
if %errorlevel% neq 0 (
    echo [오류] 이미지 로드에 실패했습니다.
    pause
    exit /b 1
)
echo [성공] 이미지가 로드되었습니다.
echo.

echo 3. 기존 컨테이너 정리 중...
docker stop post-service-app 2>nul
docker rm post-service-app 2>nul
echo [완료] 기존 컨테이너 정리 완료.
echo.

echo 4. Post Service 컨테이너 시작 중...
docker run -d --name post-service-app -p 5000:5000 post-service--app:latest
if %errorlevel% neq 0 (
    echo [오류] 컨테이너 시작에 실패했습니다.
    pause
    exit /b 1
)
echo [성공] Post Service가 시작되었습니다!
echo.

echo 5. 서비스 상태 확인 중...
timeout /t 3 /nobreak >nul
docker ps --filter name=post-service-app

echo.
echo ========================================
echo    🎉 Post Service 실행 완료!
echo ========================================
echo.
echo 🌐 웹페이지: http://localhost:5000
echo 📝 글쓰기: http://localhost:5000/write
echo 🔍 API 문서: http://localhost:5000/api/docs
echo.
echo 💡 서비스 중지: docker stop post-service-app
echo 💡 서비스 시작: docker start post-service-app
echo 💡 서비스 제거: docker rm post-service-app
echo.
pause
