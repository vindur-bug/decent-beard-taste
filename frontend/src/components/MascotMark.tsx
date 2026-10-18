import { useId } from 'react';
import brandImage from '@/assets/decent-beard-taste.png';

interface MascotMarkProps {
  className?: string;
}

/** Crops the mascot from the supplied poster for use as a light brand accent. */
export function MascotMark({ className = '' }: MascotMarkProps) {
  const clipId = useId().replace(/:/g, '');

  return (
    <svg
      role="img"
      aria-label="decent-beard-taste 黑猫吉祥物"
      viewBox="140 35 990 900"
      className={className}
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <clipPath id={clipId}>
          <rect x="140" y="35" width="990" height="900" rx="150" />
        </clipPath>
      </defs>
      <image href={brandImage} x="0" y="0" width="1248" height="1248" clipPath={`url(#${clipId})`} />
    </svg>
  );
}
