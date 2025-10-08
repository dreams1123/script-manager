@echo off
echo Starting Script1 - Audience Conversation Processor...
echo.
echo This script will monitor MongoDB for pending conversations
echo and generate summaries, keywords, and phrases using LLM.
echo.
echo Make sure LM Studio is running with the model: itlwas/hermes-3-llama-3.1-8b
echo.
pause

cd /d "%~dp0"
python script1.py

pause
