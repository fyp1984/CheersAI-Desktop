type SSOSession = {
  accessToken: string
  refreshToken?: string
  scope?: string
  createdAt: number
  lastSyncedAt: number
  expiresAt: number
}

const globalForSessions = globalThis as unknown as {
  ssoSessions: Map<string, SSOSession> | undefined
}

const sessions = globalForSessions.ssoSessions ?? new Map<string, SSOSession>()

if (process.env.NODE_ENV !== 'production') {
  globalForSessions.ssoSessions = sessions
}

const cleanupInterval = setInterval(() => {
  const now = Date.now()
  let cleaned = 0
  for (const [sessionId, session] of sessions.entries()) {
    if (session.expiresAt < now) {
      sessions.delete(sessionId)
      cleaned++
    }
  }
  if (cleaned > 0) {
    console.warn(`[SSO Session] Cleaned up ${cleaned} expired sessions`)
  }
}, 5 * 60 * 1000)

if (cleanupInterval.unref) {
  cleanupInterval.unref()
}

export function generateSessionId(): string {
  return `sso_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`
}

export function storeSession(sessionId: string, accessToken: string, refreshToken?: string, expiresIn: number = 60 * 60, scope?: string): void {
  const now = Date.now()
  sessions.set(sessionId, {
    accessToken,
    refreshToken,
    scope,
    createdAt: now,
    lastSyncedAt: now,
    expiresAt: now + (expiresIn * 1000),
  })
  console.warn(`[SSO Session] Stored session ${sessionId.substring(0, 20)}... (total: ${sessions.size})`)
}

export function getSession(sessionId: string): SSOSession | null {
  const session = sessions.get(sessionId)
  if (!session) {
    console.warn(`[SSO Session] Session not found: ${sessionId.substring(0, 20)}... (total: ${sessions.size})`)
    return null
  }

  if (session.expiresAt < Date.now()) {
    sessions.delete(sessionId)
    console.warn(`[SSO Session] Session expired: ${sessionId.substring(0, 20)}...`)
    return null
  }

  console.warn(`[SSO Session] Session retrieved: ${sessionId.substring(0, 20)}...`)
  return session
}

export function updateSession(sessionId: string, partial: Partial<SSOSession>): SSOSession | null {
  const session = sessions.get(sessionId)
  if (!session)
    return null

  const nextSession = {
    ...session,
    ...partial,
  }
  sessions.set(sessionId, nextSession)
  return nextSession
}

export function shouldRefreshSession(session: SSOSession, bufferMs: number = 5 * 60 * 1000): boolean {
  return session.expiresAt <= Date.now() + bufferMs
}

export function deleteSession(sessionId: string): void {
  sessions.delete(sessionId)
  console.warn(`[SSO Session] Deleted session: ${sessionId.substring(0, 20)}...`)
}
