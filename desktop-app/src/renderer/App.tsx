import { useEffect, useState } from "react"
import BackendStates from "./components/BackendStates"
import PokemonParty from "./components/PokemonParty"
import SelectPokemonDialog from "./components/SelectPokemonDialog"
import "./index.css"

export default function App() {
  const [isServerUp, setIsServerUp] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")

  useEffect(() => {
    if (isServerUp) return
    const intervalId = setInterval(() => {
      window.api.isServerUp().then(({ state, message }) => {
        if (state === "ok") {
          setIsServerUp(true)
        } else if (state === "loading") {
          setIsServerUp(false)
        } else {
          setErrorMessage(message)
        }
      })
    }, 1000)
    return () => clearInterval(intervalId)
  }, [isServerUp])

  if (!isServerUp) {
    return (
      <div className="m-auto grid min-h-screen w-full place-content-center">
        <img className="mx-auto my-4" src="static://assets/img/trainer.gif" />
        <p className="nes-text text-2xl">Loading...</p>
        <p className="nes-text is-error text-xl">{errorMessage}</p>
      </div>
    )
  }

  return (
    <div className="m-auto grid min-h-screen w-full max-w-sm place-content-center p-4 md:max-w-screen-lg">
      <header className="flex flex-col items-center justify-center gap-x-3 pb-6 md:flex-row">
        <img className="w-10" src="static://assets/img/pokeball.png" />
        <h1 className="text-center text-2xl font-bold">
          Pokemon Trade Spoofer
        </h1>
      </header>
      <main>
        <PokemonParty />
      </main>
      <footer className="py-4">
        <BackendStates />
      </footer>
      <aside>
        <SelectPokemonDialog />
      </aside>
    </div>
  )
}
