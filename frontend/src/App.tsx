// 主应用组件 - 控制页面流程

import { useState, useCallback } from 'react';
import { UploadPage } from '@/pages/UploadPage';
import { LoadingPage } from '@/pages/LoadingPage';
import { ResultPage } from '@/pages/ResultPage';
import { analyzeImage } from '@/api/analyzeApi';
import type { AnalysisResult } from '@/types/AnalysisResult';

type AppStage = 'upload' | 'loading' | 'result' | 'error';

export default function App() {
  const [stage, setStage] = useState<AppStage>('upload');
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>('');

  const handleGenerate = useCallback(async (imageBase64: string, preview: string) => {
    setPreviewUrl(preview);
    setStage('loading');

    try {
      const analysisResult = await analyzeImage(imageBase64);
      setResult(analysisResult);
      setStage('result');
    } catch (error) {
      const msg = error instanceof Error ? error.message : '暂时无法连接分析服务，请稍后重试。';
      setErrorMsg(msg);
      setStage('error');
    }
  }, []);

  const handleRestart = useCallback(() => {
    setStage('upload');
    setPreviewUrl('');
    setResult(null);
    setErrorMsg('');
  }, []);

  const handleReselect = useCallback(() => {
    setStage('upload');
    setResult(null);
    setErrorMsg('');
  }, []);

  if (stage === 'loading') {
    return <LoadingPage previewUrl={previewUrl} />;
  }

  if (stage === 'result' && result) {
    return (
      <ResultPage
        result={result}
        previewUrl={previewUrl}
        onRestart={handleRestart}
        onReselect={handleReselect}
      />
    );
  }

  if (stage === 'error') {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-stone-50 to-amber-50/30 px-5">
        <div className="w-full max-w-lg text-center">
          <p className="mb-4 text-base font-medium text-red-600">{errorMsg}</p>
          <button
            onClick={handleRestart}
            className="rounded-2xl bg-amber-900 px-8 py-3 text-sm font-semibold text-white transition-colors hover:bg-amber-800"
          >
            重新开始
          </button>
        </div>
      </div>
    );
  }

  return <UploadPage onGenerate={handleGenerate} />;
}
