import type { MascotCommand } from "./types";

const actions = new Set(["moveTo", "moveToTarget", "say", "play", "pointTo", "show", "hide"]);

export function parseMascotCommand(input: unknown): MascotCommand | null {
  if (!input || typeof input !== "object") return null;
  const value = input as Record<string, unknown>;
  if (typeof value.action !== "string" || !actions.has(value.action)) return null;
  if (value.action === "say" && typeof value.text === "string") return { action: "say", text: value.text };
  if ((value.action === "moveToTarget" || value.action === "pointTo") && typeof value.target === "string") return value as MascotCommand;
  if (value.action === "moveTo" && typeof value.point === "object" && value.point !== null) return value as MascotCommand;
  if (value.action === "play" && typeof value.state === "string") return value as MascotCommand;
  if (value.action === "show" || value.action === "hide") return value as MascotCommand;
  return null;
}

export function parseMascotJson(json: string): MascotCommand | null {
  try { return parseMascotCommand(JSON.parse(json)); } catch { return null; }
}
