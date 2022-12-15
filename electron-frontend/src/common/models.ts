export interface ServerInfo {
    host?: string;
    port: number;
}

export interface Pokemon {
    dexId: number;
    nickname?: string;
    IVs: number[];
    heldItemId?: number;
    OT?: number;
}

export interface Party {
    trainer: string;
    party: Pokemon[];
}