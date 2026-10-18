from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import base64
import httpx
import io

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
                "src_file_id": request.image, # 👈 这里改成 src_file_id
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
    
class UploadRequest(BaseModel):
    image: str  # 前端传来的 base64

@app.post("/api/upload")
async def upload_image(request: UploadRequest):
    try:
        # 1. 清理数据：去掉所有空格、换行符，并剥离前缀
        image_b64 = request.image
        if "," in image_b64:
            image_b64 = image_b64.split(",")[-1]
        
        # 👇 加上这行，把 \n \r 和空格全部替换为空
        image_b64 = image_b64.replace("\n", "").replace("\r", "").replace(" ", "")
        
        # 2. 解码
        image_bytes = base64.b64decode(image_b64)

        file_size = len(image_bytes)
        # ... 后面保持不变 ...

        async with httpx.AsyncClient(timeout=30.0) as client:
            # 2. 第一步：申请上传许可（将元数据包在 files 数组中）
            meta_res = await client.post(
                "https://yce-api-01.makeupar.com/s2s/v2.0/file",
                headers={
                    "Authorization": f"Bearer {YOUCAM_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "files": [  # 👈 关键修改：用 files 数组包裹
                        {
                            "content_type": "image/jpeg",
                            "file_name": "photo.jpg",
                            "file_size": file_size
                        }
                    ]
                }
            )
            meta_data = meta_res.json()
            
                        # 3. 解析返回的 file_id 和预签名上传 URL
            # 注意：files 在 data 里面
            if "data" not in meta_data or "files" not in meta_data["data"] or len(meta_data["data"]["files"]) == 0:
                return {"error": "获取上传地址失败", "raw": meta_data}

            file_info = meta_data["data"]["files"][0]
            file_id = file_info["file_id"]
            upload_request = file_info["requests"][0]  # 取出 PUT 请求的信息

            # 4. 第二步：用 PUT 方法将文件二进制上传到预签名 URL
            upload_res = await client.put(
                upload_request["url"],
                headers=upload_request.get("headers", {}),
                content=image_bytes
            )

            if upload_res.status_code == 200:
                return {
                    "file_id": file_id, 
                    "url": upload_request["url"]  # 这个 URL 可用于后续 AI 任务
                }
            else:
                return {"error": "文件上传到S3失败", "status": upload_res.status_code}

    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

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
                results = data["data"].get("results", {})
                result_url = results.get("url", "")
                return {"status": "success", "url": result_url}
            
            # 👇 改动在这里：如果失败，把完整的 data 返回给前端看
        if task_status == "error":
                return {"status": "error", "raw": data}

        return {"status": task_status}

    except Exception as e:
        # 4. 捕获所有异常并返回给前端，不再抛出 500
        print("=== 轮询请求失败 ===")
        print("错误类型:", type(e).__name__)
        print("错误信息:", str(e))
        print("====================")
        return {"error": "请求YouCam失败", "type": type(e).__name__, "message": str(e)}

class HairTryOnRequest(BaseModel):
    image: str       # 传入 file_id
    templateId: str  # 传入 hairTemplateId

@app.post("/api/hair-try-on")
async def hair_try_on(request: HairTryOnRequest):
    if not YOUCAM_API_KEY:
        return {"task_id": "mock_hair_task_12345"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 注意这里是 v2.1 的发型接口
        response = await client.post(
            "https://yce-api-01.makeupar.com/s2s/v2.1/task/hair-transfer",
            headers={"Authorization": f"Bearer {YOUCAM_API_KEY}"},
            json={
                "src_file_id": request.image,
                "template_id": request.templateId,
                "hair_color": "src" # 保留用户原发色
            }
        )
        data = response.json()
        
        if "data" not in data or "task_id" not in data.get("data", {}):
            return {"error": "YouCam 发型生成任务提交失败", "raw": data}
            
        return {"task_id": data["data"]["task_id"]}
