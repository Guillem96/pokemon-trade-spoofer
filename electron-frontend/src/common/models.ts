export interface Pokemon {
    dexId: number;
    nickname: string;
    IVs?: number[];
    heldItemId?: number;
}

export interface Party {
    trainerName: string;
    pokemon: Pokemon[];
}
