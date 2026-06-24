"use client";

import { memo } from "react";

interface PaperMoonMarkProps {
  size?: number;
  idSuffix: string;
  glow?: boolean;
}

export const PaperMoonMark = memo(function PaperMoonMark({
  size = 28,
  idSuffix,
  glow = false,
}: PaperMoonMarkProps) {
  const bgId = `pm-bg-${idSuffix}`;
  const shadowId = `pm-shadow-${idSuffix}`;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 28 28"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={bgId} x1="2" y1="2" x2="26" y2="26" gradientUnits="userSpaceOnUse">
          <stop stopColor="var(--papermoon-primary)" />
          <stop offset="1" stopColor="var(--papermoon-secondary)" />
        </linearGradient>
        <linearGradient id={shadowId} x1="3" y1="3" x2="25" y2="25" gradientUnits="userSpaceOnUse">
          <stop stopColor="rgba(255,255,255,0.12)" />
          <stop offset="1" stopColor="rgba(0,0,0,0.18)" />
        </linearGradient>
      </defs>

      {glow && (
        <rect
          x="3"
          y="4"
          width="22"
          height="22"
          rx="7"
          fill="var(--papermoon-accent)"
          opacity="0.28"
          style={{ filter: "blur(6px)" }}
        />
      )}

      <rect x="1" y="1" width="26" height="26" rx="8" fill={`url(#${bgId})`} />
      <rect x="1" y="1" width="26" height="26" rx="8" fill={`url(#${shadowId})`} />
      <path d="M19 1H20C23.866 1 27 4.13401 27 8V9L19 1Z" fill="var(--papermoon-accent)" opacity="0.9" />
      <path
        d="M8 6.5H14.2C17.9885 6.5 20.5 8.62742 20.5 12.05C20.5 15.4548 18.0231 17.6 14.2 17.6H11.25V22H8V6.5ZM11.25 9.2V14.95H13.9C16.266 14.95 17.2 13.9017 17.2 12.05C17.2 10.1983 16.266 9.2 13.9 9.2H11.25Z"
        fill="var(--papermoon-bg)"
      />
      <rect
        x="1.5"
        y="1.5"
        width="25"
        height="25"
        rx="7.5"
        stroke="rgba(255,255,255,0.18)"
        strokeWidth="0.75"
      />
    </svg>
  );
});
