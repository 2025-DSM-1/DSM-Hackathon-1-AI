#!/bin/bash

# 필요한 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt

# 서버 실행
uvicorn main:app --host 0.0.0.0 --port 8000