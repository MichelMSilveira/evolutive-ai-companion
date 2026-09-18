export type TimedLyricLine = {
  atMs: number;
  text: string;
  translation?: string;
};

export type LyricDocument = {
  id: string;
  title: string;
  artist?: string;
  source: "local" | "licensed";
  licenseNote: string;
  lines: TimedLyricLine[];
};

export type KaraokePackage = {
  audioFile: File;
  lyrics: LyricDocument;
  translation?: LyricDocument;
};
