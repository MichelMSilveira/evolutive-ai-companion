export const mascotConfig = {
  name: "Nova",
  visualIdentity: "../visual-identity.json",
  rive: {
    src: "/assets/nova.riv",
    artboard: "Nova",
    stateMachine: "Nova",
  },
  motion: {
    reducedMotion: "prefers-reduced-motion",
    defaultDurationMs: 450,
  },
} as const;
