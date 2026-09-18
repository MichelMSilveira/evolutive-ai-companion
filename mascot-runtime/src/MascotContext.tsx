import { createContext, useContext } from "react";
import type { MascotCommand, MascotPoint, MascotState } from "./types";

export type MascotApi = {
  state: MascotState;
  position: MascotPoint;
  speech: string | null;
  moveTo: (point: MascotPoint) => Promise<void>;
  moveToTarget: (target: string) => Promise<void>;
  say: (text: string) => Promise<void>;
  play: (state: Exclude<MascotState, "hidden">) => void;
  pointTo: (target: string) => Promise<void>;
  show: () => void;
  hide: () => void;
  dispatch: (command: MascotCommand) => Promise<void>;
  runSequence: (commands: MascotCommand[]) => Promise<void>;
};

export const MascotContext = createContext<MascotApi | null>(null);

export function useMascot(): MascotApi {
  const value = useContext(MascotContext);
  if (!value) throw new Error("useMascot must be used inside MascotProvider");
  return value;
}
