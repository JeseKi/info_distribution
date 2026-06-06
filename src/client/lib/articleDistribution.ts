import api from './api'
import type {
  ArticleDistributionAccount,
  ArticleDistributionAccountPage,
  ArticleDistributionAccountPageParams,
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
  ArticleDistributionMissingTrafficFilters,
  ArticleDistributionMissingTrafficPageParams,
  ArticleDistributionMissingTrafficPage,
  ArticleDistributionMissingTrafficReport,
  ArticleDistributionMissingTrafficUser,
  ArticleDistributionMetadataDashboard,
  ArticleDistributionOverview,
  ArticleDistributionOverviewArticleDetail,
  ArticleDistributionOverviewArticlePage,
  ArticleDistributionOverviewArticlePageParams,
  ArticleDistributionOverviewParams,
  ArticleDistributionPendingReportFilters,
  ArticleDistributionPublicityRecordExportParams,
  ArticleDistributionReportExportFormat,
  ArticleDistributionTrafficStat,
  ArticleDistributionTrafficStatPayload,
  ArticleDistributionTrafficSummaryPage,
  ArticleDistributionPublicDashboard,
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

export async function listArticleAccountsPage(
  params?: ArticleDistributionAccountPageParams,
): Promise<ArticleDistributionAccountPage> {
  const { data } = await api.get<ArticleDistributionAccountPage>('/article-distribution/accounts/page', { params })
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

export async function listReportOverview(
  params?: ArticleDistributionOverviewParams,
): Promise<ArticleDistributionOverview> {
  const { data } = await api.get<ArticleDistributionOverview>(
    '/article-distribution/reports/overview',
    { params },
  )
  return data
}

export async function listReportOverviewArticles(
  params?: ArticleDistributionOverviewArticlePageParams,
): Promise<ArticleDistributionOverviewArticlePage> {
  const { data } = await api.get<ArticleDistributionOverviewArticlePage>(
    '/article-distribution/reports/overview/articles',
    { params },
  )
  return data
}

export async function getReportOverviewArticleDetail(
  articleId: number,
  params?: Pick<ArticleDistributionOverviewParams, 'recorded_from' | 'recorded_to'>,
): Promise<ArticleDistributionOverviewArticleDetail> {
  const { data } = await api.get<ArticleDistributionOverviewArticleDetail>(
    `/article-distribution/reports/overview/articles/${articleId}`,
    { params },
  )
  return data
}

export async function downloadReportOverviewExport(
  params: ArticleDistributionOverviewParams,
  format: ArticleDistributionReportExportFormat = 'xlsx',
): Promise<void> {
  const exportParams = { ...params }
  delete exportParams.page
  delete exportParams.page_size
  const response = await api.get<Blob>('/article-distribution/reports/overview/export', {
    params: { ...exportParams, format },
    responseType: 'blob',
  })
  downloadBlobResponse(
    response.data,
    response.headers['content-disposition'],
    `overview-${exportParams.view ?? 'users'}-${new Date().toISOString().slice(0, 10)}.${format}`,
  )
}

export async function listArticleMetadataDashboard(
  params?: ArticleDistributionPendingReportFilters,
): Promise<ArticleDistributionMetadataDashboard> {
  const { data } = await api.get<ArticleDistributionMetadataDashboard>(
    '/article-distribution/reports/metadata-dashboard',
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

export async function listMissingTrafficArticles(
  params: ArticleDistributionMissingTrafficPageParams,
): Promise<ArticleDistributionMissingTrafficPage> {
  const { data } = await api.get<ArticleDistributionMissingTrafficPage>(
    '/article-distribution/reports/missing-traffic',
    { params },
  )
  return data
}

export async function listMissingTrafficReport(
  params: ArticleDistributionMissingTrafficFilters,
): Promise<ArticleDistributionMissingTrafficReport> {
  const { data } = await api.get<ArticleDistributionMissingTrafficReport>(
    '/article-distribution/reports/missing-traffic/users',
    { params },
  )
  return data
}

export async function getMissingTrafficReportUser(
  userId: number,
  params: ArticleDistributionMissingTrafficFilters,
): Promise<ArticleDistributionMissingTrafficUser> {
  const { data } = await api.get<ArticleDistributionMissingTrafficUser>(
    `/article-distribution/reports/missing-traffic/users/${userId}`,
    { params },
  )
  return data
}

export async function listPublicArticleDashboard(
  params?: Pick<ArticleDistributionPendingReportFilters, 'scheduled_from' | 'scheduled_to' | 'publication_type'> & {
    page?: number
    page_size?: number
  },
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

export async function downloadPublicityRecordsCsv(
  params?: ArticleDistributionPublicityRecordExportParams,
): Promise<void> {
  const response = await api.get<Blob>('/admin/article-distribution/publicity-records.csv', {
    params,
    responseType: 'blob',
  })
  downloadBlobResponse(
    response.data,
    response.headers['content-disposition'],
    `publicity-records-${new Date().toISOString().slice(0, 10)}.csv`,
  )
}

function downloadBlobResponse(blob: Blob, contentDisposition: unknown, fallback: string): void {
  const filename = resolveDownloadFilename(contentDisposition, fallback)
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(objectUrl)
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

function resolveDownloadFilename(contentDisposition: unknown, fallback: string): string {
  if (typeof contentDisposition !== 'string') {
    return fallback
  }
  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1])
  }
  const quotedMatch = contentDisposition.match(/filename="([^"]+)"/i)
  if (quotedMatch?.[1]) {
    return quotedMatch[1]
  }
  const plainMatch = contentDisposition.match(/filename=([^;]+)/i)
  return plainMatch?.[1]?.trim() || fallback
}
