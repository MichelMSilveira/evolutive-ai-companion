export type CompanionModule = "study" | "personal" | "work";
export type InputKind = "conversation" | "achievement" | "routine" | "content";

export type CompanionEvent = {
  id: string;
  module: CompanionModule;
  kind: InputKind;
  summary: string;
  sensitive: boolean;
  createdAt: string;
};

export type CompanionState = {
  evolutionVersion: number;
  traits: Record<string, number>;
  localMemoryIds: string[];
  publicMilestones: string[];
};

export type LoopResult = {
  nextState: CompanionState;
  localMemory: CompanionEvent | null;
  publicMilestone: string | null;
  publishable: false;
};

const traitByModule: Record<CompanionModule, string> = { study: "curiosity", personal: "balance", work: "focus" };

export function processCompanionEvent(state: CompanionState, event: CompanionEvent): LoopResult {
  const trait = traitByModule[event.module];
  const nextState: CompanionState = {
    evolutionVersion: state.evolutionVersion + 1,
    traits: { ...state.traits, [trait]: (state.traits[trait] ?? 0) + 1 },
    localMemoryIds: [...state.localMemoryIds, event.id],
    publicMilestones: event.sensitive ? state.publicMilestones : [...state.publicMilestones, `${event.module}:${event.kind}`],
  };
  return { nextState, localMemory: event, publicMilestone: event.sensitive ? null : `${event.module}:${event.kind}`, publishable: false };
}

export function projectPublicIdentity(state: CompanionState) {
  return { evolutionVersion: state.evolutionVersion, traits: state.traits, milestones: state.publicMilestones };
}
