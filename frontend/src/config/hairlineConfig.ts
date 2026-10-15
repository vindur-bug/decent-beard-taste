// 发际线字段适配
// 请和后台成员确认发际线字段名
// 当前暂时使用 hairlineLevel 作为 Mock 字段名，真实字段名尚未确认
// 确认后只需修改此处的 HAIRLINE_FIELD_NAME 即可

export const HAIRLINE_FIELD_NAME = 'hairlineLevel' as const;

// 从分析结果中提取发际线值
// 分析结果对象可能不包含发际线字段，此函数安全处理缺失情况
export function extractHairlineLevel(result: Record<string, unknown>): string | undefined {
  const value = result[HAIRLINE_FIELD_NAME];
  if (typeof value === 'string') {
    return value;
  }
  return undefined;
}
