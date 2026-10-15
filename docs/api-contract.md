# API 契约（已冻结，禁止随意修改）

## POST /api/analyze
请求：{ "image": "base64字符串" }
响应：{
  "faceShape": "oval | round | square | heart",
  "beardRegions": [[x, y], ...],
  "densityLevel": "sparse | medium | dense",
  "heatmapData": [[x, y, intensity], ...],
  "recommendedStyles": ["goatee", "short_boxed", ...],
  "productTips": ["使用胡须油", ...]
}

## POST /api/beard-try-on
请求：{ "image": "base64", "templateId": "goatee_style_01" }
响应：{ "task_id": "xxx" }

## GET /api/task/{task_id}
响应：{ "status": "success", "url": "图片URL" }