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
  ArticleDistributionPendingReportFilters,
  ArticleDistributionPendingUser,
  ArticlePublishStatus,
} from './types'

export async function listArticleAccounts(params?: {
  user_id?: number
  platform?: string
  publication_type?: string
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

export async function getArticle(articleId: number): Promise<ArticleDistributionArticle> {
  const { data } = await api.get<ArticleDistributionArticle>(`/article-distribution/articles/${articleId}`)
  return data
}

export async function updateArticleStatus(
  articleId: number,
  publishStatus: ArticlePublishStatus,
): Promise<ArticleDistributionArticle> {
  const { data } = await api.patch<ArticleDistributionArticle>(
    `/article-distribution/articles/${articleId}/status`,
    { publish_status: publishStatus },
  )
  return data
}

export async function listUnpublishedArticleReport(
  params?: ArticleDistributionPendingReportFilters,
): Promise<ArticleDistributionPendingUser[]> {
  const { data } = await api.get<ArticleDistributionPendingUser[]>(
    '/article-distribution/reports/unpublished',
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
