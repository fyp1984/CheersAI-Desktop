import type { PluginStatus } from '../../types'
import { checkTaskStatus as fetchCheckTaskStatus } from '@/service/plugins'
import { sleep } from '@/utils'
import { TaskStatus } from '../../types'

const INTERVAL = 10 * 1000 // 10 seconds
const MAX_CHECK_DURATION = 5 * 60 * 1000

type Params = {
  taskId: string
  pluginUniqueIdentifier: string
}

function checkTaskStatus() {
  let nextStatus = TaskStatus.running
  let isStop = false
  const startedAt = Date.now()

  const doCheckStatus = async ({
    taskId,
    pluginUniqueIdentifier,
  }: Params) => {
    if (isStop) {
      return {
        status: TaskStatus.success,
      }
    }
    const res = await fetchCheckTaskStatus(taskId)
    const { plugins } = res.task
    const plugin = plugins.find((p: PluginStatus) => p.plugin_unique_identifier === pluginUniqueIdentifier)
    if (!plugin) {
      nextStatus = TaskStatus.failed
      return {
        status: TaskStatus.failed,
        error: 'Plugin package not found',
      }
    }
    nextStatus = plugin.status
    if (nextStatus === TaskStatus.running) {
      if (Date.now() - startedAt >= MAX_CHECK_DURATION) {
        nextStatus = TaskStatus.failed
        return {
          status: TaskStatus.failed,
          error: 'Plugin installation timed out',
        }
      }
      await sleep(INTERVAL)
      return await doCheckStatus({
        taskId,
        pluginUniqueIdentifier,
      })
    }
    if (nextStatus === TaskStatus.failed) {
      return {
        status: TaskStatus.failed,
        error: plugin.message,
      }
    }
    return ({
      status: TaskStatus.success,
    })
  }

  return {
    check: doCheckStatus,
    stop: () => {
      isStop = true
    },
  }
}

export default checkTaskStatus
