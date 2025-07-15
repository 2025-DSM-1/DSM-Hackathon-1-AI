from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# FastAPI 앱 생성
app = FastAPI(title="법안 요약 AI", description="법안 요약 AI", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini API 설정
GOOGLE_API_KEY = os.getenv("API_KEY")
if not GOOGLE_API_KEY:
    logger.error("API_KEY 환경변수가 설정되지 않았습니다.")
    raise ValueError("API_KEY 환경변수를 설정해주세요.")

genai.configure(api_key=GOOGLE_API_KEY)


# 데이터 모델 정의
class BillRequest(BaseModel):
    lawModifeidContent: str


class BillResponse(BaseModel):
    lawSummary: str = Field(..., description="AI가 생성한 법안 요약")
    backgroundInfo: str = Field(..., description="법안 배경 정보")
    example: str = Field(..., description="법안 예시")


@app.post("/law/summary", response_model=BillResponse)
async def law(request: BillRequest):
    try:
        logger.info(f"법안 분석 요청: {request.lawModifeidContent}")

        summaryPrompt = f"""
        다음 법안에 대해 간결하고 명확하게 요약해주세요:

        법안 제목: {request.lawModifeidContent}

        요약 시 다음 사항을 포함해주세요:
        1. 법안의 주요 목적
        2. 핵심 내용
        3. 예상되는 영향
        4. 주요 변경사항

        간결하고 이해하기 쉽게 3줄 이내로 작성해주세요.
        """

        backgroundPrompt = f"""
        다음 법안에 대한 배경 정보를 제공해주세요:
        법안 제목: {request.lawModifeidContent}
        배경 정보는 법안이 제정된 이유, 관련된 사회적 이슈, 역사적 맥락 등을 포함해야 합니다.
        가능한 한 구체적이고 상세하게 작성해주세요.
        """

        examplePrompt = f"""
        다음 법안에 대한 예시를 제공해주세요:

        법안 제목: {request.lawModifeidContent}
        예시는 법안의 적용 사례나 유사한 법안의 사례를 포함해야 합니다.
        가능한 한 구체적이고 실제적인 한가지의 예시를 작성해주세요.
        반드시 한가지여야합니다.
        """

        essentialPrompt = "*, **, #, ##과 같은 마크다운은 반드시 사용하지마세요."
        model = genai.GenerativeModel("gemini-2.0-flash")

        summaryResponse = model.generate_content(essentialPrompt + summaryPrompt)
        backgroundResponse = model.generate_content(essentialPrompt + backgroundPrompt)
        exampleResponse = model.generate_content(essentialPrompt + examplePrompt)

        if not summaryResponse.text:
            raise HTTPException(status_code=500, detail="AI 응답이 비어있습니다.")

        logger.info("법안 분석 완료")
        return BillResponse(
            lawSummary=summaryResponse.text,
            backgroundInfo=backgroundResponse.text,
            example=exampleResponse.text,
        )

    except Exception as e:
        logger.error(f"법안 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="법안 분석 중 오류가 발생했습니다.")


@app.get("/")
async def root():
    return {
        "message": "법안 요약 AI 서버가 실행 중입니다.",
    }
