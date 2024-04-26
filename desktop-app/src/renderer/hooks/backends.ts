import { useMemo } from "react"
import { usePokemonStore } from "../store"
import { SpooferState } from "../types"
import { Backends } from "../../common/constants"

export const useBackendStates = () => {
  const [backends] = usePokemonStore((state) => [state.backends])

  const isAnyRunning = useMemo(
    () =>
      Object.values(backends).some(
        (bs) => bs === SpooferState.RUNNING || bs === SpooferState.LOADING,
      ),
    [backends],
  )

  const activeBackend: Backends = useMemo(() => {
    for (const bs of Object.entries(backends)) {
      if (bs[1] === SpooferState.RUNNING || bs[1] === SpooferState.LOADING)
        return bs[0] as Backends
    }
    for (const bs of Object.entries(backends)) {
      if (bs[1] === SpooferState.ERROR) return bs[0] as Backends
    }
  }, [backends])

  return { isAnyRunning, activeBackend }
}
