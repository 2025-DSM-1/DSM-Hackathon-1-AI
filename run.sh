#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}AI 서버 시작 스크립트${NC}"

# 가상환경이 없거나 python/pip이 깨졌으면 재생성
RECREATE_VENV=false
if [ ! -d "venv" ]; then
    RECREATE_VENV=true
else
    if [ ! -x "venv/bin/python" ] || [ ! -x "venv/bin/pip" ]; then
        RECREATE_VENV=true
    fi
fi

if [ "$RECREATE_VENV" = true ]; then
    echo -e "${GREEN}가상환경(venv) 생성/복구 중...${NC}"
    rm -rf venv
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}가상환경 생성 실패! python3가 설치되어 있는지 확인하세요.${NC}"
        exit 1
    fi
fi

# 가상환경 활성화
source venv/bin/activate

# python/pip 경로 명확히 지정
PYTHON=python3
PIP=pip3

# python, pip 정상 동작 확인
$PYTHON --version || { echo -e "${RED}venv/bin/python 실행 실패!${NC}"; exit 1; }
$PIP --version || { echo -e "${RED}venv/bin/pip 실행 실패!${NC}"; exit 1; }

# 필요한 패키지 설치
echo -e "${GREEN}필요한 패키지 설치 중...${NC}"
$PIP install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}패키지 설치 실패! requirements.txt를 확인하세요.${NC}"
    exit 1
fi

# 서버 실행
echo -e "${GREEN}서버 시작 중...${NC}"
uvicorn main:app --reload --host 0.0.0.0 --port 8000