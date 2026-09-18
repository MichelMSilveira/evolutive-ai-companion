import type { LyricDocument } from "./types";
import { localPracticeLyrics } from "./localLyrics";

export type AuthorizedTrack = LyricDocument & {
  genre: string;
  language: string;
  permissions: {
    playback: boolean;
    lyricsDisplay: boolean;
    translation: boolean;
    synchronization: boolean;
  };
};

export const authorizedCatalog: AuthorizedTrack[] = [{
  ...localPracticeLyrics,
  genre: "English practice",
  language: "English",
  permissions: { playback: true, lyricsDisplay: true, translation: true, synchronization: true },
}];

export function isKaraokeReady(track: AuthorizedTrack) {
  return Object.values(track.permissions).every(Boolean);
}
