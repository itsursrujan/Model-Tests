@echo off
echo Starting DeepStegAI Development Environment...
start cmd /k "python run.py"
start cmd /k "cd frontend && npm run dev"
