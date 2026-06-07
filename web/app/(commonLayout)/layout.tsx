import type { ReactNode } from 'react'
import * as React from 'react'
import { AppInitializer } from '@/app/components/app-initializer'
import AmplitudeProvider from '@/app/components/base/amplitude'
import GA, { GaType } from '@/app/components/base/ga'
import Zendesk from '@/app/components/base/zendesk'
import { AppContextProvider } from '@/context/app-context'
import { EventEmitterContextProvider } from '@/context/event-emitter'
import { ModalContextProvider } from '@/context/modal-context'
import { ProviderContextProvider } from '@/context/provider-context'
import { WorkspaceProvider } from '@/context/workspace-context'
import DesktopPrimaryTabs from '../components/header/desktop-primary-tabs'
import LazyClientChrome from './lazy-client-chrome'

const Layout = ({ children }: { children: ReactNode }) => {
  return (
    <>
      <GA gaType={GaType.admin} />
      <AmplitudeProvider />
      <AppInitializer>
        <AppContextProvider>
          <WorkspaceProvider>
            <EventEmitterContextProvider>
              <ProviderContextProvider>
                <ModalContextProvider>
                  <div className="flex h-screen min-w-0 flex-col bg-background-body">
                    <DesktopPrimaryTabs />
                    <main className="flex min-h-0 flex-1 min-w-0 flex-col overflow-hidden">
                      {children}
                    </main>
                  </div>
                  <LazyClientChrome />
                </ModalContextProvider>
              </ProviderContextProvider>
            </EventEmitterContextProvider>
          </WorkspaceProvider>
        </AppContextProvider>
        <Zendesk />
      </AppInitializer>
    </>
  )
}
export default Layout
