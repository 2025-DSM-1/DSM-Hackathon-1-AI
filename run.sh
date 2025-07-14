#!/bin/bash

# 패키지 설치
pip3 install --upgrade pip
pip3 install -r requirements.txt

# 서버 실행
uvicorn main:app --host 0.0.0.0 --port 8000