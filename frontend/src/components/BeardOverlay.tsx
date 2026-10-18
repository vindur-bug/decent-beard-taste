// Canvas 胡须区域和热力图覆盖组件
// 在用户照片上绘制胡须区域点位和热力图

import { useEffect, useRef } from 'react';
import type { RegionPoint, HeatmapPoint } from '@/types/AnalysisResult';

// 请确认 intensity 是否也是 0 到 1
const INTENSITY_MIN = 0;
const INTENSITY_MAX = 1;

interface BeardOverlayProps {
  imageUrl: string;
  beardRegions?: RegionPoint[];
  heatmapData?: HeatmapPoint[];
}

export function BeardOverlay({ imageUrl, beardRegions, heatmapData }: BeardOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    const img = imgRef.current;
    if (!canvas || !container || !img) return;

    const drawOverlay = () => {
      const containerWidth = container.clientWidth;
      const containerHeight = container.clientHeight;
      canvas.width = containerWidth;
      canvas.height = containerHeight;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // 叠加层与 object-contain 图片保持对齐，并同时兼容 0~1 相对坐标和原图像素坐标。
      const naturalWidth = img.naturalWidth || containerWidth;
      const naturalHeight = img.naturalHeight || containerHeight;
      const imageScale = Math.min(containerWidth / naturalWidth, containerHeight / naturalHeight);
      const renderedImageWidth = naturalWidth * imageScale;
      const renderedImageHeight = naturalHeight * imageScale;
      const imageOffsetX = (containerWidth - renderedImageWidth) / 2;
      const imageOffsetY = (containerHeight - renderedImageHeight) / 2;
      const toCanvasPoint = (x: number, y: number): [number, number] => {
        const relativeX = x >= 0 && x <= 1 ? x : x / naturalWidth;
        const relativeY = y >= 0 && y <= 1 ? y : y / naturalHeight;
        return [
          imageOffsetX + relativeX * renderedImageWidth,
          imageOffsetY + relativeY * renderedImageHeight,
        ];
      };

      ctx.clearRect(0, 0, containerWidth, containerHeight);

      // 绘制热力图（如果数据存在且非空）
      // 如果 heatmapData 为空，不画假的热力图
      if (heatmapData && heatmapData.length > 0) {
        heatmapData.forEach((point) => {
          const [x, y, intensity] = point;
          const [px, py] = toCanvasPoint(x, y);
          // 请确认 intensity 是否也是 0 到 1
          const normalizedIntensity = Math.min(
            Math.max((intensity - INTENSITY_MIN) / (INTENSITY_MAX - INTENSITY_MIN), 0),
            1
          );
          const radius = 20 + normalizedIntensity * 30;
          const gradient = ctx.createRadialGradient(px, py, 0, px, py, radius);
          gradient.addColorStop(0, `rgba(255, 120, 50, ${0.6 * normalizedIntensity})`);
          gradient.addColorStop(1, 'rgba(255, 120, 50, 0)');
          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.arc(px, py, radius, 0, Math.PI * 2);
          ctx.fill();
        });
      }

      // 绘制胡须区域点位标记
      // 注意：坐标点是否按轮廓顺序排列尚未确认，暂用点位标记方式显示
      // 需要和后台成员确认点的顺序后再决定是否连成多边形
      if (beardRegions && beardRegions.length > 0) {
        beardRegions.forEach((point) => {
          const [x, y] = point;
          const [px, py] = toCanvasPoint(x, y);
          ctx.strokeStyle = 'rgba(56, 189, 248, 0.9)';
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.arc(px, py, 6, 0, Math.PI * 2);
          ctx.stroke();
          ctx.fillStyle = 'rgba(56, 189, 248, 0.3)';
          ctx.fill();
        });
      }
    };

    if (img.complete) {
      drawOverlay();
    } else {
      img.onload = drawOverlay;
    }

    // 监听容器尺寸变化，重新绘制
    const resizeObserver = new ResizeObserver(drawOverlay);
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
    };
  }, [imageUrl, beardRegions, heatmapData]);

  const hasRegions = beardRegions && beardRegions.length > 0;
  const hasHeatmap = heatmapData && heatmapData.length > 0;

  if (!hasRegions && !hasHeatmap) {
    return null;
  }

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 pointer-events-none"
      style={{ width: '100%', height: '100%' }}
    >
      {/* 隐藏的 img 用于触发加载完成事件 */}
      <img
        ref={imgRef}
        src={imageUrl}
        alt=""
        className="hidden"
      />
      <canvas ref={canvasRef} className="w-full h-full" />
    </div>
  );
}
