export const dynamicParams = false

export async function generateStaticParams() {
  return []
}

import * as React from 'react'
import Configuration from '@/app/components/app/configuration'

const IConfiguration = async () => {
  return (
    <Configuration />
  )
}

export default IConfiguration
