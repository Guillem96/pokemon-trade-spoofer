import { useBackendStates } from "../hooks/backends"
import { usePokemonStore } from "../store"
import ButtonTooltip from "./ButtonTooltip"
import Slot from "./Slot"
import { DISABLED_OPTION_TOOLTIP } from "../../common/constants"
interface Props {
  available: boolean
}

export default function EmptySlot({ available }: Props) {
  const GIF_POKEBALL = "static://assets/img/pokeball.gif"
  const PNG_POKEBALL = "static://assets/img/pokeball.png"
  const [toggleModal] = usePokemonStore((state) => [state.toggleModal])
  const { isAnyRunning } = useBackendStates()
  return (
    <Slot>
      {available ? (
        <ButtonTooltip
          text={isAnyRunning ? DISABLED_OPTION_TOOLTIP : "Select Pokemon"}
          className="nes-pointer m-auto"
          onClick={toggleModal}
        >
          <img
            className={`m-auto w-20 pb-2 ${isAnyRunning ? "opacity-60" : ""}`}
            onMouseEnter={(event) => {
              if (isAnyRunning) return
              event.currentTarget.setAttribute("src", GIF_POKEBALL)
            }}
            onMouseLeave={(event) => {
              if (isAnyRunning) return

              event.currentTarget.setAttribute("src", PNG_POKEBALL)
            }}
            src={PNG_POKEBALL}
          />
        </ButtonTooltip>
      ) : (
        <ButtonTooltip className="nes-pointer" text="Not available">
          <img className="m-auto w-20 saturate-0" src={PNG_POKEBALL} />
        </ButtonTooltip>
      )}
    </Slot>
  )
}
