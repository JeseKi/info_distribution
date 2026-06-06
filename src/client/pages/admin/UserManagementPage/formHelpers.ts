import type { AdminUser, AdminUserUpdatePayload, UserRole, UserStatus } from '../../../lib/types'

export function buildEditFormValues(user: AdminUser) {
  return {
    username: user.username,
    email: user.email,
    name: user.name ?? '',
    wechat_nickname: user.wechat_nickname ?? '',
    wechat_id: user.wechat_id ?? '',
    role: user.role,
    status: user.status,
  }
}

export function buildCreateFormValues() {
  return {
    username: '',
    email: '',
    name: '',
    wechat_nickname: '',
    wechat_id: '',
    role: 'user' as const,
    status: 'active' as const,
    password: '',
    confirmPassword: '',
  }
}

export function isPasswordMismatch(values: { password?: string; confirmPassword?: string }) {
  return values.password !== values.confirmPassword
}

export function buildUpdatePayload(
  values: {
    username: string
    email: string
    name?: string | null
    wechat_nickname?: string | null
    wechat_id?: string | null
    role: string
    status: string
  },
  user: AdminUser
): AdminUserUpdatePayload {
  const payload: AdminUserUpdatePayload = {}
  const username = values.username.trim()
  if (username !== user.username) payload.username = username
  const email = values.email.trim().toLowerCase()
  if (email !== user.email) payload.email = email
  const name = values.name?.trim() ?? ''
  const existingName = user.name?.trim() ?? ''
  if (name !== existingName) payload.name = name || null
  const wechatNickname = values.wechat_nickname?.trim() ?? ''
  const existingWechatNickname = user.wechat_nickname?.trim() ?? ''
  if (wechatNickname !== existingWechatNickname) {
    payload.wechat_nickname = wechatNickname || null
  }
  const wechatId = values.wechat_id?.trim() ?? ''
  const existingWechatId = user.wechat_id?.trim() ?? ''
  if (wechatId !== existingWechatId) payload.wechat_id = wechatId || null
  if (values.role !== user.role) payload.role = values.role as UserRole
  if (values.status !== user.status) payload.status = values.status as UserStatus
  return payload
}
