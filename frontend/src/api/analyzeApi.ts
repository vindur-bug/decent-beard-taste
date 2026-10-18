// API 调用
// 分析接口：POST /api/analyze

import type { AnalyzeRequest, AnalysisResult } from '@/types/AnalysisResult';
import { mockResult } from '@/data/mockResult';

// 是否使用 Mock 模式
const USE_MOCK = import.meta.env.VITE_USE_MOCK_API === 'true';

// 后台地址（集中配置）
// 在 .env 文件中设置 VITE_API_BASE_URL
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'https://decent-beard-taste-production.up.railway.app';

// Mock 模式下的模拟延迟（毫秒）
const MOCK_DELAY_MS = 2000;

export async function analyzeImage(imageBase64: string): Promise<AnalysisResult> {
  if (USE_MOCK) {
    // Mock 模式：短暂等待后返回示例数据
    await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY_MS));
    return mockResult;
  }

  // 真实 API 模式
  // 请和后台成员确认 API 地址
  const url = `${API_BASE_URL}/api/analyze`;
  const body: AnalyzeRequest = { image: imageBase64 };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`API 请求失败：${response.status}`);
    }

    const data = await response.json();
    return data as AnalysisResult;
  } catch (error) {
    // 网络错误或其他异常
    throw new Error('暂时无法连接分析服务，请稍后重试。');
  }
}

export function isMockMode(): boolean {
  return USE_MOCK;
}
