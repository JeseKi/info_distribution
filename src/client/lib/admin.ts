import api, { buildTwoFactorHeaders } from './api'
import type {
  AdminScope,
  AdminScopeUpdatePayload,
  Project,
  ProjectPayload,
  Theme,
  ThemePayload,
  AdminUser,
  AdminUserCreatePayload,
  AdminUserScopesUpdatePayload,
  AdminUserUpdatePayload,
  UserProjectsUpdatePayload,
} from './types'

export async function createUser(
  payload: AdminUserCreatePayload,
  twoFactorCode?: string,
): Promise<AdminUser> {
  const { data } = await api.post<AdminUser>('/admin/users', payload, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
  return data
}

export async function listUsers(): Promise<AdminUser[]> {
  const { data } = await api.get<AdminUser[]>('/admin/users')
  return data
}

export async function updateUser(
  userId: number,
  payload: AdminUserUpdatePayload,
  twoFactorCode?: string,
): Promise<AdminUser> {
  const { data } = await api.patch<AdminUser>(`/admin/users/${userId}`, payload, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
  return data
}

export async function deleteUser(userId: number, twoFactorCode?: string): Promise<void> {
  await api.delete(`/admin/users/${userId}`, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
}

export async function listScopes(): Promise<AdminScope[]> {
  const { data } = await api.get<AdminScope[]>('/admin/scopes')
  return data
}

export async function updateScope(
  scope: string,
  payload: AdminScopeUpdatePayload,
  twoFactorCode?: string,
): Promise<AdminScope> {
  const { data } = await api.patch<AdminScope>(`/admin/scopes/${encodeURIComponent(scope)}`, payload, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
  return data
}

export async function updateUserScopes(
  userId: number,
  payload: AdminUserScopesUpdatePayload,
  twoFactorCode?: string,
): Promise<AdminUser> {
  const { data } = await api.put<AdminUser>(`/admin/users/${userId}/scopes`, payload, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
  return data
}

export async function listProjects(): Promise<Project[]> {
  const { data } = await api.get<Project[]>('/admin/projects')
  return data
}

export async function createProject(payload: ProjectPayload, twoFactorCode?: string): Promise<Project> {
  const { data } = await api.post<Project>('/admin/projects', payload, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
  return data
}

export async function updateProject(
  projectId: number,
  payload: Partial<ProjectPayload>,
  twoFactorCode?: string,
): Promise<Project> {
  const { data } = await api.patch<Project>(`/admin/projects/${projectId}`, payload, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
  return data
}

export async function listThemes(): Promise<Theme[]> {
  const { data } = await api.get<Theme[]>('/admin/themes')
  return data
}

export async function createTheme(payload: ThemePayload, twoFactorCode?: string): Promise<Theme> {
  const { data } = await api.post<Theme>('/admin/themes', payload, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
  return data
}

export async function updateTheme(
  themeId: number,
  payload: Partial<ThemePayload>,
  twoFactorCode?: string,
): Promise<Theme> {
  const { data } = await api.patch<Theme>(`/admin/themes/${themeId}`, payload, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
  return data
}

export async function updateUserProjects(
  userId: number,
  payload: UserProjectsUpdatePayload,
  twoFactorCode?: string,
): Promise<void> {
  await api.put(`/admin/users/${userId}/projects`, payload, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
}
