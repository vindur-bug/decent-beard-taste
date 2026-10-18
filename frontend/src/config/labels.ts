// 英文值到中文显示名称的映射
// 修改此处即可更新页面显示的中文名称

import type { FaceShape, DensityLevel, HairlineLevel, RecommendedStyle } from '@/types/AnalysisResult';

export const faceShapeLabels: Record<FaceShape, string> = {
  oval: '椭圆脸',
  round: '圆脸',
  square: '方脸',
  heart: '心形脸',
  long: '长脸',
};

export const densityLevelLabels: Record<DensityLevel, string> = {
  sparse: '较稀疏',
  medium: '中等',
  dense: '较浓密',
};

// 注意：本项目约定 receding 表示"发际线偏低"，请勿按英文常见含义翻译
export const hairlineLevelLabels: Record<HairlineLevel, string> = {
  high: '发际线偏高',
  normal: '正常',
  receding: '发际线偏低',
};

// 发型英文值对应中文
export const hairstyleLabels: Partial<Record<RecommendedStyle, string>> = {
  short_textured_side_part: '侧分短碎',
  textured_perm: '纹理烫',
  natural_middle_part: '自然中分',
};

// 胡须造型英文值对应中文
export const beardStyleLabels: Partial<Record<RecommendedStyle, string>> = {
  stubble_beard: '短茬胡',
  goatee: '山羊胡',
  all_goatee: '山羊胡',
  full_beard: '络腮胡',
  short_boxed: '短盒式胡须',
  clean_shave: '干净剃须',
};

// 未识别造型时的默认提示
export const UNKNOWN_STYLE_LABEL = '暂未提供该造型说明';
