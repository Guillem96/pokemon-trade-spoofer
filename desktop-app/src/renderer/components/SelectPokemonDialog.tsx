import { useEffect, useRef, useState, MouseEvent } from "react"
import { POKEMON_NAMES } from "../../common/constants"
import { usePokemonStore } from "../store"

interface PokemonDialog extends HTMLDialogElement {
  close: () => void
  showModal: () => void
}

export default function SelectPokemonDialog() {
  const dialogRef = useRef<PokemonDialog | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [displayModal, loadingAddPokemon, addPokemonToParty, toggleModal] =
    usePokemonStore((state) => [
      state.displayModal,
      state.loadingAddPokemon,
      state.addPokemonToParty,
      state.toggleModal,
    ])

  useEffect(() => {
    if (displayModal) {
      dialogRef?.current?.showModal()
    } else {
      dialogRef?.current?.close()
    }
  }, [displayModal])

  const cancelSelection = (e: MouseEvent<HTMLButtonElement>) => {
    e.preventDefault()
    setError(null)
    toggleModal()
  }

  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const data = new FormData(e.currentTarget)
    const selectedPkm = data.get("selected-pkmn") ?? ""
    if (selectedPkm === "") {
      setError("No Pokemon selected")
      return
    }

    if (selectedPkm === "Pokemon ID...") {
      setError("Invalid Pokemon selected")
      return
    }

    addPokemonToParty(Number(selectedPkm)).then(toggleModal)
  }

  return (
    <dialog
      ref={dialogRef}
      className="nes-dialog is-rounded"
      id="select-pkm-dialog"
    >
      <form onSubmit={onSubmit}>
        <div className="mb-2 flex flex-row items-center">
          <img className="mr-1 w-10" src="static://assets/img/pokeball.png" />
          <p className="font-bold">Select Pokemon</p>
        </div>

        <div className="nes-select mb-2">
          <select
            name="selected-pkmn"
            defaultValue=""
            className={error ? "is-error" : ""}
            required
          >
            <option value="" disabled hidden>
              Pokemon ID...
            </option>
            {[...Array(251).keys()].map((o) => (
              <option key={o} value={o + 1}>
                {o + 1} - {POKEMON_NAMES[o]}
              </option>
            ))}
          </select>
        </div>
        {error && (
          <p className="nes-text is-error py-2 text-right text-sm">X {error}</p>
        )}
        <menu className="flex flex-row justify-end gap-2">
          <button
            className={`nes-btn ${loadingAddPokemon ? "is-disabled" : ""}`}
            disabled={loadingAddPokemon}
            onClick={cancelSelection}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loadingAddPokemon}
            className={`nes-btn is-primary ${loadingAddPokemon ? "is-disabled" : ""}`}
          >
            Confirm
          </button>
        </menu>
      </form>
    </dialog>
  )
}
