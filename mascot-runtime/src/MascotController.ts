import type { MascotPoint } from "./types";

export const sleep = (ms: number) => new Promise<void>((resolve) => window.setTimeout(resolve, ms));

export function clampPoint(point: MascotPoint, margin = 24): MascotPoint {
  return {
    x: Math.max(margin, Math.min(point.x, window.innerWidth - margin)),
    y: Math.max(margin, Math.min(point.y, window.innerHeight - margin)),
  };
}

export function targetCenter(target: string): MascotPoint | null {
  const element = document.querySelector<HTMLElement>(`[data-mascot-target="${CSS.escape(target)}"]`);
  if (!element) return null;
  const rect = element.getBoundingClientRect();
  return clampPoint({ x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 });
}
