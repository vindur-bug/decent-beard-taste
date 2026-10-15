// 造型预览占位区域
// 当前不连接真实 YouCam，仅展示占位内容
// 试戴接口和样式编号需要团队确认后再连接

import { Scissors } from 'lucide-react';

export function StylePreviewPlaceholder() {
  return (
    <div className="rounded-2xl border border-dashed border-stone-300 bg-stone-50 p-6 text-center">
      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-stone-200">
        <Scissors className="h-6 w-6 text-stone-500" />
      </div>
      <p className="text-sm font-medium text-stone-600">造型预览（示意效果）</p>
      <p className="mt-1 text-xs text-stone-400">
        演示图片占位区域，后续连接试戴接口后展示造型预览
      </p>
    </div>
  );
}
