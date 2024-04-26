interface Props {
  children: JSX.Element | JSX.Element[]
}

export default function Slot({ children }: Props) {
  return (
    <article className="nes-container is-rounded !m-auto grid aspect-square h-full max-h-80 w-full max-w-80 content-center overflow-hidden !p-3 text-center">
      {children}
    </article>
  )
}
