import { useCallback, useMemo, useState, type PropsWithChildren } from "react";
import { MascotContext, type MascotApi } from "./MascotContext";
import type { MascotCommand, MascotPoint, MascotState } from "./types";
import { clampPoint, sleep, targetCenter } from "./MascotController";

export function MascotProvider({ children }: PropsWithChildren) {
  const [state, setState] = useState<MascotState>("idle");
  const [position, setPosition] = useState<MascotPoint>(() => JSON.parse(localStorage.getItem("nova-mascot-position") || '{"x":32,"y":32}') as MascotPoint);
  const [speech, setSpeech] = useState<string | null>(null);
  const moveTo = useCallback(async (point: MascotPoint) => { const safePoint = clampPoint(point); setState("walking"); setPosition(safePoint); localStorage.setItem("nova-mascot-position", JSON.stringify(safePoint)); await sleep(450); setState("idle"); }, []);
  const moveToTarget = useCallback(async (target: string) => { const point = targetCenter(target); if (point) await moveTo(point); }, [moveTo]);
  const say = useCallback(async (text: string) => { setState("talking"); setSpeech(text); await sleep(Math.max(1200, text.length * 45)); setSpeech(null); setState("idle"); }, []);
  const pointTo = useCallback(async (target: string) => { await moveToTarget(target); setState("pointing"); await sleep(900); setState("idle"); }, [moveToTarget]);
  const dispatch = useCallback(async (command: MascotCommand) => { if (command.action === "moveTo") return moveTo(command.point); if (command.action === "moveToTarget") return moveToTarget(command.target); if (command.action === "say") return say(command.text); if (command.action === "play") { setState(command.state); return; } if (command.action === "pointTo") return pointTo(command.target); setState(command.action === "show" ? "idle" : "hidden"); }, [moveTo, moveToTarget, pointTo, say]);
  const runSequence = useCallback(async (commands: MascotCommand[]) => { for (const command of commands) await dispatch(command); }, [dispatch]);
  const api = useMemo<MascotApi>(() => ({ state, position, speech, moveTo, moveToTarget, say, play: setState, pointTo, show: () => setState("idle"), hide: () => setState("hidden"), dispatch, runSequence }), [state, position, speech, moveTo, moveToTarget, say, pointTo, dispatch, runSequence]);
  return <MascotContext.Provider value={api}>{children}</MascotContext.Provider>;
}
