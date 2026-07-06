@echo off
REM backend ディレクトリから実行された場合、プロジェクトルートの起動スクリプトへ転送
cd /d "%~dp0..\scripts"
call start.bat
