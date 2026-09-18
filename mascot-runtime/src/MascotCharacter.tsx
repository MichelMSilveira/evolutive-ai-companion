import { useMascot } from "./MascotContext";
import { MascotRive } from "./MascotRive";
import { mascotConfig } from "./mascot.config";
import { Nova3D } from "./Nova3D";

type MascotCharacterProps = { riveSrc?: string };

export function MascotCharacter({ riveSrc }: MascotCharacterProps) {
  const { state } = useMascot();
  const templateSrc = import.meta.env.VITE_NOVA_TEMPLATE_SRC || "/nova-placeholder.png";
  return <div className={`mascot-character mascot-${state}`} aria-label={`Nova: ${state}`} role="img">
    {riveSrc ? <MascotRive src={riveSrc} stateMachine={mascotConfig.rive.stateMachine} /> : import.meta.env.VITE_NOVA_2D === "true" ? <img className="mascot-placeholder" src={templateSrc} alt="Nova" /> : <Nova3D />}
  </div>;
}
