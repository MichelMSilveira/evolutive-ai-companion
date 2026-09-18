import { MascotLayer } from "./MascotLayer";
import { MascotProvider } from "./MascotProvider";
import { useEffect, useRef, useState } from "react";
import { useMascot } from "./MascotContext";
import { exchangeSpotifyCode } from "./spotifyAuth";
import { KaraokePanel } from "./KaraokePanel";

function DemoControls() {
  const mascot = useMascot();
  const nudge = (dx: number, dy: number) => mascot.moveTo({ x: mascot.position.x + dx, y: mascot.position.y + dy });
  const wander = () => mascot.runSequence([{ action: "moveTo", point: { x: 80, y: 100 } }, { action: "moveTo", point: { x: window.innerWidth - 160, y: 100 } }, { action: "moveTo", point: { x: window.innerWidth - 160, y: window.innerHeight - 180 } }, { action: "moveTo", point: { x: 80, y: window.innerHeight - 180 } }]);
  return <main><h1>Nova Mascot Runtime</h1><p>Placeholder técnico para validar movimento e comandos antes do personagem Rive.</p><p className="status">Estado: <strong>{mascot.state}</strong> · posição: {Math.round(mascot.position.x)}, {Math.round(mascot.position.y)}</p><button data-mascot-target="english-input" onClick={() => mascot.say("Vamos praticar inglês?")}>Falar</button><input data-mascot-target="english-input" placeholder="Destino de teste" /><button onClick={() => mascot.moveToTarget("english-input")}>Mover até o campo</button><button onClick={() => mascot.runSequence([{ action: "moveToTarget", target: "english-input" }, { action: "say", text: "Escreva uma frase aqui." }, { action: "pointTo", target: "english-input" }])}>Executar sequência</button><div className="direction-pad"><button onClick={() => nudge(0, -80)}>↑</button><button onClick={() => nudge(-80, 0)}>←</button><button onClick={() => nudge(80, 0)}>→</button><button onClick={() => nudge(0, 80)}>↓</button></div><button onClick={wander}>Passear</button><div><button onClick={() => mascot.play("stretching")}>Espreguiçar</button><button onClick={() => mascot.play("sniffing")}>Farejar</button><button onClick={() => mascot.play("cuddling")}>Aconchegar</button><button onClick={() => mascot.play("playful")}>Brincar</button></div><button onClick={() => mascot.play("thinking")}>Pensar</button><button onClick={() => mascot.play("happy")}>Feliz</button><button onClick={mascot.hide}>Ocultar</button><button onClick={mascot.show}>Mostrar</button></main>;
}

function SpotifyCallback() {
  const [status, setStatus] = useState("Conectando ao Spotify...");
  const started = useRef(false);
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const oauthError = params.get("error");
    if (oauthError) { setStatus(`Spotify recusou a autorização: ${oauthError}`); return; }
    if (!code) { setStatus("Código de autorização não encontrado."); return; }
    exchangeSpotifyCode(code).then((token) => {
      localStorage.setItem("nova-spotify-access-token", token.access_token);
      window.history.replaceState({}, "", "/");
      setStatus("Spotify conectado!");
    }).catch((error) => {
      const message = error instanceof Error ? error.message : "erro desconhecido";
      localStorage.removeItem("nova-spotify-code-verifier");
      setStatus(`Não foi possível concluir a conexão: ${message}. Volte para o início e clique em Reconectar.`);
    });
  }, []);
  return <p className="spotify-status">{status}</p>;
}

export function App() { const callback = window.location.pathname === "/callback"; return <MascotProvider>{callback ? <SpotifyCallback /> : <><DemoControls /><KaraokePanel /><MascotLayer /></>}</MascotProvider>; }
