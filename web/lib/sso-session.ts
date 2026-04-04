// Simple in-memory session store for SSO tokens
// In production, use Redis or database

interface SSOSession {
  accessToken: string
  refreshToken?: string
  createdAt: number
  expiresAt: number
}

// Use globalThis to persist sessions across hot reloads in development
const globalForSessions = globalThis as unknown as {
  ssoSessions: Map<string, SSOSession> | undefined
}

const sessions = globalForSessions.ssoSessions ?? new Map<string, SSOSession>()

if (process.env.NODE_ENV !== 'production') {
  globalForSessions.ssoSessions = sessions
}

// Clean up expired sessions every 5 minutes
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
    console.log(`[SSO Session] Cleaned up ${cleaned} expired sessions`)
  }
}, 5 * 60 * 1000)

// Prevent the interval from keeping the process alive
if (cleanupInterval.unref) {
  cleanupInterval.unref()
}

export function generateSessionId(): string {
  return `sso_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`
}

export function storeSession(sessionId: string, accessToken: string, refreshToken?: string, expiresIn: number = 7 * 24 * 60 * 60): void {
  const now = Date.now()
  sessions.set(sessionId, {
    accessToken,
    refreshToken,
    createdAt: now,
    expiresAt: now + (expiresIn * 1000),
  })
  console.log(`[SSO Session] Stored session ${sessionId.substring(0, 20)}... (total: ${sessions.size})`)
}

export function getSession(sessionId: string): SSOSession | null {
  const session = sessions.get(sessionId)
  if (!session) {
    console.log(`[SSO Session] Session not found: ${sessionId.substring(0, 20)}... (total: ${sessions.size})`)
    return null
  }
  
  // Check if expired
  if (session.expiresAt < Date.now()) {
    sessions.delete(sessionId)
    console.log(`[SSO Session] Session expired: ${sessionId.substring(0, 20)}...`)
    return null
  }
  
  console.log(`[SSO Session] Session retrieved: ${sessionId.substring(0, 20)}...`)
  return session
}

export function deleteSession(sessionId: string): void {
  sessions.delete(sessionId)
  console.log(`[SSO Session] Deleted session: ${sessionId.substring(0, 20)}...`)
}
