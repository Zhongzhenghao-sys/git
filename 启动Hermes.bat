@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d D:\hermes_agent
call venv\Scripts\activate.bat
hermes %*
