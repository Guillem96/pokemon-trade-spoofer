import { Backends } from "../../common/constants"
import { SpooferState } from "../types"
import { usePokemonStore } from "../store"
import ButtonTooltip from "./ButtonTooltip"
import { useBackendStates } from "../hooks/backends"
import { MouseEvent, useEffect, useId } from "react"

const MESSAGE_CLASS: Record<SpooferState, string> = {
  [SpooferState.ERROR]: "nes-text is-error",
  [SpooferState.LOADING]: "nes-text is-primary",
  [SpooferState.RUNNING]: "nes-text is-success",
  [SpooferState.STOPPED]: "",
}

interface BackendListItemProps {
  backendName: Backends
  backendState: SpooferState
  onRunStopClick: () => void
}

function BGBHelpDialog({ id }: { id: string }) {
  return (
    <dialog id={id} className="nes-dialog max-w-screen-md">
      <form method="dialog">
        <div className="mb-2 flex flex-row items-center">
          <img className="mr-1 w-10" src="/assets/img/pokeball.png" />
          <p className="font-bold">BGB Backend</p>
        </div>
        <div className="lists">
          <ul className="nes-list is-disc p-2">
            <li>
              Download{" "}
              <a
                onClick={(e: MouseEvent<HTMLAnchorElement>) => {
                  e.preventDefault()
                  window.api.openExternalUrl(
                    e.currentTarget.getAttribute("href"),
                  )
                }}
                className="text-blue-600 underline"
                target="_blank"
                rel="noreferrer"
                href="https://bgb.bircd.org/"
              >
                BGB emulator
              </a>
              .
            </li>
            <li>Open your GSC Pokemon game with BGB.</li>
            <li>
              Right click {">"} L<span className="underline">i</span>nk {">"}{" "}
              <span className="underline">C</span>onnect.
            </li>
            <li>
              Type <b>127.0.0.1:9999</b> and accept
            </li>
            <li>Go to the nearest Pokemon center and trade as usual!</li>
          </ul>
        </div>
        <menu className="dialog-menu text-right">
          <button className="nes-btn">Close</button>
        </menu>
      </form>
    </dialog>
  )
}

function BackendListItem({
  backendName,
  backendState,
  onRunStopClick,
}: BackendListItemProps) {
  const isRunning = backendState === SpooferState.RUNNING
  const isLoading = backendState === SpooferState.LOADING

  const { isAnyRunning } = useBackendStates()
  const dialogId = useId()

  let isRunDisabled, tooltipText
  if (isRunning) {
    isRunDisabled = false
  } else if (isLoading) {
    isRunDisabled = true
  } else {
    isRunDisabled = isAnyRunning
    tooltipText = isAnyRunning ? "Stop the running backend to run this one" : ""
  }

  return (
    <li className="flex flex-row items-center gap-x-2">
      <img
        src={`static://assets/img/pikachu.${isRunning ? "gif" : "png"}`}
        className="h-14 w-auto"
        alt=""
      />
      <ButtonTooltip
        text={tooltipText}
        disabled={isRunDisabled}
        onClick={onRunStopClick}
        className={`nes-btn w-full ${isRunning ? "is-error" : "is-warning"} ${isRunDisabled ? "is-disabled" : ""}`}
      >
        <p className="overflow-hidden text-ellipsis text-nowrap">
          {isRunning
            ? `Stop ${backendName} Backend`
            : `Run ${backendName} Backend`}
        </p>
      </ButtonTooltip>
      <ButtonTooltip
        disabled={!isRunning}
        text="Press for more info"
        className={`nes-btn text-center ${isRunning ? "" : "is-disabled"}`}
        onClick={() =>
          (document.getElementById(dialogId) as HTMLDialogElement).showModal()
        }
      >
        i
      </ButtonTooltip>
      {backendName === Backends.BGB ? <BGBHelpDialog id={dialogId} /> : null}
    </li>
  )
}

export default function BackendStates() {
  const [
    backends,
    backendMessage,
    fetchBackendStates,
    startBackend,
    stopBackend,
  ] = usePokemonStore((state) => [
    state.backends,
    state.backendMessage,
    state.fetchBackendStates,
    state.startBackend,
    state.stopBackend,
  ])

  const { activeBackend } = useBackendStates()

  useEffect(() => {
    fetchBackendStates()
  }, [])
  const handleStartStop = (backend: Backends) => () => {
    if (backends[backend] === SpooferState.LOADING) return

    if (backends[backend] === SpooferState.RUNNING) {
      stopBackend(backend).then(/* TODO */)
      return
    }

    startBackend(backend).then(/* TODO */)
  }

  return (
    <>
      <ul className="flex flex-col gap-4">
        <BackendListItem
          backendName={Backends.BGB}
          backendState={backends[Backends.BGB]}
          onRunStopClick={handleStartStop(Backends.BGB)}
        />
      </ul>
      <p
        className={`${MESSAGE_CLASS[backends[activeBackend]]} py-2 text-center`}
      >
        {backendMessage}
      </p>
    </>
  )
}
