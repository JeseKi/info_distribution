import api from './api'
import type {
  ArticleDistributionAccount,
  ArticleDistributionAccountPayload,
  ArticleDistributionApiKey,
  ArticleDistributionApiKeyCreatePayload,
  ArticleDistributionApiKeyCreated,
  ArticleDistributionArticle,
  ArticleDistributionArticleBatchPayload,
  ArticleDistributionArticleFilters,
  ArticleDistributionArticlePage,
  ArticleDistributionArticlePageParams,
  ArticleDistributionArticleUpdatePayload,
  ArticleDistributionTrafficStat,
  ArticleDistributionTrafficStatPayload,
  ArticleDistributionTrafficSummaryPage,
  ArticleDistributionPublicDashboard,
  ArticleDistributionPendingReportFilters,
  ArticleDistributionPendingUser,
  ArticleDistributionReport,
  ArticlePublishStatus,
} from './types'

export async function listArticleAccounts(params?: {
  user_id?: number
  platform?: string
  publication_type?: string
  is_active?: boolean
}): Promise<ArticleDistributionAccount[]> {
  const { data } = await api.get<ArticleDistributionAccount[]>('/article-distribution/accounts', { params })
  return data
}

export async function createArticleAccount(
  payload: ArticleDistributionAccountPayload,
): Promise<ArticleDistributionAccount> {
  const { data } = await api.post<ArticleDistributionAccount>('/article-distribution/accounts', payload)
  return data
}

export async function updateArticleAccount(
  accountId: number,
  payload: Partial<ArticleDistributionAccountPayload>,
): Promise<ArticleDistributionAccount> {
  const { data } = await api.patch<ArticleDistributionAccount>(`/article-distribution/accounts/${accountId}`, payload)
  return data
}

export async function deleteArticleAccount(accountId: number): Promise<void> {
  await api.delete(`/article-distribution/accounts/${accountId}`)
}

export async function listArticles(
  params?: ArticleDistributionArticleFilters,
): Promise<ArticleDistributionArticle[]> {
  const { data } = await api.get<ArticleDistributionArticle[]>('/article-distribution/articles', { params })
  return data
}

export async function listArticlesPage(
  params?: ArticleDistributionArticlePageParams,
): Promise<ArticleDistributionArticlePage> {
  const { data } = await api.get<ArticleDistributionArticlePage>('/article-distribution/articles/page', { params })
  return data
}

export async function listArticleTrafficSummaries(
  params?: ArticleDistributionArticlePageParams,
): Promise<ArticleDistributionTrafficSummaryPage> {
  const { data } = await api.get<ArticleDistributionTrafficSummaryPage>(
    '/article-distribution/traffic-stats/articles/page',
    { params },
  )
  return data
}

export async function listArticleTrafficStats(articleId: number): Promise<ArticleDistributionTrafficStat[]> {
  const { data } = await api.get<ArticleDistributionTrafficStat[]>(
    `/article-distribution/articles/${articleId}/traffic-stats`,
  )
  return data
}

export async function createArticleTrafficStat(
  articleId: number,
  payload: ArticleDistributionTrafficStatPayload,
): Promise<ArticleDistributionTrafficStat> {
  const { data } = await api.post<ArticleDistributionTrafficStat>(
    `/article-distribution/articles/${articleId}/traffic-stats`,
    payload,
  )
  return data
}

export async function deleteArticleTrafficStat(statId: number): Promise<void> {
  await api.delete(`/article-distribution/traffic-stats/${statId}`)
}

export async function getArticle(articleId: number): Promise<ArticleDistributionArticle> {
  const { data } = await api.get<ArticleDistributionArticle>(`/article-distribution/articles/${articleId}`)
  return data
}

export async function updateArticleStatus(
  articleId: number,
  publishStatus: ArticlePublishStatus,
  publishedUrl?: string | null,
): Promise<ArticleDistributionArticle> {
  const { data } = await api.patch<ArticleDistributionArticle>(
    `/article-distribution/articles/${articleId}/status`,
    { publish_status: publishStatus, published_url: publishedUrl },
  )
  return data
}

export async function listUnpublishedArticleReport(
  params?: ArticleDistributionPendingReportFilters,
): Promise<ArticleDistributionReport> {
  const { data } = await api.get<ArticleDistributionReport>(
    '/article-distribution/reports/unpublished',
    { params },
  )
  return data
}

export async function getUnpublishedArticleReportUser(
  userId: number,
  params?: ArticleDistributionPendingReportFilters,
): Promise<ArticleDistributionPendingUser> {
  const { data } = await api.get<ArticleDistributionPendingUser>(
    `/article-distribution/reports/unpublished/users/${userId}`,
    { params },
  )
  return data
}

export async function listPublicArticleDashboard(
  params?: Pick<ArticleDistributionPendingReportFilters, 'scheduled_from' | 'scheduled_to' | 'publication_type'>,
): Promise<ArticleDistributionPublicDashboard> {
  const { data } = await api.get<ArticleDistributionPublicDashboard>(
    '/article-distribution/public/dashboard',
    { params },
  )
  return data
}

export async function createAdminArticles(
  payload: ArticleDistributionArticleBatchPayload,
): Promise<ArticleDistributionArticle[]> {
  const { data } = await api.post<ArticleDistributionArticle[]>('/admin/article-distribution/articles', payload)
  return data
}

export async function updateAdminArticle(
  articleId: number,
  payload: ArticleDistributionArticleUpdatePayload,
): Promise<ArticleDistributionArticle> {
  const { data } = await api.patch<ArticleDistributionArticle>(
    `/admin/article-distribution/articles/${articleId}`,
    payload,
  )
  return data
}

export async function deleteAdminArticle(articleId: number): Promise<void> {
  await api.delete(`/admin/article-distribution/articles/${articleId}`)
}

export async function listArticleApiKeys(): Promise<ArticleDistributionApiKey[]> {
  const { data } = await api.get<ArticleDistributionApiKey[]>('/admin/article-distribution/api-keys')
  return data
}

export async function createArticleApiKey(
  payload: ArticleDistributionApiKeyCreatePayload,
): Promise<ArticleDistributionApiKeyCreated> {
  const { data } = await api.post<ArticleDistributionApiKeyCreated>('/admin/article-distribution/api-keys', payload)
  return data
}

export async function revokeArticleApiKey(apiKeyId: number): Promise<ArticleDistributionApiKey> {
  const { data } = await api.post<ArticleDistributionApiKey>(`/admin/article-distribution/api-keys/${apiKeyId}/revoke`)
  return data
}
