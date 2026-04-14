'use client'

import {
  RiCompass3Line,
  RiCustomerService2Line,
  RiShieldCheckLine,
} from '@remixicon/react'
import Link from 'next/link'

const SideNav = () => {
  return (
    <div
      className="flex h-full w-[92px] shrink-0 flex-col bg-[#111827] text-white"
    >
      <div className="flex shrink-0 flex-col items-center gap-4 border-b border-white/10 px-3 py-5"
      >
        <Link href="/apps" className="flex flex-col items-center gap-3">
          <div className="h-12 w-12 shrink-0 overflow-hidden rounded-2xl border border-white/20 shadow-[0_8px_20px_rgba(37,99,235,0.25)]">
            <img
              src={`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/logo/CheersAI.png`}
              alt="CheersAI"
              className="h-full w-full scale-125 object-cover"
            />
          </div>
          <div className="text-center leading-tight">
            <div className="text-[11px] font-semibold tracking-[0.18em] text-white/95">CHEERSAI</div>
            <div className="mt-1 text-[10px] text-white/45">Desktop</div>
          </div>
        </Link>
      </div>

      <div className="flex flex-1 flex-col items-center gap-3 px-3 py-5">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/5 text-white/80">
          <RiCompass3Line className="h-5 w-5" />
        </div>
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/5 text-white/80">
          <RiShieldCheckLine className="h-5 w-5" />
        </div>
        <div className="mt-2 max-w-[52px] text-center text-[10px] leading-4 text-white/40">
          一级模块已迁移到顶部标签
        </div>
      </div>

      <div className="flex shrink-0 flex-col items-center gap-3 border-t border-white/10 px-3 py-4">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/5 text-white/80">
          <RiCustomerService2Line className="h-5 w-5" />
        </div>
        <div className="max-w-[52px] text-center text-[10px] leading-4 text-white/40">
          在线客服保留
        </div>
      </div>
    </div>
  )
}

export default SideNav
