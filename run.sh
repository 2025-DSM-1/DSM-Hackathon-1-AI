#!/bin/bash

# 실행 권한 자동 부여 (외부 환경 대응)
chmod +x "$0"

export PATH=$PATH:/opt/render/.local/bin

# 패키지 설치
pip3 install --upgrade pip
pip3 install -r requirements.txt

# 서버 실행
uvicorn main:app --host 0.0.0.0 --port 8000
