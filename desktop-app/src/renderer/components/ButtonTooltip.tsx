import { MouseEvent, useRef, useState } from "react"

type Children = JSX.Element | string
interface Props {
  text?: string
  children: Children | Children[]
  disabled?: boolean
}

export default function ButtonTooltip({
  text = "",
  children,
  disabled = false,
  ...rest
}: Props & React.HTMLAttributes<HTMLOrSVGElement>) {
  if (text === "")
    return (
      <button {...rest} disabled={disabled}>
        {children}
      </button>
    )

  const [showTooltip, setShowTooltip] = useState(false)
  const timeout = useRef<number | null>(null)
  const tooltip = useRef<HTMLDivElement | null>(null)

  const handleMouseEnter = () => {
    if (timeout.current != null) clearTimeout(timeout.current)
    timeout.current = window.setTimeout(() => {
      setShowTooltip(true)
    }, 500)
  }

  const handleMouseLeave = () => {
    if (timeout.current != null) clearTimeout(timeout.current)
    setShowTooltip(false)
  }

  const handleMouseMove = (event: MouseEvent<HTMLElement>) => {
    const { clientX, clientY, currentTarget } = event
    const rect = currentTarget.getBoundingClientRect()
    if (
      clientY > rect.top &&
      clientY < rect.bottom &&
      clientX > rect.left &&
      clientX < rect.right
    ) {
      tooltip.current.style.top = `${clientY}px`
      tooltip.current.style.left = `${clientX}px`
    }
  }

  const handleOnClick = (e: MouseEvent<HTMLButtonElement>) => {
    e.preventDefault()
    if (disabled) return
    rest.onClick && rest.onClick(e)
  }

  const tooltipClasses = [
    showTooltip ? "fixed" : "hidden",
    "nes-container z-50 pointer-events-none max-w-48 rounded-md bg-[#212529] bg-opacity-90 p-2 text-sm text-white",
  ]

  return (
    <>
      <button
        {...rest}
        onClick={handleOnClick}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onMouseMove={handleMouseMove}
      >
        {children}
      </button>
      <div ref={tooltip} className={tooltipClasses.join(" ")}>
        {text}
      </div>
    </>
  )
}
