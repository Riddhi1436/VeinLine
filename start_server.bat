@echo off
echo ========================================
echo   VeinLine Blood Donation Platform
echo ========================================
echo.
echo Starting Django development server...
echo.
echo Admin Login:
echo   URL: http://127.0.0.1:8000/admin/
echo   Username: admin
echo   Password: admin123
echo.
echo Web UI: http://127.0.0.1:8000/
echo API Docs: http://127.0.0.1:8000/api/
echo.
echo Press Ctrl+C to stop the server
echo.
.\venv\Scripts\python manage.py runserver

