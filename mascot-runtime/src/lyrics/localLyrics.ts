import type { LyricDocument } from "./types";

/**
 * Conteúdo de laboratório: substitua por letra própria ou autorizada.
 * O repositório não deve armazenar letras comerciais sem licença.
 */
export const localPracticeLyrics: LyricDocument = {
  id: "nova-practice-01",
  title: "Nova Practice Session",
  artist: "Conteúdo de laboratório",
  source: "local",
  licenseNote: "Texto original criado para teste acadêmico e demonstração.",
  lines: [
    { atMs: 0, text: "Hello, welcome to our practice session.", translation: "Olá, bem-vindo à nossa sessão de prática." },
    { atMs: 4000, text: "We learn one sentence at a time.", translation: "Nós aprendemos uma frase de cada vez." },
    { atMs: 8000, text: "Nova helps you speak with confidence.", translation: "Nova ajuda você a falar com confiança." },
  ],
};

export function getCurrentLyricLine(document: LyricDocument, positionMs: number) {
  return document.lines.reduce((current, line) => line.atMs <= positionMs ? line : current, document.lines[0]);
}

export function parseLrc(text: string, id = "imported-lrc"): LyricDocument {
  const lines = text.split(/\r?\n/).flatMap((raw) => {
    const match = raw.match(/^\[(\d{1,2}):(\d{2})(?:[.:](\d{1,3}))?\]\s*(.*)$/);
    if (!match) return [];
    const fraction = (match[3] ?? "0").padEnd(3, "0").slice(0, 3);
    return [{ atMs: (Number(match[1]) * 60 + Number(match[2])) * 1000 + Number(fraction), text: match[4].trim() }];
  }).filter((line) => line.text.length > 0).sort((a, b) => a.atMs - b.atMs);
  return { id, title: id, source: "local", licenseNote: "Arquivo importado pelo usuário.", lines };
}
