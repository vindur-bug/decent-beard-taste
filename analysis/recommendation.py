import os
import json
import dashscope
from dashscope import Generation

# 从环境变量读取密钥，绝对不能写死在这里！
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
print("=== 检查 DashScope Key ===", "已加载" if dashscope.api_key else "未加载，为 None！")


def generate_recommendation(face_shape: str, hairline: str, time_pref: str = "medium") -> dict:
    # 1. 数据清洗
    face_shape = str(face_shape).strip().lower() if face_shape else "oval"
    hairline = str(hairline).strip().lower() if hairline else "normal"
    time_pref = str(time_pref).strip().lower() if time_pref else "medium"
    
    if face_shape not in ["round", "oval", "square", "heart", "long"]: face_shape = "oval"
    if hairline not in ["high", "normal", "receding"]: hairline = "normal"
    if time_pref not in ["short", "medium", "long"]: time_pref = "medium"

    # 2. 映射字典（补齐真实图片和 hairTemplateId）
    hair_mapping = {
        "short_textured_side_part": {
            "styleName": "纹理寸头", "difficulty": 1, "maintenance": "每3-4周修剪一次", 
            "imageUrl": "https://app-cdn.makeupar.com/cms/430a5763-f41c-4ea6-a9c8-7c64b9b3b942/1778665908784/file.jpg",
            "hairTemplateId": "male_textured_crop"
        },
        "textured_perm": {
            "styleName": "男士短卷发", "difficulty": 2, "maintenance": "每4-6周修剪一次", 
            "imageUrl": "https://app-cdn.makeupar.com/cms/47633eff-2086-4791-b454-825aa6f9e160/1780481384535/file.jpg",
            "hairTemplateId": "male_short_curly"
        },
        "natural_middle_part": {
            "styleName": "逗号刘海", "difficulty": 2, "maintenance": "每3-4周修剪一次", 
            "imageUrl": "https://app-cdn.makeupar.com/cms/02a90e43-398a-4eda-b0bc-e9595d75430f/1778825209411/file.jpg",
            "hairTemplateId": "male_textured_comma"
        }
    }
    
    translation = {
        "short_textured_side_part": "纹理寸头", "textured_perm": "男士短卷发", "natural_middle_part": "逗号刘海",
        "stubble_beard": "短茬胡", "goatee": "山羊胡", "full_beard": "络腮胡", "clean_shave": "干净剃须"
    }
    
    youcam_template_mapping = {
        "clean_shave": "all_shaved", 
        "stubble_beard": "all_mutton_chops", # 换成了羊排胡更像短茬
        "goatee": "all_goatee", 
        "full_beard": "all_bandholz"
    }

    # 3. 默认兜底方案
    final_hairstyle_id = "natural_middle_part"
    final_beard_id = "clean_shave"
    final_reason = "根据您的面部轮廓，选择了最百搭的清爽造型。"
    final_tips = ["保持面部清洁", "日常基础保湿"]
    final_density = "medium"

    # 4. 大模型推理决策
    try:
        prompt = f"""
        你是一个顶级的男士发型与胡须造型专家。请根据用户的客观数据，推理出最适合他的发型和胡须。
        
        【用户数据】
        - 脸型 (face_shape): {face_shape}
        - 发际线 (hairline): {hairline}
        - 打理意愿 (time_pref): {time_pref}
        
        【你的决策范围限制】
        发型 ID 只能从以下选择:short_textured_side_part, textured_perm, natural_middle_part
        胡须 ID 只能从以下选择:clean_shave, stubble_beard, goatee, full_beard
        
        【要求】
        请严格返回如下 JSON 格式（不要输出 markdown 标记）：
        {{
            "hairstyle_id": "推导出的发型ID",
            "beard_id": "推导出的胡须ID",
            "densityLevel": "sparse或medium或dense",
            "reason": "用40个字以内,像理发师一样专业地解释。",
            "productTips": ["建议1", "建议2"]
        }}
        """
        
        response = Generation.call(
            model="qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            result_format='message',
            response_format={'type': 'json_object'}
        )
        
        ai_data = json.loads(response.output.choices[0].message.content)
        
        if ai_data.get("hairstyle_id") in hair_mapping:
            final_hairstyle_id = ai_data["hairstyle_id"]
        if ai_data.get("beard_id") in translation:
            final_beard_id = ai_data["beard_id"]
            
        final_reason = ai_data.get("reason", final_reason)
        final_tips = ai_data.get("productTips", final_tips)
        final_density = ai_data.get("densityLevel", final_density)

    except Exception as e:
        print(f"⚠️ AI 推理失败: {e}")
        
        # 👇 关键改动：把真实的报错原因，直接写进返回的推荐理由里！
        final_reason = f"【大模型报错：{str(e)}】"
        
        final_hairstyle_id = "natural_middle_part"
        final_beard_id = "goatee"
        final_tips = ["保持面部清洁", "日常基础保湿"]

    # 5. 组装最终 JSON
    hair_info = hair_mapping.get(final_hairstyle_id, hair_mapping["natural_middle_part"])
    hairstyle_cn = translation.get(final_hairstyle_id, "自然发型")
    beard_style_cn = translation.get(final_beard_id, "干净剃须")
    youcam_beard_id = youcam_template_mapping.get(final_beard_id, "all_shaved")

    # 必须补全 all_hair_options 给前端！
    all_hair_options = [
        {"id": "male_textured_crop", "name": "纹理寸头", "image": "https://app-cdn.makeupar.com/cms/430a5763-f41c-4ea6-a9c8-7c64b9b3b942/1778665908784/file.jpg"},
        {"id": "male_short_curly", "name": "男士短卷发", "image": "https://app-cdn.makeupar.com/cms/47633eff-2086-4791-b454-825aa6f9e160/1780481384535/file.jpg"},
        {"id": "male_gray_taper_fade", "name": "渐变推剪", "image": "https://app-cdn.makeupar.com/cms/02a90e43-398a-4eda-b0bc-e9595d75430f/1778825209411/file.jpg"},
        {"id": "male_textured_comma", "name": "逗号刘海", "image": ""}, 
        {"id": "male_wavy_undercut", "name": "波浪底切", "image": ""},
        {"id": "male_tousled_cut", "name": "凌乱碎发", "image": ""},
        {"id": "male_afro", "name": "爆炸头", "image": ""},
        {"id": "male_bald", "name": "光头", "image": ""}
    ]

    return {
        "faceShape": face_shape,
        "beardRegions": [[100, 100], [150, 150]],
        "densityLevel": final_density,
        "heatmapData": [[100, 100, 50], [150, 150, 80]],
        "recommendedStyles": [final_hairstyle_id, youcam_beard_id],
        "hairstyle_cn": hairstyle_cn,
        "beard_style_cn": beard_style_cn,
        "reason": final_reason,
        "productTips": final_tips,
        "hairRecommendations": [
            {
                "styleName": hair_info["styleName"],
                "reason": final_reason,
                "imageUrl": hair_info["imageUrl"],
                "difficulty": hair_info["difficulty"],
                "maintenance": hair_info["maintenance"],
                "hairTemplateId": hair_info["hairTemplateId"]
            }
        ],
        "hairTips": ["避免厚重刘海遮住额头", "顶部保留一定长度便于造型"],
        "all_hair_options": all_hair_options
    }

def recommend_styles(face_shape: str, density: str = "medium") -> dict:
    return generate_recommendation(face_shape, "normal", density)