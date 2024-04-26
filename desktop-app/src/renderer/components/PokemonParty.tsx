import EmptySlot from "./EmptySlot"
import TrainerInput from "./TrainerInput"
import PokemonSlot from "./PokemonSlot"
import { usePokemonStore } from "../store"
import Controls from "./Controls"

export default function PokemonParty() {
  const [party, deletePartySlot] = usePokemonStore((state) => [
    state.party,
    state.deletePartySlot,
  ])
  const remainingSlots = 6 - party.length

  return (
    <section>
      <div className="flex h-14 flex-row items-center justify-between gap-x-2">
        <TrainerInput />
        <Controls />
      </div>
      <div className="nes-container is-rounded !mt-4 grid grid-cols-1 content-center gap-4 md:grid-cols-3">
        {party.map((pkmn, idx) => (
          <PokemonSlot
            key={pkmn.id}
            slotIdx={idx}
            pokemon={pkmn}
            onDeleteSlot={deletePartySlot}
          />
        ))}
        {[...Array(remainingSlots).keys()].map((o) => (
          <EmptySlot key={o} available={o === 0} />
        ))}
      </div>
    </section>
  )
}
