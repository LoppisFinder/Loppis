@echo off
REM Run LoppisFinder crawlers and ingest into PostgreSQL
cd /d "%~dp0\.."
call ..\api\.venv\Scripts\activate.bat
set DATABASE_URL=postgresql+asyncpg://loppis:loppis@localhost:5432/loppisfinder
cd crawler
python -m crawler.runner
pause
