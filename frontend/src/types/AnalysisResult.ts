// API 数据类型定义
// 后台返回的分析结果数据结构

// 脸型英文枚举值：oval | round | square | heart | long
export type FaceShape = 'oval' | 'round' | 'square' | 'heart' | 'long';

// 胡须密度英文枚举值：sparse | medium | dense
export type DensityLevel = 'sparse' | 'medium' | 'dense';

// 发际线英文枚举值：high | normal | receding
// 注意：本项目约定 receding 表示"发际线偏低"，请勿按英文常见含义翻译
export type HairlineLevel = 'high' | 'normal' | 'receding';

// 推荐造型英文值枚举
export type RecommendedStyle =
  | 'short_textured_side_part'
  | 'textured_perm'
  | 'natural_middle_part'
  | 'stubble_beard'
  | 'goatee'
  | 'all_goatee'
  | 'full_beard'
  | 'short_boxed'
  | 'clean_shave';

// 胡须区域坐标点 [x, y]，支持 0~1 相对坐标或图片像素坐标
export type RegionPoint = [number, number];

// 热力图数据点 [x, y, intensity]；坐标支持相对比例或图片像素，强度为 0~1
export type HeatmapPoint = [number, number, number];

// 发型推荐图片可能是普通 URL、data URL、Base64 字符串，或 JSON 图片对象。
export type RecommendationImage =
  | string
  | {
      url?: string;
      imageUrl?: string;
      image?: string | Record<string, unknown>;
      base64?: string;
      data?: string | Record<string, unknown>;
      content?: string | Record<string, unknown>;
      mimeType?: string;
      contentType?: string;
      type?: string;
      [key: string]: unknown;
    };

// API 返回的一项发型建议
export interface HairRecommendation {
  styleName?: string;
  reason?: string;
  imageUrl?: RecommendationImage | null;
  difficulty?: number;
  maintenance?: string;
}

// 分析结果完整结构
// 注意：所有字段都是可选的，后台可能缺少某些字段
export interface AnalysisResult {
  faceShape?: FaceShape;
  densityLevel?: DensityLevel;
  recommendedStyles?: RecommendedStyle[];
  productTips?: string[];
  beardRegions?: RegionPoint[];
  heatmapData?: HeatmapPoint[];
  // 请和后台成员确认发际线字段名
  // 当前暂时使用 hairlineLevel 作为 Mock 字段名
  hairlineLevel?: HairlineLevel;
  hairRecommendations?: HairRecommendation[];
  hairTips?: string[];
}

// POST /api/analyze 请求体
export interface AnalyzeRequest {
  image: string; // Base64 字符串
}
