@echo off
echo Starting Dodge AI System...
start cmd /k "cd backend && python main.py"
start cmd /k "cd frontend && npm run dev"
echo Backend running at http://localhost:8000
echo Frontend running at http://localhost:5173
pause
