import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname } from 'node:path'

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

const SESSION_STORE_FILE = process.env.SSO_SESSION_STORE_FILE?.trim() || '/tmp/cheersai-desktop-sso-sessions.json'

const persistSessions = (sessions: Map<string, SSOSession>) => {
  try {
    mkdirSync(dirname(SESSION_STORE_FILE), { recursive: true })
    writeFileSync(
      SESSION_STORE_FILE,
      JSON.stringify(Array.from(sessions.entries())),
      'utf8',
    )
  }
  catch (error) {
    console.warn('[SSO Session] Failed to persist session store', error)
  }
}

const hydrateSessions = () => {
  try {
    if (!existsSync(SESSION_STORE_FILE))
      return new Map<string, SSOSession>()

    const raw = readFileSync(SESSION_STORE_FILE, 'utf8')
    if (!raw.trim())
      return new Map<string, SSOSession>()

    const entries = JSON.parse(raw) as Array<[string, SSOSession]>
    return new Map(entries)
  }
  catch (error) {
    console.warn('[SSO Session] Failed to hydrate session store', error)
    return new Map<string, SSOSession>()
  }
}

const sessions = globalForSessions.ssoSessions ?? hydrateSessions()

// Always keep a single process-wide session map so token exchange and userinfo
// routes resolve the same in-memory session during production standalone runs.
globalForSessions.ssoSessions = sessions

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
    persistSessions(sessions)
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
  persistSessions(sessions)
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
  persistSessions(sessions)
  return nextSession
}

export function shouldRefreshSession(session: SSOSession, bufferMs: number = 5 * 60 * 1000): boolean {
  return session.expiresAt <= Date.now() + bufferMs
}

export function deleteSession(sessionId: string): void {
  sessions.delete(sessionId)
  persistSessions(sessions)
  console.warn(`[SSO Session] Deleted session: ${sessionId.substring(0, 20)}...`)
}
