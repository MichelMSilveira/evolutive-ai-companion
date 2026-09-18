export type MascotState =
  | "idle" | "walking" | "talking" | "pointing" | "thinking"
  | "happy" | "surprised" | "sleeping" | "stretching" | "sniffing" | "cuddling" | "playful" | "hidden";

export type MascotPoint = { x: number; y: number };

export type MascotCommand =
  | { action: "moveTo"; point: MascotPoint }
  | { action: "moveToTarget"; target: string }
  | { action: "say"; text: string }
  | { action: "play"; state: Exclude<MascotState, "hidden"> }
  | { action: "pointTo"; target: string }
  | { action: "show" | "hide" };
