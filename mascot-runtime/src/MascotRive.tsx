import { useRive, Layout, Fit } from "@rive-app/react-canvas";

type MascotRiveProps = {
  src: string;
  stateMachine?: string;
};

export function MascotRive({ src, stateMachine }: MascotRiveProps) {
  const { RiveComponent } = useRive({
    src,
    autoplay: true,
    stateMachines: stateMachine,
    layout: new Layout({ fit: Fit.Contain }),
  });

  return RiveComponent ? <RiveComponent /> : null;
}
