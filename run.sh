#!/bin/bash

# 기존 가상환경 및 패키지 삭제 (Render 환경에서 강제 초기화)
rm -rf .venv
pip uninstall -y pydantic fastapi

# 필요한 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt

# 서버 실행
uvicorn main:app --host 0.0.0.0 --port 8000