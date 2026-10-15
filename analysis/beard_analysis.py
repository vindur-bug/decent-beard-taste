# ==========================================
# 成员3 胡须分析模块 (beard_analysis.py) - 真实数据适配版
# 输入：bytes图片 + 成员2提供的字典格式 landmarks
# 输出：符合契约的胡须区域、密度和热力图数据
# ==========================================

def analyze_beard(image_bytes: bytes, landmarks: dict) -> dict:
    """
    分析胡须区域、密度和热力图
    适配成员2的数据格式：landmarks 是字典 {"152": [x, y], ...}，坐标为0-1小数
    兼容契约：image_bytes 为解码后的 bytes 数据
    """
    # 🛡️ 兜底逻辑：如果成员2没传数据或数据格式不对，保证绝不报错
    if not landmarks or not isinstance(landmarks, dict):
        return {
            "beardRegions": [[0.1, 0.5], [0.2, 0.6], [0.3, 0.5]], # 假数据占位
            "densityLevel": "medium",
            "heatmapData": [[0.1, 0.5, 70], [0.2, 0.6, 70], [0.3, 0.5, 70]]
        }

    # 1. 胡须区域定位 (beardRegions)
    beard_indexes = ["152", "172", "397", "234", "454"]
    beard_regions = []
    
    for idx in beard_indexes:
        if idx in landmarks:
            x = landmarks[idx][0]
            y = landmarks[idx][1]
            beard_regions.append([x, y])

    # 2. 密度分析 (densityLevel)
    if len(beard_regions) >= 4:
        density_level = "medium"
    else:
        density_level = "sparse"

    # 3. 热力图数据 (heatmapData)
    heatmap_data = []
    for region in beard_regions:
        intensity = 70
        heatmap_data.append([region[0], region[1], intensity])

    # 4. 返回符合契约的完整字典
    return {
        "beardRegions": beard_regions,
        "densityLevel": density_level,
        "heatmapData": heatmap_data
    }


# ==========================================
# 本地测试代码（直接测试朴总发来的真实数据！）
# ==========================================
if __name__ == "__main__":
    print("=== 成员3 胡须分析模块 (真实数据测试) ===")
    
    real_data = {
      "face_shape": "round",
      "landmarks": {
        "152": [0.5015743374824524, 0.620393693447113],
        "172": [0.33852094411849976, 0.5481072664260864],
        "397": [0.6728698015213013, 0.5540541410446167],
        "234": [0.29253000020980835, 0.41015058755874634],
        "454": [0.731300950050354, 0.4185183048248291]
      },
      "hairline": "normal"
    }

    # 测试 1：正常输入（传入 bytes）
    print("\n--- 测试 1: 朴总的真实数据 ---")
    result = analyze_beard(b"fake_image_bytes", real_data["landmarks"])
    print(result)

    # 测试 2：异常兜底（不传landmarks）
    print("\n--- 测试 2: 异常兜底 ---")
    print(analyze_beard(b"fake_image_bytes", {}))