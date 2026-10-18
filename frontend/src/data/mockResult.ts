// Mock 示例数据
// 当前为比赛演示使用，并非真实 AI 分析结果
// 修改此文件即可改变演示页面显示的示例结果

import type { AnalysisResult } from '@/types/AnalysisResult';

export const mockResult: AnalysisResult = {
  faceShape: 'oval',
  densityLevel: 'sparse',
  recommendedStyles: [
    'short_textured_side_part',
    'stubble_beard',
  ],
  productTips: [
    '清洁胡须和下方皮肤',
    '按需要使用胡须护理产品',
  ],
  hairRecommendations: [
    {
      styleName: '侧分短发',
      reason: '椭圆脸适合露出额头，侧分可以增加面部立体感。',
      difficulty: 2,
      maintenance: '每3-4周修剪一次',
    },
    {
      styleName: '纹理碎发',
      reason: '增加顶部高度，让面部比例显得更修长。',
      difficulty: 1,
      maintenance: '每2-3周修剪一次',
    },
  ],
  hairTips: [
    '避免厚重刘海遮住额头',
    '顶部保留一定长度，方便日常造型',
  ],
  beardRegions: [],
  heatmapData: [],
  hairlineLevel: 'normal',
};
