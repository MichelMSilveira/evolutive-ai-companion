export type AssetType = "pet" | "item" | "module" | "service";
export type AssetLicense = "private" | "cc0" | "cc-by" | "direct-permission" | "commercial-license";

export type MarketplaceAsset = {
  id: string;
  type: AssetType;
  title: string;
  description: string;
  creatorId: string;
  version: number;
  license: AssetLicense;
  contentHash: string;
  publicTraits: string[];
  privateDataIncluded: false;
  humanReviewRequired: boolean;
  createdAt: string;
  origin: "original" | "authorized-derivative" | "copy";
};

export type AssetTransfer = {
  assetId: string;
  fromOwnerId: string;
  toOwnerId: string;
  includesPrivateMemories: boolean;
  consentRecorded: boolean;
  createdAt: string;
};

export function canPublishAsset(asset: MarketplaceAsset) {
  return !asset.privateDataIncluded && asset.license !== "private" && asset.origin !== "copy";
}

export function canTransferMemories(transfer: AssetTransfer) {
  return transfer.includesPrivateMemories && transfer.consentRecorded;
}
