import { useEffect, useRef, useState } from "react";

export function KaraokePanel() {
  const modelName = import.meta.env.VITE_NOVA_MODEL || "llama3.2:3b";
  const [audioUrl, setAudioUrl] = useState("");
  const [audioName, setAudioName] = useState("");
  const [progress, setProgress] = useState(0);
  const [minimized, setMinimized] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);
  useEffect(() => () => { if (audioUrl) URL.revokeObjectURL(audioUrl); }, [audioUrl]);
  const importAudio = (file?: File) => { if (!file) return; if (audioUrl) URL.revokeObjectURL(audioUrl); setAudioUrl(URL.createObjectURL(file)); setAudioName(file.name.replace(/\.[^.]+$/, "")); setProgress(0); };
  return <section className={`karaoke-panel${minimized ? " karaoke-panel-minimized" : ""}`} aria-label="Modo de áudio"><div className="karaoke-heading"><span>Modelo local: {modelName}</span><button className="karaoke-minimize" onClick={() => setMinimized((value) => !value)} aria-label={minimized ? "Restaurar painel" : "Minimizar painel"}>{minimized ? "＋" : "−"}</button></div>{minimized ? <div className="karaoke-ticker"><b>{audioName || "Pronto"}</b><span>{audioName ? "Áudio local carregado" : "Importe um áudio para começar"}</span></div> : <><strong>{audioName || "Modelo local ativo"}</strong><span className="karaoke-artist">{modelName} · execução local</span><div className="karaoke-progress"><span style={{ width: `${progress}%` }} /></div>{audioUrl ? <audio ref={audioRef} controls src={audioUrl} onTimeUpdate={(event) => { const audio = event.currentTarget; setProgress(audio.duration ? audio.currentTime / audio.duration * 100 : 0); }} /> : <div className="karaoke-line"><b>Modelo local ativo</b><span>Importe um arquivo de áudio para começar.</span></div>}<div className="karaoke-actions"><label className="file-button">Importar áudio<input type="file" accept="audio/*" onChange={(event) => importAudio(event.target.files?.[0])} hidden /></label></div></>}</section>;
}
