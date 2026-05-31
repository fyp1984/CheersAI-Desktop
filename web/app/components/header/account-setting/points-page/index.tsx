'use client'

import {
  RiCalendarCheckLine,
  RiCheckboxCircleFill,
  RiCopperCoinLine,
  RiExchangeDollarLine,
  RiGiftLine,
  RiHistoryLine,
  RiSparklingFill,
} from '@remixicon/react'
import dayjs from 'dayjs'
import { useMemo, useState } from 'react'
import Button from '@/app/components/base/button'
import Modal from '@/app/components/base/modal'
import Toast from '@/app/components/base/toast'
import { useAccountPoints, useCheckInAccountPoints, useRedeemAccountPoints } from '@/service/use-common'
import { cn } from '@/utils/classnames'

const formatInteger = (value: number) => Intl.NumberFormat().format(value || 0)

const formatTime = (value: number | null) => {
  if (!value)
    return '-'
  return dayjs(value * 1000).format('YYYY-MM-DD HH:mm')
}

const sourceLabel: Record<string, string> = {
  daily_check_in: '每日签到',
  invite_code: '邀请奖励',
  redemption: '权益兑换',
  expiration: '过期清算',
}

const PointsPage = () => {
  const { data, isLoading } = useAccountPoints()
  const { mutateAsync: redeem, isPending } = useRedeemAccountPoints()
  const { mutateAsync: checkIn, isPending: isCheckingIn } = useCheckInAccountPoints()
  const [selectedDate, setSelectedDate] = useState('')
  const balance = data?.balance || 0
  const rewards = data?.rewards || []
  const transactions = data?.transactions || []
  const redemptions = data?.redemptions || []
  const checkInState = data?.check_in
  const expiration = data?.expiration
  const calendar = data?.calendar
  const selectedCalendarDate = selectedDate || calendar?.today || ''
  const selectedDay = useMemo(() => {
    return calendar?.days.find(day => day.date === selectedCalendarDate) || calendar?.days.find(day => day.is_today) || calendar?.days[0]
  }, [calendar?.days, selectedCalendarDate])
  const calendarCells = useMemo(() => {
    const prefix = Array.from({ length: calendar?.month_start_weekday || 0 }, (_, index) => ({ id: `blank-${index}` }))
    return [...prefix, ...(calendar?.days || [])]
  }, [calendar])
  const checkedDays = calendar?.days.filter(day => day.is_checked_in).length || 0

  const handleRedeem = async (rewardId: string) => {
    try {
      await redeem({ reward_id: rewardId })
      Toast.notify({ type: 'success', message: '兑换成功，权益已进入待激活状态' })
    }
    catch (error) {
      console.error(error)
    }
  }

  const handleCalendarDayClick = async (date: string) => {
    const isToday = calendar?.today === date
    if (isToday && !checkInState?.checked_today && checkInState?.today_points && !isCheckingIn) {
      try {
        await checkIn()
        Toast.notify({ type: 'success', message: '签到成功，积分已到账' })
      }
      catch (error) {
        console.error(error)
      }
      return
    }
    setSelectedDate(date)
  }

  if (isLoading)
    return <div className="system-sm-regular text-text-tertiary">正在加载积分权益...</div>

  return (
    <div className="space-y-4">
      <div className="rounded-3xl border border-divider-regular bg-gradient-to-r from-components-panel-bg to-background-section-burn p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="system-xs-medium-uppercase text-text-tertiary">当前积分</div>
            <div className="mt-3 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-state-accent-solid text-text-primary-on-surface">
                <RiCopperCoinLine className="h-6 w-6" />
              </div>
              <div className="title-4xl-semi-bold text-text-primary">{formatInteger(balance)}</div>
            </div>
            <div className="system-sm-regular mt-3 text-text-secondary">
              每成功邀请 1 位新用户注册，你将获得
              {' '}
              <span className="system-sm-semibold text-text-primary">{data?.invite_reward_points || 0}</span>
              {' '}
              积分。邀请码使用后会失效。
            </div>
          </div>
          <div className="rounded-2xl border border-divider-subtle bg-background-section-burn p-4 text-right">
            <div className="system-xs-medium-uppercase text-text-tertiary">可兑换权益</div>
            <div className="title-2xl-semi-bold mt-2 text-text-primary">{rewards.length}</div>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-divider-regular bg-components-panel-bg p-4 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <RiCalendarCheckLine className="h-5 w-5 text-state-accent-solid" />
            <div>
              <div className="system-md-semibold text-text-primary">签到日历</div>
              <div className="system-xs-regular mt-1 text-text-tertiary">
                {calendar?.year}
                年
                {calendar?.month}
                月 · 点击日期查看明细，点击今天完成签到
              </div>
            </div>
          </div>
          <div
            className={cn(
              'system-sm-semibold inline-flex items-center gap-2 rounded-full border px-3 py-1.5',
              checkInState?.checked_today
                ? 'border-green-200 bg-green-50 text-green-700'
                : 'border-state-accent-solid/20 bg-state-accent-hover text-text-accent',
            )}
          >
            <span
              className={cn(
                'h-2 w-2 rounded-full',
                checkInState?.checked_today ? 'bg-green-500' : 'bg-state-accent-solid',
              )}
            />
            {checkInState?.checked_today
              ? '今日已签到'
              : `今日未签到 · 可领 ${formatInteger(checkInState?.today_points || 0)} 分`}
          </div>
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-[420px_1fr]">
          <div className="rounded-2xl border border-divider-subtle bg-background-section-burn p-3">
            <div className="grid grid-cols-7 gap-1.5">
              {['一', '二', '三', '四', '五', '六', '日'].map(weekday => (
                <div key={weekday} className="system-xs-semibold pb-1 text-center text-text-tertiary">
                  {weekday}
                </div>
              ))}
              {calendarCells.map((cell, index) => {
                if (!('date' in cell))
                  return <div key={cell.id} />

                const isPastOrToday = calendar?.today ? !dayjs(cell.date).isAfter(dayjs(calendar.today), 'day') : false
                const isTodayPending = cell.is_today && !cell.is_checked_in
                const isMissed = isPastOrToday && !cell.is_checked_in && !isTodayPending
                const hasPoints = cell.earned_points > 0 || cell.spent_points > 0 || cell.expired_points > 0
                return (
                  <button
                    key={cell.date}
                    type="button"
                    className={cn(
                      'group relative flex h-10 items-center justify-center rounded-xl border text-center transition-all duration-200',
                      'hover:-translate-y-0.5 hover:shadow-md active:translate-y-0',
                      cell.is_checked_in && 'border-green-200 bg-green-50 text-green-700',
                      isTodayPending && 'border-state-accent-solid/30 bg-state-accent-hover text-text-accent',
                      isMissed && 'border-red-100 bg-red-50/60 text-red-500',
                      !cell.is_checked_in && !isMissed && !isTodayPending && 'border-divider-subtle bg-components-panel-bg text-text-tertiary',
                      cell.is_today && 'ring-state-accent-solid/30 ring-2',
                    )}
                    style={{ animationDelay: `${Math.min(index, 12) * 18}ms` }}
                    onClick={() => handleCalendarDayClick(cell.date)}
                  >
                    <span className="system-sm-semibold">{cell.day}</span>
                    {cell.is_checked_in && (
                      <RiCheckboxCircleFill className="ml-0.5 h-3.5 w-3.5 text-green-600 transition-transform duration-200 group-hover:scale-110" />
                    )}
                    {(isMissed || isTodayPending) && (
                      <span className={cn(
                        'absolute bottom-1 h-0.5 w-4 rounded-full',
                        isTodayPending ? 'bg-state-accent-solid' : 'bg-red-300',
                      )}
                      />
                    )}
                    {hasPoints && (
                      <span className={cn(
                        'absolute right-1 top-1 h-1.5 w-1.5 rounded-full',
                        cell.net_points >= 0 ? 'bg-green-500' : 'bg-red-400',
                      )}
                      />
                    )}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl bg-background-section-burn p-4">
              <div className="system-xs-medium-uppercase text-text-tertiary">签到状态</div>
              <div className="system-sm-regular mt-2 text-text-secondary">
                已连续
                {' '}
                <span className="system-md-semibold text-text-primary">{checkInState?.streak_days || 0}</span>
                {' '}
                天，本月已签
                {' '}
                <span className="system-md-semibold text-text-primary">{checkedDays}</span>
                {' '}
                天。
              </div>
              <div className="system-xs-regular mt-3 text-text-tertiary">
                {checkInState?.checked_today
                  ? '今天已经签到完成。'
                  : `点击今天日期即可领取 ${formatInteger(checkInState?.today_points || 0)} 分。`}
              </div>
            </div>

            <div className="rounded-2xl bg-background-section-burn p-4">
              <div className="system-xs-medium-uppercase text-text-tertiary">积分规则</div>
              <div className="system-sm-regular mt-2 text-text-secondary">
                本月
                {' '}
                <span className="system-md-semibold text-text-primary">
                  {formatInteger(checkInState?.monthly_check_in_points || 0)}
                  /
                  {formatInteger(checkInState?.monthly_check_in_cap || 0)}
                </span>
                {' '}
                分，签到积分有效期
                {' '}
                {checkInState?.valid_days || 90}
                天。
              </div>
              <div className="system-xs-regular mt-3 text-text-tertiary">
                本月将过期
                {formatInteger(expiration?.expiring_points_this_month || 0)}
                分，最近到期：
                {formatTime(expiration?.nearest_expiration_at || null)}
              </div>
            </div>

            <div className="rounded-2xl bg-background-section-burn p-4 sm:col-span-2">
              <div className="flex flex-wrap gap-3 text-text-tertiary">
                <div className="system-xs-regular flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-green-400" />
                  已签到
                </div>
                <div className="system-xs-regular flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-red-200" />
                  未签到
                </div>
                <div className="system-xs-regular flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-components-panel-bg ring-1 ring-divider-regular" />
                  未到日期
                </div>
                <div className="system-xs-regular flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-state-accent-solid" />
                  有积分流水
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Modal
        isShow={!!selectedDate}
        onClose={() => setSelectedDate('')}
        closable
        className="max-w-[520px] p-0"
        containerClassName="p-6"
      >
        <div className="bg-components-panel-bg text-text-primary">
          <div className="border-b border-divider-subtle px-6 py-5 pr-14">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-state-accent-hover text-text-accent">
                <RiSparklingFill className="h-5 w-5" />
              </div>
              <div>
                <div className="title-xl-semi-bold text-text-primary">{selectedDay?.date}</div>
                <div className="system-xs-regular mt-1 text-text-tertiary">当天积分获得与消耗明细</div>
              </div>
            </div>
          </div>

          <div className="px-6 py-5">
            <div className="grid grid-cols-3 gap-2">
              <div className="rounded-2xl bg-background-section-burn p-3 text-center">
                <div className="system-xs-regular text-text-tertiary">获得</div>
                <div className="system-lg-semibold mt-1 text-green-600">
                  +
                  {formatInteger(selectedDay?.earned_points || 0)}
                </div>
              </div>
              <div className="rounded-2xl bg-background-section-burn p-3 text-center">
                <div className="system-xs-regular text-text-tertiary">消耗</div>
                <div className="system-lg-semibold mt-1 text-red-600">
                  -
                  {formatInteger(selectedDay?.spent_points || 0)}
                </div>
              </div>
              <div className="rounded-2xl bg-background-section-burn p-3 text-center">
                <div className="system-xs-regular text-text-tertiary">过期</div>
                <div className="system-lg-semibold mt-1 text-text-secondary">
                  -
                  {formatInteger(selectedDay?.expired_points || 0)}
                </div>
              </div>
            </div>

            <div className="mt-5 max-h-[340px] space-y-2 overflow-y-auto pr-1">
              {selectedDay?.transactions.length
                ? selectedDay.transactions.map(item => (
                    <div key={item.id} className="rounded-2xl border border-divider-subtle bg-background-section-burn p-3">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="system-sm-medium text-text-primary">{item.description}</div>
                          <div className="system-xs-regular mt-1 text-text-tertiary">
                            {sourceLabel[item.source] || item.source}
                            {' '}
                            ·
                            {' '}
                            {formatTime(item.created_at)}
                          </div>
                        </div>
                        <div className={cn(
                          'system-md-semibold',
                          item.points > 0 ? 'text-green-600' : 'text-red-600',
                        )}
                        >
                          {item.points > 0 ? '+' : ''}
                          {formatInteger(item.points)}
                        </div>
                      </div>
                    </div>
                  ))
                : (
                    <div className="system-sm-regular rounded-2xl border border-dashed border-divider-regular bg-background-section-burn p-6 text-center text-text-tertiary">
                      这一天没有积分获得或消耗
                    </div>
                  )}
            </div>
          </div>
        </div>
      </Modal>

      <div>
        <div className="mb-3 flex items-center gap-2">
          <RiGiftLine className="h-5 w-5 text-text-secondary" />
          <div className="system-md-semibold text-text-primary">权益兑换</div>
        </div>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {rewards.map((reward) => {
            const disabled = balance < reward.points || isPending
            return (
              <div key={reward.id} className="rounded-2xl border border-divider-regular bg-components-panel-bg p-4 shadow-xs">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="system-md-semibold text-text-primary">{reward.name}</div>
                    <div className="system-sm-regular mt-1 min-h-10 text-text-tertiary">{reward.description}</div>
                  </div>
                  <div className="system-xs-semibold rounded-xl bg-background-section-burn px-2 py-1 text-text-secondary">
                    {formatInteger(reward.points)}
                    {' '}
                    分
                  </div>
                </div>
                <Button
                  className="mt-4 w-full"
                  variant="primary"
                  disabled={disabled}
                  loading={isPending}
                  onClick={() => handleRedeem(reward.id)}
                >
                  {balance < reward.points ? '积分不足' : '立即兑换'}
                </Button>
              </div>
            )
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <div className="overflow-hidden rounded-2xl border border-divider-regular bg-components-panel-bg">
          <div className="flex items-center gap-2 border-b border-divider-regular px-4 py-3">
            <RiHistoryLine className="h-5 w-5 text-text-secondary" />
            <div className="system-md-semibold text-text-primary">积分流水</div>
          </div>
          {transactions.length === 0 && (
            <div className="system-sm-regular p-4 text-text-tertiary">暂无积分流水</div>
          )}
          {transactions.map(item => (
            <div key={item.id} className="flex items-center justify-between gap-4 border-b border-divider-subtle px-4 py-3 last:border-b-0">
              <div>
                <div className="system-sm-medium text-text-primary">{item.description}</div>
                <div className="system-xs-regular mt-1 text-text-tertiary">
                  {formatTime(item.created_at)}
                  {item.points > 0 && item.expires_at && (
                    <>
                      {' '}
                      · 到期
                      {' '}
                      {dayjs(item.expires_at * 1000).format('YYYY-MM-DD')}
                      {' '}
                      · 剩余
                      {' '}
                      {formatInteger(item.remaining_points)}
                      {' '}
                      分
                    </>
                  )}
                </div>
              </div>
              <div
                className={cn(
                  'system-md-semibold',
                  item.points > 0 ? 'text-util-colors-green-green-600' : 'text-text-secondary',
                )}
              >
                {item.points > 0 ? '+' : ''}
                {formatInteger(item.points)}
              </div>
            </div>
          ))}
        </div>

        <div className="overflow-hidden rounded-2xl border border-divider-regular bg-components-panel-bg">
          <div className="flex items-center gap-2 border-b border-divider-regular px-4 py-3">
            <RiExchangeDollarLine className="h-5 w-5 text-text-secondary" />
            <div className="system-md-semibold text-text-primary">兑换记录</div>
          </div>
          {redemptions.length === 0 && (
            <div className="system-sm-regular p-4 text-text-tertiary">暂无兑换记录</div>
          )}
          {redemptions.map(item => (
            <div key={item.id} className="flex items-center justify-between gap-4 border-b border-divider-subtle px-4 py-3 last:border-b-0">
              <div>
                <div className="system-sm-medium text-text-primary">{item.reward_name}</div>
                <div className="system-xs-regular mt-1 text-text-tertiary">{formatTime(item.created_at)}</div>
              </div>
              <div className="text-right">
                <div className="system-sm-semibold text-text-primary">
                  {formatInteger(item.points)}
                  {' '}
                  分
                </div>
                <div className="system-xs-regular mt-1 text-text-tertiary">
                  {item.status === 'pending_activation' ? '待激活' : item.status}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default PointsPage
