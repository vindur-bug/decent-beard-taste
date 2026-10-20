import { useEffect, useState } from 'react';
import { Download, X } from 'lucide-react';
import { API_BASE_URL } from '@/api/analyzeApi';
import brandImage from '@/assets/decent-beard-taste.png';
import type { AnalysisResult } from '@/types/AnalysisResult';
import { beardStyleLabels, densityLevelLabels, faceShapeLabels, hairlineLevelLabels, hairstyleLabels } from '@/config/labels';
import { extractHairlineLevel } from '@/config/hairlineConfig';
import { displayApiText, resolveImageSource } from '@/utils/apiContent';

interface SharePosterProps {
  result: AnalysisResult;
  previewUrl: string;
  beardUrl: string;
  hairUrl: string;
  onClose: () => void;
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    const isRemoteImage = /^https?:\/\//i.test(src);
    // 海报中的远程图片通过后端代理加载，避免污染 Canvas，导致导出失败。
    const imageSrc = isRemoteImage
      ? `${API_BASE_URL.replace(/\/+$/, '')}/api/proxy-image?url=${encodeURIComponent(src)}`
      : src;
    image.crossOrigin = 'anonymous';
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error('海报图片加载失败，请稍后重试。'));
    image.src = imageSrc;
  });
}

async function createPoster(result: AnalysisResult, previewUrl: string, beardUrl: string, hairUrl: string): Promise<Blob> {
  const [mascot, beard, hair, original] = await Promise.all([
    loadImage(brandImage),
    beardUrl ? loadImage(beardUrl) : Promise.resolve(null),
    hairUrl ? loadImage(hairUrl) : Promise.resolve(null),
    result.heatmapData?.length ? loadImage(previewUrl) : Promise.resolve(null),
  ]);
  const hairImages = await Promise.all((result.hairRecommendations ?? []).map(async (item) => {
    const src = resolveImageSource(item.imageUrl);
    if (!src) return null;
    try { return await loadImage(src); } catch { return null; }
  }));
  const width = 960;
  const side = 58;
  const contentWidth = width - side * 2;
  const canvas = document.createElement('canvas');
  const measure = canvas.getContext('2d');
  if (!measure) throw new Error('当前浏览器无法生成海报。');
  const drawings: Array<(ctx: CanvasRenderingContext2D) => void> = [];
  let y = 0;

  function text(value: string, x: number, top: number, size: number, color = '#302721', weight = 400) {
    drawings.push((ctx) => {
      ctx.font = `${weight} ${size}px "Microsoft YaHei", "PingFang SC", sans-serif`;
      ctx.fillStyle = color;
      ctx.textBaseline = 'top';
      ctx.fillText(value, x, top);
    });
  }
  function wrapped(value: string, x: number, top: number, maxWidth: number, size = 25, color = '#62574f', weight = 400): number {
    measure!.font = `${weight} ${size}px "Microsoft YaHei", "PingFang SC", sans-serif`;
    const lines: string[] = [];
    for (const paragraph of value.split('\n')) {
      let line = '';
      for (const char of Array.from(paragraph)) {
        if (line && measure!.measureText(line + char).width > maxWidth) { lines.push(line); line = char; }
        else line += char;
      }
      lines.push(line);
    }
    const lineHeight = Math.round(size * 1.55);
    lines.forEach((line, index) => text(line, x, top + index * lineHeight, size, color, weight));
    return lines.length * lineHeight;
  }
  function card(top: number, height: number) {
    drawings.push((ctx) => {
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.roundRect(side, top, contentWidth, height, 30);
      ctx.fill();
    });
  }
  function section(title: string, entries: string[]) {
    const values = entries.filter(Boolean);
    if (!values.length) return;
    const top = y;
    const backgroundIndex = drawings.length;
    y += 35;
    text(title, side + 34, y, 28, '#793515', 700);
    y += 51;
    for (const entry of values) {
      y += wrapped(entry, side + 34, y, contentWidth - 68);
      y += 9;
    }
    y += 20;
    const height = y - top;
    const background = (ctx: CanvasRenderingContext2D) => { ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.roundRect(side, top, contentWidth, height, 30); ctx.fill(); };
    drawings.splice(backgroundIndex, 0, background);
    y += 20;
  }
  function imageSection(title: string, image: HTMLImageElement, heatmap = false) {
    const imageWidth = contentWidth - 48;
    const imageHeight = Math.min(900, Math.round(imageWidth * image.naturalHeight / image.naturalWidth));
    const top = y;
    const height = imageHeight + 106;
    card(top, height);
    text(title, side + 30, top + 25, 27, '#793515', 700);
    const boxX = side + 24;
    const boxY = top + 76;
    const scale = Math.min(imageWidth / image.naturalWidth, imageHeight / image.naturalHeight);
    const drawWidth = image.naturalWidth * scale;
    const drawHeight = image.naturalHeight * scale;
    const x = boxX + (imageWidth - drawWidth) / 2;
    const imageY = boxY + (imageHeight - drawHeight) / 2;
    drawings.push((ctx) => {
      ctx.fillStyle = '#f4f1ec';
      ctx.fillRect(boxX, boxY, imageWidth, imageHeight);
      ctx.drawImage(image, x, imageY, drawWidth, drawHeight);
      if (!heatmap) return;
      const point = (px: number, py: number) => [x + (px >= 0 && px <= 1 ? px : px / image.naturalWidth) * drawWidth, imageY + (py >= 0 && py <= 1 ? py : py / image.naturalHeight) * drawHeight];
      for (const [px, py, intensity] of result.heatmapData ?? []) {
        const [cx, cy] = point(px, py);
        const amount = Math.max(0, Math.min(1, intensity));
        const radius = (20 + amount * 30) * imageWidth / 600;
        const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
        gradient.addColorStop(0, `rgba(255,120,50,${0.6 * amount})`);
        gradient.addColorStop(1, 'rgba(255,120,50,0)');
        ctx.fillStyle = gradient; ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.fill();
      }
      for (const [px, py] of result.beardRegions ?? []) {
        const [cx, cy] = point(px, py);
        ctx.strokeStyle = 'rgba(56,189,248,0.9)'; ctx.fillStyle = 'rgba(56,189,248,0.3)'; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.arc(cx, cy, 7, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      }
    });
    y += height + 20;
  }

  drawings.push((ctx) => { ctx.drawImage(mascot, 140, 35, 990, 900, side, 34, 110, 100); });
  text('decent-beard-taste', side + 135, 49, 30, '#302721', 700);
  text('让每根胡子都长得有道理', side + 135, 95, 22, '#87766a');
  text('我的专属形象方案', side, 173, 43, '#302721', 700);
  text('YOUR PERSONAL GROOMING GUIDE', side, 233, 18, '#a76535', 700);
  y = 280;

  if (beard) imageSection('胡须试戴效果', beard);
  if (hair) imageSection('发型试戴效果', hair);
  const hairline = extractHairlineLevel(result as Record<string, unknown>);
  section('面部分析', [
    `脸型：${result.faceShape ? faceShapeLabels[result.faceShape] ?? '暂未提供该脸型说明' : '暂未提供脸型数据'}`,
    `胡须密度：${result.densityLevel ? densityLevelLabels[result.densityLevel] ?? '暂未提供密度说明' : '暂未提供密度数据'}`,
    hairline && hairline in hairlineLevelLabels ? `发际线：${hairlineLevelLabels[hairline as keyof typeof hairlineLevelLabels]}` : '',
  ]);
  const styles = result.recommendedStyles ?? [];
  const hairStyle = styles.find((style) => style in hairstyleLabels);
  const beardStyle = styles.find((style) => style in beardStyleLabels);
  section('推荐造型', [hairStyle ? `推荐发型：${hairstyleLabels[hairStyle]}` : '', beardStyle ? `推荐胡须：${beardStyleLabels[beardStyle]}` : '']);
  section('产品建议', (result.productTips ?? []).map((tip) => displayApiText(tip)).filter(Boolean).map((tip) => `• ${tip}`));
  for (let i = 0; i < (result.hairRecommendations ?? []).length; i += 1) {
    const item = result.hairRecommendations![i];
    section('个性化发型推荐', [
      displayApiText(item.styleName) || '推荐发型',
      displayApiText(item.reason),
      item.difficulty !== undefined ? `难度等级：${item.difficulty}` : '',
      item.maintenance ? `打理：${displayApiText(item.maintenance)}` : '',
      item.imageUrl && !hairImages[i] ? '参考图片暂无法加入海报' : '',
    ]);
    if (hairImages[i]) imageSection('发型参考图', hairImages[i]!);
  }
  section('发型打理建议', (result.hairTips ?? []).map((tip) => displayApiText(tip)).filter(Boolean).map((tip) => `• ${tip}`));
  if (original) imageSection('胡须热力图', original, true);
  else section('胡须热力图', ['暂未提供胡须热力图数据']);
  text('decent-beard-taste  ·  让每根胡子都长得有道理', side, y + 20, 22, '#a28a75', 700);
  y += 110;

  canvas.width = width;
  canvas.height = y;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('当前浏览器无法生成海报。');
  ctx.fillStyle = '#fbf8ee'; ctx.fillRect(0, 0, width, y);
  drawings.forEach((draw) => draw(ctx));
  return new Promise((resolve, reject) => {
    try { canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error('海报保存失败，请重试。')), 'image/png'); }
    catch { reject(new Error('试戴图片暂不支持导出海报，请联系成员 4 检查图片读取权限。')); }
  });
}

