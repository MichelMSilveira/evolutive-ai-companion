import { useMascot } from "./MascotContext";

export function MascotSpeech() {
  const { speech } = useMascot();
  return speech ? <div className="mascot-speech">{speech}</div> : null;
}
