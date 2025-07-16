from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv
import re

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
model = genai.GenerativeModel("gemini-2.0-flash")


# 데이터 모델 정의
class BillRequest(BaseModel):
    lawModifiedContent: str


class BillResponseElement(BaseModel):
    summaryElement: str


class BillResponse(BaseModel):
    lawContent: str = Field(..., description="법안 한줄 요약")
    lawSummaryContent: list[BillResponseElement]
    backgroundInfo: str = Field(..., description="법안 배경 정보")
    example: str = Field(..., description="법안 예시")
    agreeLogic: str = Field(..., description="법안에 대한 찬성 논리")
    disagreeLogic: str = Field(..., description="법안에 대한 반대 논리")


def clean_markdown(text):
    # 마크다운 기호 제거
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # **굵은 글씨** 제거
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # *기울임체* 제거
    text = re.sub(r"#+\s", "", text)  # # 제목 제거
    text = re.sub(r"`(.*?)`", r"\1", text)  # `코드` 제거
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)  # [링크](url) 제거
    text = re.sub(r"---", "", text)  # 구분선 제거
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)  # 코드 블록 제거

    # 글머리 기호 제거 및 정리
    text = re.sub(
        r"^\s*[\*\-•]\s+", "", text, flags=re.MULTILINE
    )  # 줄 시작의 글머리 기호 제거
    text = re.sub(
        r"\n\s*[\*\-•]\s+", "\n", text
    )  # 줄 중간의 글머리 기호를 줄바꿈으로 변경

    # 빈 줄 정리
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)  # 3개 이상 연속된 줄바꿈을 2개로 정리

    return text.strip()


@app.post("/law/summary", response_model=BillResponse)
async def law(request: BillRequest):
    try:
        req = request.lawModifiedContent

        logger.info(f"법안 분석 요청: {req}")

        summaryPrompt1 = f"""
        다음 법안에 대해 간결하고 명확하게 요약해주세요:

        법안 제목: {req}

        요약 시 다음 사항을 포함해주세요:
        1. 법안의 주요 목적
        2. 핵심 내용
        3. 예상되는 영향
        4. 주요 변경사항

        간결하고 이해하기 쉽게 100자 이내로 3문장으로 작성해주세요.
        """

        summaryPrompt2 = f"""
        {summaryPrompt1}을 한문장으로 요약한 내용을 작성해주세요.
        """

        backgroundPrompt = f"""
        다음 법안에 대한 배경 정보를 230자 이내로 제공해주세요:
        법안 제목: {req}
        배경 정보는 법안이 제정된 이유, 관련된 사회적 이슈, 역사적 맥락 등을 포함해야 합니다.
        가능한 한 구체적이고 상세하게 작성해주세요.
        """

        examplePrompt = f"""
        다음 법안에 대한 사례를 제공해주세요:

        법안 제목: {req}
        예시는 법안의 적용 사례나 유사한 법안의 사례를 포함해야 합니다.
        가능한 한 구체적이고 실제적인 한가지의 예시를 작성해주세요.
        반드시 한가지여야합니다.
        """

        agreeLogicPrompt = f"""
        다음 법안에 대한 찬성 논리를 100자 작성해주세요:
        법안 제목: {req}
        찬성 논리는 법안의 장점, 사회적 필요성, 예상되는 긍정적 영향 등을 포함해야 합니다.
        가능한 한 설득력 있고 논리적으로 작성해주세요.
        """

        disagreeLogicPrompt = f"""
        다음 법안에 대한 반대 논리를 100자 이내로 작성해주세요:
        법안 제목: {req}
        반대 논리는 법안의 단점, 사회적 우려, 예상되는 부정적 영향 등을 포함해야 합니다.
        가능한 한 설득력 있고 논리적으로 작성해주세요.
        """

        summaryResponse1 = model.generate_content(clean_markdown(summaryPrompt1))
        summaryResponse2 = model.generate_content(clean_markdown(summaryPrompt2))
        backgroundResponse = model.generate_content(clean_markdown(backgroundPrompt))
        exampleResponse = model.generate_content(clean_markdown(examplePrompt))
        agreeLogicResponse = model.generate_content(clean_markdown(agreeLogicPrompt))
        disagreeLogicResponse = model.generate_content(
            clean_markdown(disagreeLogicPrompt)
        )

        if not summaryResponse1.text:
            raise HTTPException(status_code=500, detail="AI 응답이 비어있습니다.")

        logger.info("법안 분석 완료")
        # 문장 분리 및 BillResponseElement 리스트 생성
        summary_elements = [
            BillResponseElement(summaryElement=s.strip())
            for s in summaryResponse2.text.split(".")
            if s.strip()
        ]
        return BillResponse(
            lawContent=summaryResponse1.text,
            lawSummaryContent=summary_elements,
            backgroundInfo=backgroundResponse.text,
            example=exampleResponse.text,
            agreeLogic=agreeLogicResponse.text,
            disagreeLogic=disagreeLogicResponse.text,
        )

    except Exception as e:
        logger.error(f"법안 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="법안 분석 중 오류가 발생했습니다.")


@app.get("/")
async def root():
    return {
        "message": "법안 요약 AI 서버가 실행 중입니다.",
    }
