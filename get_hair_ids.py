import httpx
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUCAM_API_KEY")

url = "https://yce-api-01.makeupar.com/s2s/v2.1/task/template/hair-transfer?page_size=20"
headers = {"Authorization": f"Bearer {API_KEY}"}

response = httpx.get(url, headers=headers)
data = response.json()

print("=== 请把下面的 JSON 复制下来 ===")
for item in data.get("data", {}).get("templates", []):
    if item["id"].startswith("male_"):
        # 打印出 id、名称和缩略图链接
        print(f'{{"id": "{item["id"]}", "name": "{item["id"]}", "image": "{item.get("thumb", "")}"}},')