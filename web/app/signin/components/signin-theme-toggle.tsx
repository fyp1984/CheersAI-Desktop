'use client'

import { RiMoonClearLine, RiSunLine } from '@remixicon/react'
import { useEffect, useReducer, useRef } from 'react'
import useTheme from '@/hooks/use-theme'
import { Theme } from '@/types/app'

const SignInThemeToggle = () => {
  const { setTheme, theme } = useTheme()
  const mountedRef = useRef(false)
  const [, rerender] = useReducer((value: number) => value + 1, 0)

  useEffect(() => {
    mountedRef.current = true
    rerender()
  }, [])

  const nextTheme = theme === Theme.dark ? Theme.light : Theme.dark
  const label = theme === Theme.dark ? '切换到浅色模式' : '切换到深色模式'
  const isMounted = mountedRef.current

  return (
    <button
      type="button"
      className="signin-theme-toggle"
      onClick={() => setTheme(nextTheme)}
      aria-label={label}
      disabled={!isMounted}
    >
      {theme === Theme.dark
        ? <RiSunLine className="signin-theme-toggle__icon" />
        : <RiMoonClearLine className="signin-theme-toggle__icon" />}
      <span className="signin-theme-toggle__text">{isMounted ? label : '主题切换'}</span>
    </button>
  )
}

export default SignInThemeToggle
