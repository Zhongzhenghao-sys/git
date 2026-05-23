@echo off
chcp 65001 >nul
title Hermes 守护进程（自动重启）
echo ========================================
echo  Hermes 守护进程
echo  此窗口请保持开启，不要关闭！
echo  它会在网关崩溃时自动重启网关。
echo ========================================
echo.
PowerShell -NoProfile -ExecutionPolicy Bypass -File "%~dp0hermes_守护进程.ps1"
echo.
echo 守护进程已退出，按任意键关闭...
pause
