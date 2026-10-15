# ==========================================
# 成员3 推荐引擎（完美兼容成员4 Mock 版本 + YouCam ID 映射）
# ==========================================

def generate_recommendation(face_shape: str, hairline: str, time_pref: str = "medium") -> dict:
    """
    核心推荐引擎：接收CV提取的机器语言，输出结构化的JSON
    """
    # 1. 极致数据清洗（防脏数据）
    face_shape = str(face_shape).strip().lower() if face_shape else "oval"
    hairline = str(hairline).strip().lower() if hairline else "normal"
    time_pref = str(time_pref).strip().lower() if time_pref else "medium"

    if face_shape not in ["round", "oval", "square", "heart", "long"]:
        face_shape = "oval"
    if hairline not in ["high", "normal", "receding"]:
        hairline = "normal"
    if time_pref not in ["short", "medium", "long"]:
        time_pref = "medium"

    # 2. 45条规则核心数据库（保持你的原有逻辑不变）
    rules_db = {
        ("round", "high", "short"): {"densityLevel": "sparse", "recommendedStyles": ["short_textured_side_part", "stubble_beard"], "productTips": ["使用胡须油", "修须刀打造边缘"]},
        ("round", "high", "medium"): {"densityLevel": "medium", "recommendedStyles": ["textured_perm", "goatee"], "productTips": ["搭配发蜡", "定期修剪胡须"]},
        ("round", "high", "long"): {"densityLevel": "dense", "recommendedStyles": ["natural_middle_part", "full_beard"], "productTips": ["护发精油", "胡须刷打理"]},
        ("round", "normal", "short"): {"densityLevel": "sparse", "recommendedStyles": ["short_textured_side_part", "clean_shave"], "productTips": ["温和洁面", "日常保湿"]},
        ("round", "normal", "medium"): {"densityLevel": "medium", "recommendedStyles": ["textured_perm", "stubble_beard"], "productTips": ["使用胡须油", "修须刀打造边缘"]},
        ("round", "normal", "long"): {"densityLevel": "dense", "recommendedStyles": ["natural_middle_part", "full_beard"], "productTips": ["护发素", "胡须护理油"]},
        ("round", "receding", "short"): {"densityLevel": "sparse", "recommendedStyles": ["short_textured_side_part", "stubble_beard"], "productTips": ["生发精华", "控油洁面"]},
        ("round", "receding", "medium"): {"densityLevel": "medium", "recommendedStyles": ["textured_perm", "goatee"], "productTips": ["头皮精华", "胡须蜡"]},
        ("round", "receding", "long"): {"densityLevel": "dense", "recommendedStyles": ["natural_middle_part", "full_beard"], "productTips": ["发量修护精华", "胡须滋养油"]},
        ("square", "high", "short"): {"densityLevel": "sparse", "recommendedStyles": ["short_textured_side_part", "clean_shave"], "productTips": ["舒缓须后水", "控油乳液"]},
        ("square", "high", "medium"): {"densityLevel": "medium", "recommendedStyles": ["natural_middle_part", "stubble_beard"], "productTips": ["保湿面霜", "胡须软化剂"]},
        ("square", "high", "long"): {"densityLevel": "dense", "recommendedStyles": ["textured_perm", "full_beard"], "productTips": ["护发精油", "胡须梳"]},
        ("square", "normal", "short"): {"densityLevel": "sparse", "recommendedStyles": ["natural_middle_part", "clean_shave"], "productTips": ["洗面奶", "保湿水"]},
        ("square", "normal", "medium"): {"densityLevel": "medium", "recommendedStyles": ["natural_middle_part", "stubble_beard"], "productTips": ["温和洁面", "须后乳"]},
        ("square", "normal", "long"): {"densityLevel": "dense", "recommendedStyles": ["textured_perm", "full_beard"], "productTips": ["发膜", "胡须油"]},
        ("square", "receding", "short"): {"densityLevel": "sparse", "recommendedStyles": ["short_textured_side_part", "stubble_beard"], "productTips": ["头皮护理液", "洁面乳"]},
        ("square", "receding", "medium"): {"densityLevel": "medium", "recommendedStyles": ["natural_middle_part", "goatee"], "productTips": ["蓬松喷雾", "胡须修剪器"]},
        ("square", "receding", "long"): {"densityLevel": "dense", "recommendedStyles": ["textured_perm", "full_beard"], "productTips": ["生发液", "胡须保养油"]},
        ("long", "high", "short"): {"densityLevel": "dense", "recommendedStyles": ["textured_perm", "full_beard"], "productTips": ["护发素", "胡须刷"]},
        ("long", "high", "medium"): {"densityLevel": "medium", "recommendedStyles": ["short_textured_side_part", "goatee"], "productTips": ["发蜡", "胡须油"]},
        ("long", "high", "long"): {"densityLevel": "dense", "recommendedStyles": ["natural_middle_part", "full_beard"], "productTips": ["护发精油", "胡须护理套装"]},
        ("long", "normal", "short"): {"densityLevel": "sparse", "recommendedStyles": ["textured_perm", "stubble_beard"], "productTips": ["蓬松粉", "洁面乳"]},
        ("long", "normal", "medium"): {"densityLevel": "medium", "recommendedStyles": ["short_textured_side_part", "goatee"], "productTips": ["发泥", "须后水"]},
        ("long", "normal", "long"): {"densityLevel": "dense", "recommendedStyles": ["natural_middle_part", "full_beard"], "productTips": ["发膜", "胡须油"]},
        ("long", "receding", "short"): {"densityLevel": "sparse", "recommendedStyles": ["textured_perm", "stubble_beard"], "productTips": ["生发精华", "控油洗发水"]},
        ("long", "receding", "medium"): {"densityLevel": "medium", "recommendedStyles": ["short_textured_side_part", "full_beard"], "productTips": ["头皮营养液", "胡须蜡"]},
        ("long", "receding", "long"): {"densityLevel": "dense", "recommendedStyles": ["natural_middle_part", "full_beard"], "productTips": ["发量修护液", "胡须滋养油"]},
        ("oval", "high", "short"): {"densityLevel": "sparse", "recommendedStyles": ["short_textured_side_part", "stubble_beard"], "productTips": ["洗面奶", "须后乳"]},
        ("oval", "high", "medium"): {"densityLevel": "medium", "recommendedStyles": ["natural_middle_part", "stubble_beard"], "productTips": ["保湿水", "胡须软化剂"]},
        ("oval", "high", "long"): {"densityLevel": "dense", "recommendedStyles": ["textured_perm", "full_beard"], "productTips": ["护发精油", "胡须梳"]},
        ("oval", "normal", "short"): {"densityLevel": "sparse", "recommendedStyles": ["natural_middle_part", "clean_shave"], "productTips": ["温和洁面", "日常保湿"]},
        ("oval", "normal", "medium"): {"densityLevel": "medium", "recommendedStyles": ["short_textured_side_part", "stubble_beard"], "productTips": ["发蜡", "须后水"]},
        ("oval", "normal", "long"): {"densityLevel": "dense", "recommendedStyles": ["textured_perm", "goatee"], "productTips": ["发泥", "胡须油"]},
        ("oval", "receding", "short"): {"densityLevel": "sparse", "recommendedStyles": ["short_textured_side_part", "clean_shave"], "productTips": ["生发液", "洁面乳"]},
        ("oval", "receding", "medium"): {"densityLevel": "medium", "recommendedStyles": ["natural_middle_part", "stubble_beard"], "productTips": ["头皮精华", "保湿霜"]},
        ("oval", "receding", "long"): {"densityLevel": "dense", "recommendedStyles": ["textured_perm", "full_beard"], "productTips": ["发量精华", "胡须油"]},
        ("heart", "high", "short"): {"densityLevel": "sparse", "recommendedStyles": ["natural_middle_part", "stubble_beard"], "productTips": ["控油洁面", "须后乳"]},
        ("heart", "high", "medium"): {"densityLevel": "medium", "recommendedStyles": ["short_textured_side_part", "goatee"], "productTips": ["保湿水", "胡须修剪器"]},
        ("heart", "high", "long"): {"densityLevel": "dense", "recommendedStyles": ["textured_perm", "full_beard"], "productTips": ["发膜", "胡须护理油"]},
        ("heart", "normal", "short"): {"densityLevel": "sparse", "recommendedStyles": ["natural_middle_part", "clean_shave"], "productTips": ["洗面奶", "保湿乳液"]},
        ("heart", "normal", "medium"): {"densityLevel": "medium", "recommendedStyles": ["short_textured_side_part", "stubble_beard"], "productTips": ["发蜡", "须后水"]},
        ("heart", "normal", "long"): {"densityLevel": "dense", "recommendedStyles": ["textured_perm", "goatee"], "productTips": ["护发素", "胡须梳"]},
        ("heart", "receding", "short"): {"densityLevel": "sparse", "recommendedStyles": ["natural_middle_part", "stubble_beard"], "productTips": ["生发液", "洁面乳"]},
        ("heart", "receding", "medium"): {"densityLevel": "medium", "recommendedStyles": ["short_textured_side_part", "full_beard"], "productTips": ["头皮营养液", "胡须油"]},
        ("heart", "receding", "long"): {"densityLevel": "dense", "recommendedStyles": ["textured_perm", "full_beard"], "productTips": ["发量修护液", "胡须滋养油"]},
    }

    # 3. 查表
    result = rules_db.get((face_shape, hairline, time_pref))
    
    # 4. 终极兜底
    if not result:
        result = {
            "densityLevel": "medium",
            "recommendedStyles": ["natural_middle_part", "clean_shave"],
            "productTips": ["保持面部清洁", "日常保湿"]
        }

    # 5. 核心升级：根据成员4的Mock格式，动态生成发型对象
    hairstyle_id = result["recommendedStyles"][0]
    beard_id = result["recommendedStyles"][1]

    hair_mapping = {
        "short_textured_side_part": {"styleName": "侧分短碎", "reason": "修饰脸型，清爽百搭", "imageUrl": "https://example.com/side-part.jpg", "difficulty": 1, "maintenance": "每3-4周修剪一次"},
        "textured_perm": {"styleName": "纹理烫", "reason": "增加头顶蓬松度，视觉拉长脸型", "imageUrl": "https://example.com/textured-perm.jpg", "difficulty": 2, "maintenance": "每4-6周修剪一次"},
        "natural_middle_part": {"styleName": "自然中分", "reason": "柔和面部轮廓，自然稳重", "imageUrl": "https://example.com/middle-part.jpg", "difficulty": 1, "maintenance": "每3-4周修剪一次"}
    }
    
    hair_info = hair_mapping.get(hairstyle_id, {"styleName": "自然发型", "reason": "适合大部分脸型", "imageUrl": "https://example.com/natural.jpg", "difficulty": 1, "maintenance": "每3-4周修剪一次"})
    hair_recommendations = [hair_info]
    hair_tips = ["避免厚重刘海遮住额头", "顶部保留一定长度便于造型"]

    translation = {
        "short_textured_side_part": "侧分短碎", "textured_perm": "纹理烫",
        "natural_middle_part": "自然中分", "stubble_beard": "短茬胡",
        "goatee": "山羊胡", "full_beard": "络腮胡", "clean_shave": "干净剃须"
    }

    # ==========================================
    # 🟢 新增：YouCam API 模板 ID 映射（根据成员4提供的 template 列表）
    # ==========================================
    youcam_template_mapping = {
        "clean_shave": "all_shaved",
        "stubble_beard": "all_goatee",  # 兜底：YouCam没有直接的短茬胡，用山羊胡模板暂代
        "goatee": "all_goatee",
        "full_beard": "all_bandholz"    # 用 Bandholz（大胡子）模板代替络腮胡
    }
    
    # 将内部 ID 替换为 YouCam 的真实 template_id
    youcam_beard_id = youcam_template_mapping.get(beard_id, "all_shaved")
    youcam_recommended_styles = [hairstyle_id, youcam_beard_id]

    # 6. 组装最终返回（包含所有新旧字段，完美兼容！）
    return {
        "faceShape": face_shape, 
        "beardRegions": [[100, 100], [150, 150]], 
        "densityLevel": result["densityLevel"],
        "heatmapData": [[100, 100, 50], [150, 150, 80]], 
        "recommendedStyles": youcam_recommended_styles,  # 👈 注意这里换成了映射后的 ID
        "hairstyle_cn": translation.get(hairstyle_id, hairstyle_id),
        "beard_style_cn": translation.get(beard_id, beard_id),
        "reason": "根据您的脸型和发际线特征，这款组合能有效扬长避短。",
        "productTips": result["productTips"],
        "hairRecommendations": hair_recommendations,
        "hairTips": hair_tips
    }


# ==========================================
# 兼容层（契约要求）
# ==========================================
def recommend_styles(face_shape: str, density: str = "medium") -> dict:
    return generate_recommendation(face_shape, "normal", density)


# ==========================================
# 本地测试
# ==========================================
if __name__ == "__main__":
    print("=== 成员3 推荐引擎 (带YouCam映射版) 测试 ===")
    import json
    print(json.dumps(generate_recommendation("round", "high"), ensure_ascii=False, indent=2))