export function SharePoster({ result, previewUrl, beardUrl, hairUrl, onClose }: SharePosterProps) {
  const [posterUrl, setPosterUrl] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    let createdUrl = '';
    setLoading(true);
    createPoster(result, previewUrl, beardUrl, hairUrl).then((blob) => {
      if (cancelled) return;
      createdUrl = URL.createObjectURL(blob);
      setPosterUrl(createdUrl);
    }).catch((reason: unknown) => {
      if (!cancelled) setError(reason instanceof Error ? reason.message : '海报生成失败，请重试。');
    }).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; if (createdUrl) URL.revokeObjectURL(createdUrl); };
  }, [result, previewUrl, beardUrl, hairUrl]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-950/60 p-4" role="dialog" aria-modal="true" aria-labelledby="poster-title">
      <div className="flex max-h-[92vh] w-full max-w-xl flex-col overflow-hidden rounded-3xl bg-[#fffdf7] shadow-2xl">
        <div className="flex items-center justify-between border-b border-stone-200 px-5 py-4">
          <div><h2 id="poster-title" className="text-lg font-bold text-stone-800">我的分享海报</h2><p className="mt-1 text-xs text-stone-500">预览后保存，分享你喜欢的造型</p></div>
          <button type="button" onClick={onClose} aria-label="关闭海报预览" className="rounded-full p-2 text-stone-500 hover:bg-stone-100"><X className="h-5 w-5" /></button>
        </div>
        <div className="min-h-[200px] overflow-y-auto bg-stone-100 p-4 text-center">
          {loading && <p className="py-12 text-sm text-stone-600" role="status">正在整理你的海报，请稍候…</p>}
          {error && <p className="py-12 text-sm text-red-600" role="alert">{error}</p>}
          {posterUrl && <img src={posterUrl} alt="分享海报预览" className="mx-auto h-auto w-full max-w-md rounded-lg shadow-sm" />}
        </div>
        <div className="flex gap-3 border-t border-stone-200 px-5 py-4">
          <button type="button" onClick={onClose} className="flex-1 rounded-2xl bg-stone-100 px-4 py-3 text-sm font-semibold text-stone-600">关闭</button>
          {posterUrl ? <a href={posterUrl} download="decent-beard-taste-分享海报.png" className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-amber-900 px-4 py-3 text-sm font-semibold text-white hover:bg-amber-800"><Download className="h-4 w-4" />保存海报</a> : <button type="button" disabled className="flex-1 rounded-2xl bg-stone-200 px-4 py-3 text-sm font-semibold text-stone-400">保存海报</button>}
        </div>
      </div>
    </div>
  );
}
