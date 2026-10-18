import httpx
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUCAM_API_KEY")

url = "https://yce-api-01.makeupar.com/s2s/v2.1/task/template/hair-transfer?page_size=20"
headers = {"Authorization": f"Bearer {API_KEY}"}

all_male_styles = []
next_token = None

print("正在翻页获取所有男士发型...\n")

while True:
    # 拼接下一页的 token
    req_url = url if not next_token else f"{url}&starting_token={next_token}"
    response = httpx.get(req_url, headers=headers)
    
    if response.status_code != 200:
        print("获取失败:", response.text)
        break
        
    data = response.json().get("data", {})
    templates = data.get("templates", [])
    
    for item in templates:
        if item["id"].startswith("male_"):
            all_male_styles.append(item["id"])
            
    next_token = data.get("next_token")
    if not next_token:
        break # 没有下一页了，退出循环

print(f"✅ 共找到 {len(all_male_styles)} 个男士发型ID：\n")
for idx, hair_id in enumerate(all_male_styles, 1):
    print(f"{idx}. {hair_id}")