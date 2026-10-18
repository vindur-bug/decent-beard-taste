import type { RecommendationImage } from '@/types/AnalysisResult';

function decodeBase64(value: string): string | null {
  try {
    const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4);
    const binary = window.atob(padded);
    const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
    return new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  } catch {
    return null;
  }
}

/** API 文字字段是普通文字，直接显示原文。 */
export function displayApiText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

function imageStringToSource(value: string, mimeType?: string): string | null {
  const text = value.trim();
  if (!text) return null;

  if (/^(https?:|data:image\/|blob:|\/)/i.test(text)) return text;

  // 有些接口会把图片对象直接序列化成 JSON 字符串。
  if (text.startsWith('{') || text.startsWith('[')) {
    try {
      return resolveImageSource(JSON.parse(text) as RecommendationImage);
    } catch {
      return null;
    }
  }

  // 也兼容 API 返回的 data:application/json;base64,... 图片包装。
  const jsonDataUrl = text.match(/^data:application\/json;base64,(.+)$/i);
  if (jsonDataUrl) {
    const decoded = decodeBase64(jsonDataUrl[1]);
    if (decoded) {
      try {
        return resolveImageSource(JSON.parse(decoded) as RecommendationImage);
      } catch {
        return null;
      }
    }
  }

  // 原始 Base64 图片内容没有 MIME 信息时，按 JPEG 显示。
  if (/^[A-Za-z0-9+/_-]+={0,2}$/.test(text) && text.length > 40) {
    const normalized = text.replace(/-/g, '+').replace(/_/g, '/');
    const type = mimeType?.startsWith('image/') ? mimeType : 'image/jpeg';
    return `data:${type};base64,${normalized}`;
  }

  return null;
}

/** 从 URL、Base64 字符串或常见 JSON 图片对象中提取浏览器可显示的图片地址。 */
export function resolveImageSource(value: unknown, depth = 0): string | null {
  if (depth > 5 || value == null) return null;
  if (typeof value === 'string') return imageStringToSource(value);
  if (Array.isArray(value)) {
    for (const item of value) {
      const source = resolveImageSource(item, depth + 1);
      if (source) return source;
    }
    return null;
  }
  if (typeof value !== 'object') return null;

  const record = value as Record<string, unknown>;
  const mimeType = [record.mimeType, record.mime_type, record.contentType, record.content_type, record.type].find(
    (candidate): candidate is string => typeof candidate === 'string' && candidate.startsWith('image/')
  );

  for (const key of [
    'url', 'imageUrl', 'image_url', 'image', 'base64', 'base64Image', 'base64_image',
    'image_base64', 'data', 'content', 'result', 'output',
  ]) {
    const candidate = record[key];
    if (typeof candidate === 'string') {
      const source = imageStringToSource(candidate, mimeType);
      if (source) return source;
    } else if (candidate && typeof candidate === 'object') {
      const source = resolveImageSource(candidate, depth + 1);
      if (source) return source;
    }
  }

  return null;
}
