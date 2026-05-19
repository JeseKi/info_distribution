export interface TokenResponse {
  access_token: string
  token_type: string
  scope: string
}

export interface MessageResponse {
  message: string
}

export interface LoginChallengeResponse {
  requires_2fa: true
  challenge_token: string
  challenge_type: 'totp'
}

export type LoginResponse = TokenResponse | LoginChallengeResponse

export type OAuthProviderName = 'GITHUB' | 'GOOGLE'

export interface OAuthProviderInfo {
  provider: OAuthProviderName
  label: string
}

export interface OAuthProvidersResponse {
  providers: OAuthProviderInfo[]
}

export interface OAuthTicketExchangePayload {
  ticket: string
}

export interface OAuthAuthorizeMetadata {
  client_id: string
  client_name: string
  redirect_uri: string
  permissions: OAuthPermission[]
  state: string | null
}

export interface OAuthPermission {
  scope: string
  title: string
  description: string
}

export interface OAuthAuthorizeConfirmPayload {
  response_type: string
  client_id: string
  redirect_uri: string
  scope: string
  state?: string | null
  code_challenge: string
  code_challenge_method: string
  approve: boolean
}

export interface OAuthAuthorizeResult {
  redirect_url: string
}

export interface OAuthDeviceAuthorizationMetadata {
  client_id: string
  client_name: string
  user_code: string
  permissions: OAuthPermission[]
  expires_at: string
}

export interface OAuthDeviceAuthorizationConfirmPayload {
  user_code: string
  approve: boolean
}

export interface OAuthDeviceAuthorizationResult {
  status: 'approved' | 'denied'
}

export interface OAuthClient {
  id: number
  client_id: string
  name: string
  redirect_uris: string[]
  allowed_scopes: string[]
  is_active: boolean
  require_pkce: boolean
  created_at: string
  updated_at: string
}

export interface OAuthClientWithSecret extends OAuthClient {
  client_secret: string
}

export interface OAuthClientCreatePayload {
  name: string
  redirect_uris: string[]
  allowed_scopes: string[]
  is_active: boolean
  require_pkce: boolean
}

export interface OAuthClientUpdatePayload {
  name?: string
  redirect_uris?: string[]
  allowed_scopes?: string[]
  is_active?: boolean
  require_pkce?: boolean
}

export interface AuthTokens {
  accessToken: string
}

export type UserRole = 'user' | 'admin'

export type UserStatus = 'active' | 'inactive'

export interface UserProfile {
  id: number
  username: string
  email: string
  name: string | null
  role: UserRole
  status: UserStatus
  effective_scopes: string[]
  two_factor_enabled: boolean
  two_factor_confirmed_at: string | null
}

export interface LoginPayload {
  username: string
  password: string
  turnstile_token?: string
}

export interface TwoFactorVerifyPayload {
  challenge_token: string
  code: string
}

export interface TwoFactorSetupStartResponse {
  secret: string
  secret_masked: string
  otpauth_url: string
  setup_token: string
}

export interface TwoFactorSetupConfirmPayload {
  setup_token: string
  code: string
}

export interface TwoFactorDisablePayload {
  password: string
  code: string
}

export interface TwoFactorRegenerateBackupCodesPayload {
  password: string
  code: string
}

export interface BackupCodesResponse extends MessageResponse {
  backup_codes: string[]
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
}

export interface VerificationCodePayload {
  email: string
  turnstile_token?: string
}

export interface RegisterWithCodePayload {
  username: string
  email: string
  password: string
  code: string
  turnstile_token?: string
}

export interface UpdateProfilePayload {
  username?: string | null
  name?: string | null
}

export interface PasswordResetLinkPayload {
  email: string
  turnstile_token?: string
}

export interface PasswordResetWithTokenPayload {
  token: string
  new_password: string
}

export interface EmailChangeCodePayload {
  email: string
}

export interface EmailChangeConfirmPayload {
  email: string
  code: string
}

export interface PasswordChangeConfirmPayload {
  token: string
  new_password: string
}

export interface AdminUser {
  id: number
  username: string
  email: string
  name: string | null
  role: UserRole
  status: UserStatus
  scope_overrides: string[] | null
  effective_scopes: string[]
  available_scopes: string[]
  created_at: string
}

export interface AdminUserCreatePayload {
  username: string
  email: string
  name?: string | null
  role?: UserRole
  status?: UserStatus
  password: string
}

export interface AdminUserUpdatePayload {
  username?: string | null
  email?: string | null
  name?: string | null
  role?: UserRole
  status?: UserStatus
  password?: string | null
}

export interface AdminUserScopesUpdatePayload {
  scopes: string[]
}

