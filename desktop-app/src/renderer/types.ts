export interface PokeApiPokemon {
  id: number
  name: string
  sprites: {
    versions: Record<string, { gold: { front_transparent: string } }>
  }
}

export enum SpooferState {
  STOPPED,
  ERROR,
  RUNNING,
  LOADING,
}
