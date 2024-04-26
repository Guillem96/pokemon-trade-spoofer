import { DISABLED_OPTION_TOOLTIP } from "../../common/constants"
import { useBackendStates } from "../hooks/backends"
import type { PokeApiPokemon } from "../types"
import ButtonTooltip from "./ButtonTooltip"
import Slot from "./Slot"

interface Props {
  slotIdx?: number
  pokemon: PokeApiPokemon
  onDeleteSlot: (slotIdx: number) => void
}

export default function PokemonSlot({
  pokemon,
  slotIdx = 0,
  onDeleteSlot,
}: Props) {
  const handleDelete = () => onDeleteSlot(slotIdx)
  const { isAnyRunning } = useBackendStates()
  const removeTooltip = isAnyRunning ? DISABLED_OPTION_TOOLTIP : "Remove"

  return (
    <Slot>
      {/* <div className="flex w-full flex-row justify-end align-bottom"></div> */}
      <div className="text-center">
        <h2 className="uppercase">{pokemon.name}</h2>
        <h3>#{pokemon.id}</h3>
      </div>

      <img
        src={pokemon.sprites.versions["generation-ii"].gold.front_transparent}
        className="m-auto"
      />

      <ButtonTooltip
        text={removeTooltip}
        disabled={isAnyRunning}
        onClick={handleDelete}
        className={`nes-btn is-error w-full text-sm ${isAnyRunning ? "is-disabled" : ""}`}
      >
        X
      </ButtonTooltip>
    </Slot>
  )
}
