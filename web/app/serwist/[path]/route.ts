export const dynamic = 'force-static'

export async function GET() {
  return new Response('', { status: 404 })
}
