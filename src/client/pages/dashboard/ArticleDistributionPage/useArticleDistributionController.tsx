import { useCallback, useEffect, useMemo, useState } from 'react'
import { App, Form, Space } from 'antd'
import dayjs from 'dayjs'
import { useAuth } from '../../../hooks/useAuth'
import { listProjects } from '../../../lib/admin'
import * as articleApi from '../../../lib/articleDistribution'
import type {
  ArticleDistributionAccount,
  ArticleDistributionArticle,
  ArticleDistributionArticleFilters,
  ArticleDistributionArticleStatusCounts,
  ArticlePublishStatus,
  AccountOptions as ArticleAccountOptions,
  ProjectSummary,
} from '../../../lib/types'
import { copyArticleContent, downloadArticleImagePackage, type ImagePackageDownloadMode } from './articleOperations'
import { defaultArticlePageSize, defaultArticleStatusCounts, publicationTypeText } from './constants'
import { resolveErrorMessage } from './errors'
import { normalizeAccountPayload } from './normalize'
import { inactiveAccountTag } from './statusTags'
import type {
  AccountFormValues,
  ArticleEditFormValues,
  ArticleFilterFormValues,
  ImagePackageProgressState,
} from './types'

export function useArticleDistributionController() {
  const { message } = App.useApp()
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const [accounts, setAccounts] = useState<ArticleDistributionAccount[]>([])
  const [articles, setArticles] = useState<ArticleDistributionArticle[]>([])
  const [selectedArticleId, setSelectedArticleId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [accountModalOpen, setAccountModalOpen] = useState(false)
  const [accountSetupOptions, setAccountSetupOptions] = useState<ArticleAccountOptions>({ projects: [], themes: [] })
  const [accountSetupOptionsLoading, setAccountSetupOptionsLoading] = useState(false)
  const [availableProjects, setAvailableProjects] = useState<ProjectSummary[]>([])
  const [editingAccount, setEditingAccount] = useState<ArticleDistributionAccount | null>(null)
  const [accountForm] = Form.useForm<AccountFormValues>()
  const [filterForm] = Form.useForm<ArticleFilterFormValues>()
  const [publishModalOpen, setPublishModalOpen] = useState(false)
  const [publishForm] = Form.useForm<{ published_url: string }>()
  const [articleEditModalOpen, setArticleEditModalOpen] = useState(false)
  const [articleEditForm] = Form.useForm<ArticleEditFormValues>()
  const [copyMenuOpen, setCopyMenuOpen] = useState(false)
  const [downloadingImages, setDownloadingImages] = useState(false)
  const [imagePackageProgress, setImagePackageProgress] = useState<ImagePackageProgressState | null>(null)
  const [articlePage, setArticlePage] = useState(1)
  const [articlePageSize, setArticlePageSize] = useState(defaultArticlePageSize)
  const [articleTotal, setArticleTotal] = useState(0)
  const [articleStatusCounts, setArticleStatusCounts] = useState<ArticleDistributionArticleStatusCounts>(
    defaultArticleStatusCounts,
  )

  const selectedArticle = useMemo(
    () => articles.find((article) => article.id === selectedArticleId) ?? articles[0] ?? null,
    [articles, selectedArticleId],
  )

  const accountOptions = useMemo(
    () => accounts.map((account) => ({
      label: (
        <Space size={4}>
          <span>{account.platform} / {account.account_name} / {publicationTypeText[account.publication_type]}</span>
          {inactiveAccountTag(account.is_active)}
        </Space>
      ),
      value: account.id,
    })),
    [accounts],
  )

  const projectOptions = useMemo(
    () => availableProjects.map((project) => ({
      label: project.is_active ? project.name : `${project.name}（停用）`,
      value: project.id,
    })),
    [availableProjects],
  )

  const buildFilters = useCallback((): ArticleDistributionArticleFilters => {
    const values = filterForm.getFieldsValue()
    const range = values.date_range
    return {
      account_id: values.account_id,
      project_id: values.project_id,
      publish_status: values.publish_status,
      publication_type: values.publication_type,
      scheduled_from: range?.[0]?.format('YYYY-MM-DD'),
      scheduled_to: range?.[1]?.format('YYYY-MM-DD'),
    }
  }, [filterForm])

  const loadData = useCallback(async (
    filters?: ArticleDistributionArticleFilters,
    pagination: { page: number; pageSize: number } = { page: 1, pageSize: defaultArticlePageSize },
  ) => {
    setLoading(true)
    try {
      const [nextAccounts, nextArticlePage] = await Promise.all([
        articleApi.listArticleAccounts(),
        articleApi.listArticlesPage({ ...filters, page: pagination.page, page_size: pagination.pageSize }),
      ])
      setAccounts(nextAccounts)
      setArticles(nextArticlePage.items)
      setArticlePage(nextArticlePage.page)
      setArticlePageSize(nextArticlePage.page_size)
      setArticleTotal(nextArticlePage.total)
      setArticleStatusCounts(nextArticlePage.status_counts)
      setSelectedArticleId((current) => resolveSelectedArticleId(current, nextArticlePage.items))
    } catch (error) {
      message.error(resolveErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    void loadData(undefined, { page: 1, pageSize: defaultArticlePageSize })
  }, [loadData])

  useEffect(() => {
    if (!user) {
      setAvailableProjects([])
      return
    }
    if (!isAdmin) {
      setAvailableProjects(user.projects)
      return
    }
    void listProjects()
      .then((projects) => setAvailableProjects(projects))
      .catch(() => setAvailableProjects([]))
  }, [isAdmin, user])

  const reloadCurrentPage = () => loadData(buildFilters(), { page: articlePage, pageSize: articlePageSize })

  const loadAccountSetupOptions = useCallback(async (targetUserId?: number) => {
    setAccountSetupOptionsLoading(true)
    try {
      const options = await articleApi.getArticleAccountOptions(isAdmin ? targetUserId : undefined)
      setAccountSetupOptions(options)
    } catch (error) {
      message.error(resolveErrorMessage(error))
      setAccountSetupOptions({ projects: [], themes: [] })
    } finally {
      setAccountSetupOptionsLoading(false)
    }
  }, [isAdmin, message])

  const handleCreateAccount = () => {
    setEditingAccount(null)
    accountForm.resetFields()
    accountForm.setFieldsValue({ is_active: true })
    setAccountModalOpen(true)
    void loadAccountSetupOptions()
  }

  const handleEditAccount = (account: ArticleDistributionAccount) => {
    setEditingAccount(account)
    accountForm.setFieldsValue(account)
    setAccountModalOpen(true)
    void loadAccountSetupOptions(account.user_id)
  }

  const handleAccountSubmit = async (values: AccountFormValues) => {
    try {
      if (editingAccount) {
        await articleApi.updateArticleAccount(editingAccount.id, normalizeAccountPayload(values))
        message.success('账号已更新')
      } else {
        await articleApi.createArticleAccount(normalizeAccountPayload(values))
        message.success('账号已创建')
      }
      setAccountModalOpen(false)
      setEditingAccount(null)
      accountForm.resetFields()
      await reloadCurrentPage()
    } catch (error) {
      message.error(resolveErrorMessage(error))
    }
  }

  const handleDeleteAccount = async (accountId: number) => {
    try {
      await articleApi.deleteArticleAccount(accountId)
      message.success('账号已删除')
      await reloadCurrentPage()
    } catch (error) {
      message.error(resolveErrorMessage(error))
    }
  }

  const handleToggleAccountActive = async (account: ArticleDistributionAccount) => {
    try {
      await articleApi.updateArticleAccount(account.id, { is_active: !account.is_active })
      message.success(account.is_active ? '账号已停用' : '账号已启用')
      await reloadCurrentPage()
    } catch (error) {
      message.error(resolveErrorMessage(error))
    }
  }

  const updateArticleInList = (updated: ArticleDistributionArticle) => {
    setArticles((items) => items.map((item) => (item.id === updated.id ? updated : item)))
  }

  const handleDirectStatusChange = async (article: ArticleDistributionArticle, publishStatus: ArticlePublishStatus) => {
    try {
      const updated = await articleApi.updateArticleStatus(article.id, publishStatus)
      updateArticleInList(updated)
      message.success('发布状态已更新')
    } catch (error) {
      message.error(resolveErrorMessage(error))
    }
  }

  const openPublishModal = (article: ArticleDistributionArticle) => {
    setSelectedArticleId(article.id)
    publishForm.setFieldsValue({ published_url: article.published_url ?? '' })
    setPublishModalOpen(true)
  }

  const handlePublishSubmit = async ({ published_url }: { published_url: string }) => {
    if (!selectedArticle) return
    try {
      const updated = await articleApi.updateArticleStatus(selectedArticle.id, 'published', published_url)
      updateArticleInList(updated)
      setPublishModalOpen(false)
      publishForm.resetFields()
      message.success('发布状态已更新')
    } catch (error) {
      message.error(resolveErrorMessage(error))
    }
  }

  const openArticleEditModal = (article: ArticleDistributionArticle) => {
    articleEditForm.setFieldsValue({
      account_id: article.account_id,
      project_id: article.project_id,
      title: article.title,
      scheduled_date: dayjs(article.scheduled_date),
      markdown_content: article.markdown_content,
    })
    void loadAccountSetupOptions(article.account?.user_id)
    setArticleEditModalOpen(true)
  }

  const handleArticleEditAccountChange = (accountId: number) => {
    const account = accounts.find((item) => item.id === accountId)
    articleEditForm.setFieldValue('project_id', undefined)
    void loadAccountSetupOptions(account?.user_id)
  }

  const handleArticleEditSubmit = async (values: ArticleEditFormValues) => {
    if (!selectedArticle) return
    try {
      const updated = await articleApi.updateAdminArticle(selectedArticle.id, {
        account_id: values.account_id,
        project_id: values.project_id,
        title: values.title,
        scheduled_date: values.scheduled_date.format('YYYY-MM-DD'),
        markdown_content: values.markdown_content,
      })
      updateArticleInList(updated)
      setArticleEditModalOpen(false)
      message.success('文章已更新')
    } catch (error) {
      message.error(resolveErrorMessage(error))
    }
  }

  const handleDeleteArticle = async (article: ArticleDistributionArticle) => {
    try {
      await articleApi.deleteAdminArticle(article.id)
      message.success('文章已删除')
      await loadData(buildFilters(), {
        page: articles.length === 1 && articlePage > 1 ? articlePage - 1 : articlePage,
        pageSize: articlePageSize,
      })
    } catch (error) {
      message.error(resolveErrorMessage(error))
    }
  }

  const copyAction = async (type: 'markdown' | 'plain' | 'html' | 'wechat') => {
    if (!selectedArticle) return
    await copyArticleContent({
      article: selectedArticle,
      message,
      type,
      onCopied: () => setCopyMenuOpen(false),
    })
  }

  const handleDownloadImagePackage = async (mode: ImagePackageDownloadMode) => {
    if (!selectedArticle) return
    await downloadArticleImagePackage({
      article: selectedArticle,
      message,
      mode,
      setDownloadingImages,
      setImagePackageProgress,
    })
  }

  const handleResetFilters = (page: number, pageSize: number) => {
    filterForm.resetFields()
    void loadData(undefined, { page, pageSize })
  }

  return {
    accountForm, articleEditForm, filterForm, publishForm,
    accountModalOpen, accountSetupOptions, accountSetupOptionsLoading,
    articleEditModalOpen, copyMenuOpen, publishModalOpen,
    accountOptions, accounts, articlePage, articlePageSize, articleStatusCounts, articleTotal, articles,
    downloadingImages, editingAccount, imagePackageProgress, isAdmin, loading, selectedArticle,
    projectOptions,
    buildFilters, copyAction, loadAccountSetupOptions, loadData, openArticleEditModal, openPublishModal, reloadCurrentPage,
    handleAccountSubmit, handleArticleEditAccountChange, handleArticleEditSubmit, handleCreateAccount, handleDeleteAccount,
    handleDeleteArticle, handleDirectStatusChange, handleDownloadImagePackage, handleEditAccount,
    handlePublishSubmit, handleResetFilters, handleToggleAccountActive,
    setAccountModalOpen, setArticleEditModalOpen, setCopyMenuOpen, setPublishModalOpen, setSelectedArticleId,
  }
}

function resolveSelectedArticleId(
  current: number | null,
  nextArticles: ArticleDistributionArticle[],
) {
  if (!nextArticles.length) return null
  if (current && nextArticles.some((article) => article.id === current)) return current
  return nextArticles[0].id
}
