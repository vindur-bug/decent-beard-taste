// 上传照片页面

import { useRef, useState, useCallback } from 'react';
import { Upload, RotateCw, Trash2, RefreshCw, Sparkles, Camera } from 'lucide-react';
import {
  fileToBase64,
  isAcceptedImageType,
  ACCEPTED_IMAGE_EXTENSIONS,
} from '@/utils/imageToBase64';
import { MascotMark } from '@/components/MascotMark';

interface UploadPageProps {
  onGenerate: (imageBase64: string, previewUrl: string) => void;
}

export function UploadPage({ onGenerate }: UploadPageProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  const [rotation, setRotation] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = useCallback(async (file: File) => {
    setError(null);

    if (!isAcceptedImageType(file)) {
      setError('请上传 JPG、PNG 或 WebP 图片。');
      return;
    }

    try {
      const base64 = await fileToBase64(file);
      setImageBase64(base64);
      setPreviewUrl(base64);
      setRotation(0);
    } catch {
      setError('照片读取失败，请重新选择。');
    }
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFileSelect(file);
      }
    },
    [handleFileSelect]
  );

  const handleReset = useCallback(() => {
    setPreviewUrl(null);
    setImageBase64(null);
    setRotation(0);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const handleRotate = useCallback(() => {
    setRotation((r) => (r + 90) % 360);
  }, []);

  const handleGenerate = useCallback(() => {
    if (!imageBase64) {
      setError('请先选择一张照片。');
      return;
    }
    onGenerate(imageBase64, previewUrl!);
  }, [imageBase64, previewUrl, onGenerate]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-stone-50 to-amber-50/30">
      <div className="mx-auto max-w-6xl px-5 pb-10 pt-5 sm:px-8 lg:px-10 lg:pt-7">
        <header className="flex items-center gap-3">
          <div className="flex h-12 w-14 items-center justify-center overflow-hidden rounded-2xl bg-amber-100/70">
            <MascotMark className="h-11 w-12" />
          </div>
          <div>
            <p className="text-sm font-extrabold tracking-tight text-stone-800">decent-beard-taste</p>
            <p className="mt-0.5 text-xs text-stone-500">让每根胡子都长得有道理</p>
          </div>
        </header>

        <main className="mt-6 grid items-center gap-6 lg:min-h-[calc(100vh-112px)] lg:grid-cols-[minmax(0,1.05fr)_minmax(400px,0.95fr)] lg:gap-12">
          <section className="relative flex items-center overflow-hidden rounded-[2rem] border border-amber-900/5 bg-[#fffbed]/80 px-5 py-6 sm:px-8 lg:min-h-[420px] lg:self-center lg:px-9 lg:py-8">
            <div aria-hidden="true" className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-amber-200/35 blur-3xl" />
            <div className="relative grid w-full grid-cols-[minmax(0,1fr)_minmax(120px,0.72fr)] items-center gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(170px,0.78fr)] lg:grid-cols-[minmax(0,1.25fr)_minmax(190px,0.75fr)] lg:gap-5">
              <div>
                <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-amber-900 px-3.5 py-1.5 text-xs font-medium text-amber-50">
                  <Sparkles className="h-3.5 w-3.5" />
                  AI 胡须规划师
                </div>
                <h1 className="text-2xl font-bold leading-tight tracking-normal text-stone-800 sm:text-3xl lg:text-[2.5rem]">
                  <span className="block">让每根胡子</span>
                  <span className="mt-4 block">都长得有道理</span>
                </h1>
                <p className="mt-5 max-w-sm text-sm leading-[1.85] tracking-[0.035em] text-stone-600 sm:text-base">
                  根据你的脸型与胡须特征，整理适合你的造型建议和打理步骤。
                </p>
              </div>
              <div className="relative flex items-center justify-center">
                <MascotMark className="w-full drop-shadow-[0_12px_16px_rgba(68,40,28,0.12)] mix-blend-multiply" />
              </div>
            </div>
          </section>

          <section className="rounded-[2rem] border border-stone-200/70 bg-white/90 p-5 shadow-[0_18px_55px_-35px_rgba(68,40,28,0.32)] sm:p-7">
            <div className="mb-5">
              <h2 className="text-lg font-bold text-stone-800">上传你的正面照片</h2>
              <p className="mt-1 text-sm text-stone-500">光线清晰、正对镜头的照片会更适合分析。</p>
            </div>

        {/* 上传区域 */}
        {!previewUrl ? (
          <div
            onClick={() => fileInputRef.current?.click()}
            className="cursor-pointer rounded-3xl border-2 border-dashed border-stone-300 bg-white/60 p-10 text-center transition-all hover:border-amber-700 hover:bg-amber-50/40"
          >
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-amber-100">
              <Camera className="h-8 w-8 text-amber-800" />
            </div>
            <p className="text-base font-medium text-stone-700">选择照片</p>
            <p className="mt-1 text-xs text-stone-400">支持 JPG、PNG、WebP 格式</p>
          </div>
        ) : (
          <div className="rounded-3xl bg-white p-4 shadow-sm">
            <div
              className="relative overflow-hidden rounded-2xl bg-stone-100"
              style={{ aspectRatio: '1 / 1' }}
            >
              <img
                src={previewUrl}
                alt="预览照片"
                className="h-full w-full object-contain transition-transform duration-300"
                style={{ transform: `rotate(${rotation}deg)` }}
              />
            </div>
            <div className="mt-4 flex items-center justify-center gap-3">
              <button
                onClick={handleRotate}
                className="flex items-center gap-1.5 rounded-full bg-stone-100 px-4 py-2 text-sm font-medium text-stone-600 transition-colors hover:bg-stone-200"
              >
                <RotateCw className="h-4 w-4" />
                旋转
              </button>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-1.5 rounded-full bg-stone-100 px-4 py-2 text-sm font-medium text-stone-600 transition-colors hover:bg-stone-200"
              >
                <RefreshCw className="h-4 w-4" />
                重新选择
              </button>
              <button
                onClick={handleReset}
                className="flex items-center gap-1.5 rounded-full bg-stone-100 px-4 py-2 text-sm font-medium text-stone-600 transition-colors hover:bg-stone-200"
              >
                <Trash2 className="h-4 w-4" />
                删除
              </button>
            </div>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_IMAGE_EXTENSIONS}
          className="hidden"
          onChange={handleInputChange}
        />

        {/* 错误提示 */}
        {error && (
          <div className="mt-4 rounded-xl bg-red-50 px-4 py-3 text-center text-sm text-red-600">
            {error}
          </div>
        )}

        {/* 生成按钮 */}
        <button
          onClick={handleGenerate}
          disabled={!previewUrl}
          className={`mt-6 flex w-full items-center justify-center gap-2 rounded-2xl py-4 text-base font-semibold transition-all ${
            previewUrl
              ? 'bg-amber-900 text-white shadow-lg shadow-amber-900/20 hover:bg-amber-800 active:scale-[0.98]'
              : 'cursor-not-allowed bg-stone-200 text-stone-400'
          }`}
        >
          <Sparkles className="h-5 w-5" />
          生成我的方案
        </button>

        {!previewUrl && (
          <p className="mt-3 text-center text-xs text-stone-400">
            请先选择一张照片才能继续
          </p>
        )}

        {/* 隐私说明 */}
        <div className="mt-8 flex items-center justify-center gap-1.5 text-xs text-stone-400">
          <Upload className="h-3.5 w-3.5" />
          照片仅在浏览器本地预览，不会上传到第三方服务
        </div>
          </section>
        </main>
      </div>
    </div>
  );
}