export type ScopeCategory = 'normal' | 'sensitive' | 'dangerous'

export interface AdminScope {
  id: number
  scope: string
  title: string
  description: string
  category: ScopeCategory
  created_at: string
  updated_at: string
}

export interface AdminScopeUpdatePayload {
  category: ScopeCategory
}

export interface ItemPayload {
  name: string
}

export interface Item {
  id: number
  name: string
}

export type AsyncTaskStatus = 'pending' | 'running' | 'completed' | 'failed'

export type AsyncTaskLogLevel = 'info' | 'warning' | 'error'

export interface AsyncTaskPayload {
  name: string
  total_count: number
  fail_every: number
  delay_ms: number
}

export interface AsyncTaskLog {
  id: number
  sequence: number
  level: AsyncTaskLogLevel
  message: string
  created_at: string
}

export interface AsyncTask {
  id: number
  name: string
  status: AsyncTaskStatus
  total_count: number
  processed_count: number
  success_count: number
  failure_count: number
  progress_percent: number
  fail_every: number
  delay_ms: number
  last_message: string | null
  requested_by_user_id: number | null
  created_at: string
  started_at: string | null
  finished_at: string | null
}

export interface AsyncTaskDetail extends AsyncTask {
  logs: AsyncTaskLog[]
}

export type ArticlePublicationType = 'video' | 'article' | 'image_text'

export type ArticlePublishStatus = 'unpublished' | 'published' | 'invalid'

export interface ArticleDistributionAccount {
  id: number
  user_id: number
  account_name: string
  platform: string
  publication_type: ArticlePublicationType
  created_at: string
  updated_at: string
}

export interface ArticleDistributionAccountPayload {
  account_name: string
  platform: string
  publication_type: ArticlePublicationType
  user_id?: number | null
}

export interface ArticleDistributionArticle {
  id: number
  user_id: number
  account_id: number
  title: string
  markdown_content: string
  scheduled_date: string
  publish_status: ArticlePublishStatus
  published_url: string | null
  source: string
  created_by_user_id: number | null
  api_key_id: number | null
  created_at: string
  updated_at: string
  account: ArticleDistributionAccount | null
}

export interface ArticleDistributionArticleUploadItem {
  title: string
  markdown_content: string
  scheduled_date: string
}

export interface ArticleDistributionArticleBatchPayload {
  account_id: number
  articles: ArticleDistributionArticleUploadItem[]
}

export interface ArticleDistributionArticleFilters {
  user_id?: number
  account_id?: number
  scheduled_from?: string
  scheduled_to?: string
  publish_status?: ArticlePublishStatus
  platform?: string
  publication_type?: ArticlePublicationType
}

export interface ArticleDistributionArticleUpdatePayload {
  account_id?: number
  title?: string
  markdown_content?: string
  scheduled_date?: string
  publish_status?: ArticlePublishStatus
  published_url?: string | null
}

export interface ArticleDistributionPendingArticle {
  id: number
  title: string
  markdown_content: string
  scheduled_date: string
  account_id: number
  account_name: string
  platform: string
  publication_type: ArticlePublicationType
  publish_status: ArticlePublishStatus
  published_url: string | null
  created_at: string
}

export interface ArticleDistributionPlatformSummary {
  account_id: number
  account_name: string
  platform: string
  publication_type: ArticlePublicationType
  published_count: number
  unpublished_count: number
  invalid_count: number
  latest_published_url: string | null
}

export interface ArticleDistributionPendingUser {
  user_id: number
  username: string
  name: string | null
  email: string
  remaining_count: number
  published_count: number
  invalid_count: number
  platform_summaries: ArticleDistributionPlatformSummary[]
  articles: ArticleDistributionPendingArticle[]
}

export interface ArticleDistributionReportSummary {
  total_users: number
  unpublished_users: number
  published_articles: number
  unpublished_articles: number
  invalid_articles: number
}

export interface ArticleDistributionReport {
  summary: ArticleDistributionReportSummary
  users: ArticleDistributionPendingUser[]
}

export interface ArticleDistributionPendingReportFilters {
  scheduled_from?: string
  scheduled_to?: string
  platform?: string
  publication_type?: ArticlePublicationType
}

export interface ArticleDistributionApiKey {
  id: number
  name: string
  key_prefix: string
  created_by_user_id: number
  is_active: boolean
  created_at: string
  last_used_at: string | null
  revoked_at: string | null
}

export interface ArticleDistributionApiKeyCreatePayload {
  name: string
}

export interface ArticleDistributionApiKeyCreated extends ArticleDistributionApiKey {
  api_key: string
}
