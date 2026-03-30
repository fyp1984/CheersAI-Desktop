'use client'

import { useContext } from 'react'
import { SandboxSecurityContext } from './sandbox-security-context'

export const useSandboxSecurity = () => useContext(SandboxSecurityContext)
