import { DISABLED_OPTION_TOOLTIP } from "../../common/constants"
import { useBackendStates } from "../hooks/backends"
import ButtonTooltip from "./ButtonTooltip"

export default function Controls() {
  const { isAnyRunning } = useBackendStates()

  const openHelpDialog = () => {
    const $dialog = document.getElementById("help-dialog") as HTMLDialogElement
    $dialog.showModal()
  }

  return (
    <section className="flex max-h-14 flex-row gap-x-2">
      <ButtonTooltip
        text="Help"
        onClick={openHelpDialog}
        className="nes-btn is-success h-full"
      >
        i<span className="hidden md:inline md:pl-1">Help</span>
      </ButtonTooltip>
      <ButtonTooltip
        text={isAnyRunning ? DISABLED_OPTION_TOOLTIP : "Clear party"}
        className={`nes-btn is-error h-full ${isAnyRunning ? "is-disabled" : ""}`}
      >
        X<span className="hidden md:inline md:pl-1">Clear</span>
      </ButtonTooltip>

      <dialog className="nes-dialog max-w-screen-md" id="help-dialog">
        <form method="dialog">
          <div className="mb-2 flex flex-row items-center">
            <img className="mr-1 w-10" src="static://assets/img/pokeball.png" />
            <p className="font-bold">Trade Spoofer Help</p>
          </div>
          <div className="lists">
            <ul className="nes-list is-disc p-2">
              <li>Enter your trainer name, defaults to SPOOFER.</li>
              <li>
                Click the
                <img
                  className="inline h-6 w-auto px-1"
                  src="static://assets/img/pokeball.png"
                />
                to add the Pokemon you want to transfer.
              </li>
              <li>
                Start your preferred transfer method (BGB or original link
                cable).
              </li>
              <li>Trade!</li>
            </ul>
          </div>
          <menu className="dialog-menu text-right">
            <button className="nes-btn">Close</button>
          </menu>
        </form>
      </dialog>
    </section>
  )
}
