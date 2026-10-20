// 分析结果页面

import { useEffect, useMemo, useRef, useState } from 'react';
import {
  RotateCcw,
  Home,
  Sparkles,
  User,
  Scissors,
  Droplets,
  Brush,
  Image as ImageIcon,
} from 'lucide-react';
import type { AnalysisResult, RecommendedStyle } from '@/types/AnalysisResult';
import {
  faceShapeLabels,
  densityLevelLabels,
  hairlineLevelLabels,
  hairstyleLabels,
  beardStyleLabels,
  UNKNOWN_STYLE_LABEL,
} from '@/config/labels';
import { extractHairlineLevel } from '@/config/hairlineConfig';
import { displayApiText, resolveImageSource } from '@/utils/apiContent';
import { isMockMode } from '@/api/analyzeApi';
import { BeardOverlay } from '@/components/BeardOverlay';
import { MascotMark } from '@/components/MascotMark';
import { generateTryOn, uploadTryOnImage } from '@/api/tryOnApi';
import { SharePoster } from '@/components/SharePoster';

interface ResultPageProps {
  result: AnalysisResult;
  previewUrl: string;
  onRestart: () => void;
  onReselect: () => void;
}

export function ResultPage({ result, previewUrl, onRestart, onReselect }: ResultPageProps) {
  const [beardUrl, setBeardUrl] = useState('');
  const [hairUrl, setHairUrl] = useState('');
  const [selectedTryOn, setSelectedTryOn] = useState<'beard' | 'hair' | null>(null);
  const [tryOnLoading, setTryOnLoading] = useState(false);
  const [tryOnError, setTryOnError] = useState('');
  const [showPoster, setShowPoster] = useState(false);
  const tryOnController = useRef<AbortController | null>(null);
  useEffect(() => () => { tryOnController.current?.abort(); }, []);

  async function handleTryOn() {
    const beardTemplate = result.recommendedStyles?.[1];
    const hairTemplate = result.hairRecommendations?.[0]?.hairTemplateId;
    const missing = [!beardUrl && !beardTemplate ? '胡须' : '', !hairUrl && !hairTemplate ? '发型' : ''].filter(Boolean);
    const tasks: Array<{ kind: 'beard' | 'hair'; templateId: string }> = [];
    if (!beardUrl && beardTemplate) tasks.push({ kind: 'beard', templateId: beardTemplate });
    if (!hairUrl && hairTemplate) tasks.push({ kind: 'hair', templateId: hairTemplate });
    if (tasks.length === 0) {
      setTryOnError(missing.length ? `没有收到${missing.join('和')}试戴所需的造型编号。` : '两张试戴图片已经生成。');
      return;
    }
    const controller = new AbortController();
    tryOnController.current = controller;
    setTryOnLoading(true);
    setTryOnError('');
    try {
      const fileId = await uploadTryOnImage(previewUrl, controller.signal);
      const results = await Promise.allSettled(tasks.map(async ({ kind, templateId }) => {
        const url = await generateTryOn(fileId, templateId, kind, controller.signal);
        if (!controller.signal.aborted) {
          if (kind === 'beard') setBeardUrl(url);
          else setHairUrl(url);
          setSelectedTryOn((current) => current ?? kind);
        }
      }));
      if (!controller.signal.aborted) {
        const failures = results.flatMap((item, index) => item.status === 'rejected' ? [tasks[index].kind === 'beard' ? '胡须' : '发型'] : []);
        const messages = [
          missing.length ? `没有收到${missing.join('和')}试戴所需的造型编号` : '',
          failures.length ? `${failures.join('和')}试戴生成失败，请重试` : '',
        ].filter(Boolean);
        setTryOnError(messages.join('；'));
      }
    } catch (error) {
      if (!controller.signal.aborted) setTryOnError(error instanceof Error ? error.message : '试戴生成失败，请重试。');
    } finally {
      if (!controller.signal.aborted) setTryOnLoading(false);
      if (tryOnController.current === controller) tryOnController.current = null;
    }
  }
  const tryOnUrl = selectedTryOn === 'beard' ? beardUrl : selectedTryOn === 'hair' ? hairUrl : '';
  // 提取发际线值（通过适配文件统一获取字段名）
  const hairlineValue = useMemo(() => extractHairlineLevel(result as Record<string, unknown>), [result]);
  const hasHairline = hairlineValue !== undefined && hairlineValue in hairlineLevelLabels;

  // 解析推荐造型
  const styles = result.recommendedStyles ?? [];
  // 按造型类型分类，不依赖数组顺序；后端样例中的 goatee 也不会被误当成发型。
  const hairstyleKey: RecommendedStyle | undefined = styles.find((style) => style in hairstyleLabels);
  const beardStyleKey: RecommendedStyle | undefined = styles.find((style) => style in beardStyleLabels);
  const hairstyleLabel = hairstyleKey ? (hairstyleLabels[hairstyleKey] ?? UNKNOWN_STYLE_LABEL) : null;
  const beardStyleLabel = beardStyleKey ? (beardStyleLabels[beardStyleKey] ?? UNKNOWN_STYLE_LABEL) : null;
  const hairRecommendations = (result.hairRecommendations ?? []).map((item) => ({
    styleName: displayApiText(item.styleName) || '推荐发型',
    reason: displayApiText(item.reason),
    imageSrc: resolveImageSource(item.imageUrl),
    difficulty: item.difficulty,
    maintenance: displayApiText(item.maintenance),
  }));
  const hairTips = (result.hairTips ?? []).map(displayApiText).filter(Boolean);
  const productTips = (result.productTips ?? []).map(displayApiText).filter(Boolean);

  const hasHeatmap = result.heatmapData && result.heatmapData.length > 0;

  return (
    <div className="min-h-screen bg-gradient-to-b from-stone-50 to-amber-50/30">
      <div className="mx-auto max-w-6xl px-5 pb-12 pt-6 sm:px-8 lg:px-10 lg:pt-8">
        <header className="mb-6 flex items-center gap-3">
          <div className="flex h-14 w-16 items-center justify-center overflow-hidden rounded-2xl bg-[#fffbed]">
            <MascotMark className="h-12 w-14" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber-800">decent-beard-taste</p>
            <h1 className="mt-0.5 text-lg font-bold text-stone-800">你的定制形象方案</h1>
          </div>
        </header>

        <div className="grid items-center gap-5 lg:grid-cols-[minmax(0,1.05fr)_minmax(320px,0.95fr)] lg:gap-7">
          {/* 顶部照片区域 + 演示标记 */}
          <div>
          <div className="relative overflow-hidden rounded-3xl bg-stone-100 shadow-sm" style={{ aspectRatio: '1 / 1' }}>
            <img src={tryOnUrl || previewUrl} alt={tryOnUrl ? (selectedTryOn === 'hair' ? '发型试戴效果' : '胡须试戴效果') : '你的照片'} className="h-full w-full object-contain" onError={() => { if (tryOnUrl) { if (selectedTryOn === 'hair') { setHairUrl(''); setSelectedTryOn(beardUrl ? 'beard' : null); } else { setBeardUrl(''); setSelectedTryOn(hairUrl ? 'hair' : null); } setTryOnError('试戴图片加载失败，请重试。'); } }} />
            {!tryOnUrl && <BeardOverlay
              imageUrl={previewUrl}
              beardRegions={result.beardRegions}
              heatmapData={result.heatmapData}
            />}
            <div className="absolute left-3 top-3 rounded-full bg-amber-900/90 px-3 py-1 text-xs font-medium text-amber-50 backdrop-blur-sm">
              {tryOnUrl ? (selectedTryOn === 'hair' ? '发型试戴效果' : '胡须试戴效果') : isMockMode() ? '演示示例数据' : 'AI 分析结果'}
            </div>
          </div>
          {(beardUrl || hairUrl) && <div className="mt-3 grid grid-cols-2 gap-2" aria-label="切换试戴效果">
            <button type="button" disabled={!beardUrl} aria-pressed={selectedTryOn === 'beard'} onClick={() => setSelectedTryOn('beard')} className={`rounded-2xl px-4 py-3 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${selectedTryOn === 'beard' ? 'bg-amber-900 text-white' : 'bg-white text-stone-600 shadow-sm'}`}>胡须试戴{!beardUrl && tryOnLoading ? '（生成中）' : ''}</button>
            <button type="button" disabled={!hairUrl} aria-pressed={selectedTryOn === 'hair'} onClick={() => setSelectedTryOn('hair')} className={`rounded-2xl px-4 py-3 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${selectedTryOn === 'hair' ? 'bg-amber-900 text-white' : 'bg-white text-stone-600 shadow-sm'}`}>发型试戴{!hairUrl && tryOnLoading ? '（生成中）' : ''}</button>
          </div>}
          {(!beardUrl || !hairUrl) && <button type="button" onClick={handleTryOn} disabled={tryOnLoading} className="mt-3 flex w-full items-center justify-center gap-2 rounded-2xl bg-amber-900 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-amber-800 disabled:cursor-wait disabled:opacity-60">
            <Sparkles className={`h-4 w-4 ${tryOnLoading ? 'animate-pulse' : ''}`} />
            {tryOnLoading ? '正在生成试戴效果，请稍候…' : (beardUrl || hairUrl) ? '重试未生成的效果' : '生成胡须和发型试戴效果'}
          </button>}
          {tryOnError && <p role="alert" className="mt-2 text-center text-sm text-red-600">{tryOnError}</p>}
          <button type="button" onClick={() => setShowPoster(true)} disabled={!beardUrl && !hairUrl} className="mt-3 flex w-full items-center justify-center gap-2 rounded-2xl border border-amber-900/20 bg-white px-4 py-3 text-sm font-semibold text-amber-900 transition-colors hover:bg-amber-50 disabled:cursor-not-allowed disabled:opacity-40">
            <ImageIcon className="h-4 w-4" />生成分享海报
          </button>
          {!beardUrl && !hairUrl && <p className="mt-2 text-center text-xs text-stone-500">生成至少一种试戴效果后，就可以制作海报。</p>}
          </div>

          <aside className="relative flex min-h-[360px] flex-col items-center justify-center overflow-hidden rounded-[2rem] border border-amber-900/5 bg-[#fffbed] px-6 py-5 text-center sm:min-h-[420px] lg:min-h-[500px]">
            <div aria-hidden="true" className="absolute -right-12 -top-16 h-56 w-56 rounded-full bg-amber-200/35 blur-3xl" />
            <MascotMark className="relative w-52 drop-shadow-[0_12px_18px_rgba(68,40,28,0.12)] sm:w-60 lg:w-64" />
            <div className="relative mt-1">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber-800">Your grooming guide</p>
              <h2 className="mt-2 text-xl font-bold text-stone-800">你的方案已经整理好</h2>
              <p className="mt-2 text-sm leading-relaxed text-stone-500">查看分析结果，了解适合你的造型与日常打理建议。</p>
            </div>
            <div className="relative mt-6 flex w-full gap-3">
              <button
                onClick={onReselect}
                className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-white py-3 text-sm font-medium text-stone-600 shadow-sm transition-colors hover:bg-stone-50"
              >
                <RotateCcw className="h-4 w-4" />
                重新选择
              </button>
              <button
                onClick={onRestart}
                className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-amber-900 py-3 text-sm font-medium text-white shadow-sm transition-colors hover:bg-amber-800"
              >
                <Home className="h-4 w-4" />
                重新开始
              </button>
            </div>
          </aside>
        </div>

        <div className="mt-5 grid gap-5 md:grid-cols-2">
        {/* 区块1：脸型 */}
        <ResultSection icon={<User className="h-5 w-5 text-amber-800" />} title="脸型">
          <p className="text-lg font-semibold text-stone-700">
            {result.faceShape ? (faceShapeLabels[result.faceShape] ?? '暂未提供该脸型说明') : '暂未提供脸型数据'}
          </p>
        </ResultSection>

        {/* 区块2：发际线（如果结果中有此字段才显示） */}
        {hasHairline && (
          <ResultSection icon={<Brush className="h-5 w-5 text-amber-800" />} title="发际线">
            <p className="text-lg font-semibold text-stone-700">
              {hairlineLevelLabels[hairlineValue as keyof typeof hairlineLevelLabels]}
            </p>
          </ResultSection>
        )}

        {/* 区块3：胡须密度 */}
        <ResultSection icon={<Droplets className="h-5 w-5 text-amber-800" />} title="胡须密度">
          <p className="text-lg font-semibold text-stone-700">
            {result.densityLevel ? (densityLevelLabels[result.densityLevel] ?? '暂未提供密度说明') : '暂未提供密度数据'}
          </p>
        </ResultSection>

        {/* 区块4：推荐造型 - 发型和胡须分两个卡片 */}
        {(hairstyleLabel || beardStyleLabel) && (
          <ResultSection icon={<Scissors className="h-5 w-5 text-amber-800" />} title="推荐造型">
            <div className="space-y-3">
              {hairstyleLabel && (
                <div className="rounded-2xl border border-amber-200/60 bg-amber-50/40 p-4">
                  <p className="mb-1 text-xs font-medium text-amber-800">推荐发型</p>
                  <p className="text-base font-semibold text-stone-700">{hairstyleLabel}</p>
                </div>
              )}
              {beardStyleLabel && (
                <div className="rounded-2xl border border-stone-200/60 bg-stone-50/60 p-4">
                  <p className="mb-1 text-xs font-medium text-stone-500">推荐胡须造型</p>
                  <p className="text-base font-semibold text-stone-700">{beardStyleLabel}</p>
                </div>
              )}
            </div>
          </ResultSection>
        )}

        {/* 区块5：产品建议 */}
        {productTips.length > 0 && (
          <ResultSection icon={<Droplets className="h-5 w-5 text-amber-800" />} title="产品建议">
            <ul className="space-y-2">
              {productTips.map((tip, index) => (
                <li
                  key={index}
                  className="flex items-start gap-2 text-sm leading-relaxed text-stone-600"
                >
                  <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-700" />
                  {tip}
                </li>
              ))}
            </ul>
          </ResultSection>
        )}

        {/* 新增字段：发型推荐详情 */}
        {hairRecommendations.length > 0 && (
          <ResultSection icon={<Scissors className="h-5 w-5 text-amber-800" />} title="个性化发型推荐">
            <div className="space-y-4">
              {hairRecommendations.map((item, index) => (
                <article key={`${item.styleName}-${index}`} className="overflow-hidden rounded-2xl border border-amber-200/60 bg-amber-50/30">
                  {item.imageSrc && (
                    <img
                      src={item.imageSrc}
                      alt={item.styleName}
                      className="max-h-64 w-full bg-stone-100 object-contain"
                      onError={(event) => { event.currentTarget.style.display = 'none'; }}
                    />
                  )}
                  <div className="p-4">
                    <h3 className="font-semibold text-stone-700">{item.styleName}</h3>
                    {item.reason && <p className="mt-2 text-sm leading-relaxed text-stone-600">{item.reason}</p>}
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-stone-500">
                      {item.difficulty !== undefined && <span className="rounded-full bg-white px-3 py-1">难度等级：{item.difficulty}</span>}
                      {item.maintenance && <span className="rounded-full bg-white px-3 py-1">打理：{item.maintenance}</span>}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </ResultSection>
        )}

        {/* 新增字段：发型打理提示 */}
        {hairTips.length > 0 && (
          <ResultSection icon={<Brush className="h-5 w-5 text-amber-800" />} title="发型打理建议">
            <ul className="space-y-2">
              {hairTips.map((tip, index) => (
                <li key={index} className="flex items-start gap-2 text-sm leading-relaxed text-stone-600">
                  <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-700" />
                  {tip}
                </li>
              ))}
            </ul>
          </ResultSection>
        )}

        {/* 区块7：胡须热力图 */}
        <ResultSection icon={<ImageIcon className="h-5 w-5 text-amber-800" />} title="胡须热力图">
          {hasHeatmap ? (
            <div className="relative overflow-hidden rounded-2xl bg-stone-100" style={{ aspectRatio: '1 / 1' }}>
              <img src={previewUrl} alt="热力图" className="h-full w-full object-contain" />
              <BeardOverlay
                imageUrl={previewUrl}
                beardRegions={result.beardRegions}
                heatmapData={result.heatmapData}
              />
            </div>
          ) : (
            <p className="text-sm text-stone-400">暂未提供胡须热力图数据</p>
          )}
        </ResultSection>

        </div>
      </div>
      {showPoster && <SharePoster result={result} previewUrl={previewUrl} beardUrl={beardUrl} hairUrl={hairUrl} onClose={() => setShowPoster(false)} />}
    </div>
  );
}

// 结果区块通用组件
function ResultSection({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-3xl bg-white p-5 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        {icon}
        <h2 className="text-base font-bold text-stone-700">{title}</h2>
      </div>
      {children}
    </div>
  );
}
