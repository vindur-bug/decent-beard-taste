from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import base64
import httpx

from analysis.face_shape import analyze_face_shape
from analysis.beard_analysis import analyze_beard
from analysis.recommendation import recommend_styles

load_dotenv()
YOUCAM_API_KEY = os.getenv("YOUCAM_API_KEY")
print("YouCam Key:", "已加载" if YOUCAM_API_KEY else "未加载")
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 请求体模型 ====================

class AnalyzeRequest(BaseModel):
    image: str

class TryOnRequest(BaseModel):
    image: str
    templateId: str


# ==================== 健康检查 ====================

@app.get("/")
def read_root():
    return {"message": "API is running"}



@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    # 成员2现在直接接受 URL、base64、bytes
    # 不需要我们手动解码
    face_result = analyze_face_shape(request.image)
    face_shape = face_result["faceShape"]
    hairline = face_result["hairline"]
    landmarks = face_result["landmarks"]

    # 成员3的 analyze_beard 只需要 landmarks
    # image_bytes 传空 bytes 即可（它内部没用到这个参数）
    beard_result = analyze_beard(b"", landmarks)

    # 推荐
    rec_result = recommend_styles(face_shape, beard_result["densityLevel"])

    return {
        "faceShape": face_shape,
        "beardRegions": beard_result["beardRegions"],
        "densityLevel": beard_result["densityLevel"],
        "heatmapData": beard_result["heatmapData"],
        "recommendedStyles": rec_result["recommendedStyles"],
        "productTips": rec_result["productTips"],
        "hairRecommendations": rec_result["hairRecommendations"],
        "hairTips": rec_result["hairTips"]
    }


@app.post("/api/beard-try-on")
async def beard_try_on(request: TryOnRequest):
    if not YOUCAM_API_KEY:
        return {"task_id": "mock_task_12345"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://yce-api-01.makeupar.com/s2s/v2.0/task/beard-style",
            headers={"Authorization": f"Bearer {YOUCAM_API_KEY}"},
            json={
                "src_file_url": request.image,
                "template_id": request.templateId
            }
        )

        # ===== 关键：把 YouCam 的原始响应打印出来 =====
        print("=== YouCam 响应 ===")
        print("状态码:", response.status_code)
        print("内容:", response.text)
        print("===================")

        data = response.json()

        # 如果返回格式不对，直接把原始响应返回，不要崩
        if "data" not in data:
            return {
                "error": "YouCam API 返回异常",
                "status_code": response.status_code,
                "raw": data
            }

        return {"task_id": data["data"]["task_id"]}

@app.get("/api/task/{task_id}")
async def get_task(task_id: str):
    # 1. 清洗 task_id，防止复制时带入空格或换行符
    task_id = task_id.strip()

    if not YOUCAM_API_KEY or task_id.startswith("mock"):
        return {"status": "success", "url": "https://example.com/mock-beard-result.jpg"}

    # 2. 用 try...except 包裹所有网络请求，避免 500 崩溃
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://yce-api-01.makeupar.com/s2s/v2.0/task/beard-style/{task_id}",
                headers={"Authorization": f"Bearer {YOUCAM_API_KEY}"}
            )
            
            data = response.json()
            
            # 打印真实返回，方便调试
            print("=== 轮询 YouCam 响应 ===")
            print("状态码:", response.status_code)
            print("内容:", data)
            print("========================")

                    # 安全解析
        if "data" not in data:
            return {"status": "unknown", "raw": data}

        task_status = data["data"].get("task_status", "unknown")
        
        if task_status == "success":
            # 正确提取 url 的路径：data -> results -> url
            results = data["data"].get("results", {})
            result_url = results.get("url", "")
            return {"status": "success", "url": result_url}
        
        return {"status": task_status}

    except Exception as e:
        # 4. 捕获所有异常并返回给前端，不再抛出 500
        print("=== 轮询请求失败 ===")
        print("错误类型:", type(e).__name__)
        print("错误信息:", str(e))
        print("====================")
        return {"error": "请求YouCam失败", "type": type(e).__name__, "message": str(e)}
