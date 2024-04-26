import { useBackendStates } from "../hooks/backends"
import { usePokemonStore } from "../store"

export default function TrainerInput() {
  const [trainerName, setTrainerName] = usePokemonStore((state) => [
    state.trainerName,
    state.setTrainerName,
  ])

  const { isAnyRunning } = useBackendStates()
  return (
    <article className="flex h-10 flex-row items-center gap-x-2">
      <img className="h-10 w-auto" src="static://assets/img/trainer.gif" />
      <input
        disabled={isAnyRunning}
        type="text"
        name="trainer"
        className="nes-input w-full"
        placeholder="Trainer name"
        maxLength={10}
        value={trainerName}
        onChange={(e) => setTrainerName(e.target.value)}
        required
      />
    </article>
  )
}
