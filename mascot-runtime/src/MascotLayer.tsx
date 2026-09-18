import { MascotCharacter } from "./MascotCharacter";
import { MascotSpeech } from "./MascotSpeech";
import { useMascot } from "./MascotContext";
import { useRef, useState } from "react";

export function MascotLayer() {
  const { position, state, moveTo } = useMascot();
  const dragging = useRef(false);
  const [size, setSize] = useState(180);
  const riveSrc = import.meta.env.VITE_NOVA_RIVE_SRC || undefined;
  return <div className={`mascot-layer ${state === "hidden" ? "is-hidden" : ""}`} style={{ transform: `translate3d(${position.x}px, ${position.y}px, 0)` }} onPointerDown={(event) => { if (event.button === 0) { dragging.current = true; event.currentTarget.setPointerCapture(event.pointerId); } }} onPointerMove={(event) => { if (dragging.current) moveTo({ x: position.x + event.movementX, y: position.y + event.movementY }); }} onPointerUp={() => { dragging.current = false; }} onWheel={(event) => { event.preventDefault(); setSize((value) => Math.max(64, Math.min(220, value + (event.deltaY < 0 ? 8 : -8)))); }}><MascotSpeech /><div className="mascot-resizable" style={{ width: size, height: size }}><MascotCharacter riveSrc={riveSrc} /></div></div>;
}
