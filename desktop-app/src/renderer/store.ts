import { create } from "zustand"
import { type PokeApiPokemon, SpooferState } from "./types"
import { Backends } from "../common/constants"
import { type Party } from "../common/models"

const START_BACKEND_FNS: Record<Backends, (party: Party) => Promise<boolean>> =
  {
    [Backends.BGB]: window.api.startBGBServer,
  }

const STOP_BACKEND_FNS: Record<Backends, () => Promise<boolean>> = {
  [Backends.BGB]: window.api.stopBGBServer,
}

interface State {
  trainerName: string
  party: PokeApiPokemon[]
  displayModal: boolean
  loadingAddPokemon: boolean
  backends: Record<Backends, SpooferState>
  backendMessage: string
}

interface Actions {
  setTrainerName: (name: string) => void
  addPokemonToParty: (dexId: number) => Promise<void>
  deletePartySlot: (slotIdx: number) => void
  clearParty: () => void
  fetchBackendStates: () => Promise<void>
  startBackend: (backend: Backends) => Promise<void>
  stopBackend: (backend: Backends) => Promise<void>
  toggleModal: () => void
}

export const usePokemonStore = create<State & Actions>()((set, get) => ({
  backends: {
    [Backends.BGB]: SpooferState.LOADING,
  },
  backendMessage: "",
  trainerName: "",
  party: [],
  displayModal: false,
  loadingAddPokemon: false,
  setTrainerName(name: string) {
    set({ trainerName: name })
  },
  addPokemonToParty: async (dexId) => {
    const { party } = get()
    if (party.length === 6) return

    set({ loadingAddPokemon: true })
    try {
      const res = await fetch(`https://pokeapi.co/api/v2/pokemon/${dexId}`)
      if (!res.ok) {
        // TODO: show error
        return
      }
      const pokemon = await res.json()
      set({
        party: [...party, pokemon as PokeApiPokemon],
        loadingAddPokemon: false,
      })
    } catch (err) {
      console.error(err)
    } finally {
      set({ loadingAddPokemon: false })
    }
  },
  deletePartySlot(slotIdx) {
    const { party } = get()
    if (party.length === 0) return
    set({ party: [...party.slice(0, slotIdx), ...party.slice(slotIdx + 1)] })
  },
  fetchBackendStates: async () => {
    const states = await window.api.fetchBackendStates()
    set({ backends: states })
  },
  startBackend: async (backend: Backends) => {
    const { backends, trainerName, party } = get()
    if (!(backend in backends)) return
    if (
      backends[backend] === SpooferState.RUNNING ||
      backends[backend] === SpooferState.LOADING
    )
      return

    const simplifiedParty = {
      trainerName: trainerName === "" ? "SPOOFER" : trainerName,
      pokemon: party.map((pkm) => ({
        dexId: pkm.id,
        nickname: pkm.name,
      })),
    } as Party

    console.log(`Starting ${backend} Backend with the following Pokemon party:`)
    console.log(simplifiedParty)

    set({
      backends: { ...backends, [backend]: SpooferState.LOADING },
      backendMessage: `Booting up ${backend} backend...`,
    })
    const res = await START_BACKEND_FNS[backend](simplifiedParty)
    if (res)
      set({
        backends: {
          ...backends,
          [backend]: SpooferState.RUNNING,
        },
        backendMessage: `Backend ${backend} is up`,
      })
    else {
      set({
        backends: { ...backends, [backend]: SpooferState.ERROR },
        backendMessage: `Error starting ${backend} backend`,
      })
    }
  },
  stopBackend: async (backend: Backends) => {
    const { backends } = get()
    if (!(backend in backends)) return
    if (
      backends[backend] === SpooferState.STOPPED ||
      backends[backend] === SpooferState.LOADING
    )
      return

    set({
      backends: { ...backends, [backend]: SpooferState.LOADING },
      backendMessage: `Stopping ${backend} backend...`,
    })

    const res = await STOP_BACKEND_FNS[backend]()
    if (res)
      set({
        backends: {
          ...backends,
          [backend]: SpooferState.STOPPED,
        },
        backendMessage: `Backend ${backend} stopped`,
      })
    else {
      set({
        backends: { ...backends, [backend]: SpooferState.ERROR },
        backendMessage: `Error stopping ${backend} backend`,
      })
    }
  },
  clearParty() {
    set({ party: [] })
  },
  toggleModal() {
    set({ displayModal: !get().displayModal })
  },
}))
