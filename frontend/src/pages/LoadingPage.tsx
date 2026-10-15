// 等待状态页面

import { Loader2 } from 'lucide-react';
import loadingCat from '@/assets/loading-cat.png';

interface LoadingPageProps {
  previewUrl: string;
}

export function LoadingPage({ previewUrl }: LoadingPageProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-stone-50 via-[#fffdf7] to-amber-50/50 px-5 py-8">
      <div className="w-full max-w-4xl overflow-hidden rounded-[2rem] border border-amber-900/5 bg-white/80 shadow-[0_24px_70px_-42px_rgba(68,40,28,0.35)] md:flex md:items-stretch">
        <div className="relative flex min-h-52 items-center justify-center overflow-hidden bg-[#fffbed] px-8 py-6 md:w-[44%] md:min-h-[390px]">
          <div aria-hidden="true" className="absolute h-64 w-64 rounded-full bg-amber-200/35 blur-2xl" />
          <img
            src={loadingCat}
            alt="点赞的黑猫吉祥物"
            className="relative w-48 rounded-[2rem] object-contain mix-blend-multiply drop-shadow-[0_14px_20px_rgba(68,40,28,0.12)] sm:w-56 md:w-72"
          />
        </div>

        <div className="flex flex-1 flex-col items-center justify-center px-6 py-8 text-center sm:px-10 md:items-start md:text-left">
          <div className="mb-6 flex items-center gap-4">
            <div className="h-20 w-20 overflow-hidden rounded-2xl bg-stone-100 shadow-sm sm:h-24 sm:w-24">
              <img src={previewUrl} alt="你的照片" className="h-full w-full object-cover" />
            </div>
            <div className="text-left">
              <p className="text-xs font-medium uppercase tracking-[0.16em] text-amber-800">Personal style plan</p>
              <p className="mt-1 text-sm text-stone-500">照片已收到</p>
            </div>
          </div>

          <div className="mb-3 flex items-center justify-center gap-2 text-amber-800 md:justify-start">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-lg font-semibold text-stone-700">正在整理你的方案</span>
          </div>
          <p className="text-sm leading-relaxed text-stone-500">
            正在读取照片特征，并组合适合你的造型与打理建议。
          </p>
          <div aria-hidden="true" className="mt-7 h-1.5 w-full max-w-xs overflow-hidden rounded-full bg-amber-100">
            <div className="h-full w-2/3 animate-pulse rounded-full bg-amber-700/75" />
          </div>
          <p className="mt-3 text-xs text-stone-400">decent-beard-taste</p>
        </div>
      </div>
    </div>
  );
}
