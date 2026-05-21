import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  App,
  Button,
  DatePicker,
  Descriptions,
  Empty,
  Flex,
  Form,
  Input,
  Modal,
  Popconfirm,
  Popover,
  Select,
  Space,
  Statistic,
  Tabs,
  Tag,
  Typography,
} from 'antd'
import dayjs from 'dayjs'
import {
  CopyOutlined,
  DeleteOutlined,
  DownloadOutlined,
  EditOutlined,
  FileTextOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useAuth } from '../../hooks/useAuth'
import MarkdownArticleViewer from '../../components/article/MarkdownArticleViewer'
import * as articleApi from '../../lib/articleDistribution'
import {
  buildWechatHtml,
  buildStyledArticleHtml,
  copyHtml,
  copyText,
  downloadMarkdownAsDocx,
  downloadMarkdownImagesAsZip,
  markdownToPlainText,
} from '../../lib/articleDistributionExport'
import type {
  ArticleDistributionAccount,
  ArticleDistributionAccountPayload,
  ArticleDistributionArticle,
  ArticleDistributionArticleFilters,
  ArticlePublicationType,
  ArticlePublishStatus,
} from '../../lib/types'

const publicationTypeOptions = [
  { label: '视频', value: 'video' },
  { label: '文章', value: 'article' },
  { label: '图文', value: 'image_text' },
]

const publishStatusOptions = [
  { label: '未发布', value: 'unpublished' },
  { label: '已发布', value: 'published' },
  { label: '文档失效', value: 'invalid' },
]

const publicationTypeText: Record<ArticlePublicationType, string> = {
  video: '视频',
  article: '文章',
  image_text: '图文',
}

function publishStatusTag(status: ArticlePublishStatus) {
  if (status === 'published') return <Tag color="green">已发布</Tag>
  if (status === 'invalid') return <Tag color="red">文档失效</Tag>
  return <Tag>未发布</Tag>
}

interface ArticleEditFormValues {
  account_id: number
  title: string
  scheduled_date: dayjs.Dayjs
  markdown_content: string
}

export default function ArticleDistributionPage() {
  const { message } = App.useApp()
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const [accounts, setAccounts] = useState<ArticleDistributionAccount[]>([])
  const [articles, setArticles] = useState<ArticleDistributionArticle[]>([])
  const [selectedArticleId, setSelectedArticleId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [accountModalOpen, setAccountModalOpen] = useState(false)
  const [editingAccount, setEditingAccount] = useState<ArticleDistributionAccount | null>(null)
  const [accountForm] = Form.useForm<ArticleDistributionAccountPayload>()
  const [filterForm] = Form.useForm()
  const [publishModalOpen, setPublishModalOpen] = useState(false)
  const [publishForm] = Form.useForm<{ published_url: string }>()
  const [articleEditModalOpen, setArticleEditModalOpen] = useState(false)
  const [articleEditForm] = Form.useForm<ArticleEditFormValues>()
  const [copyMenuOpen, setCopyMenuOpen] = useState(false)
  const [downloadingImages, setDownloadingImages] = useState(false)

  const selectedArticle = useMemo(
    () => articles.find((article) => article.id === selectedArticleId) ?? articles[0] ?? null,
    [articles, selectedArticleId],
  )

  const unreadCount = articles.filter((article) => article.publish_status === 'unpublished').length
  const invalidCount = articles.filter((article) => article.publish_status === 'invalid').length
  const publishedCount = articles.filter((article) => article.publish_status === 'published').length

  const accountOptions = useMemo(
    () => accounts.map((account) => ({
      label: `${account.platform} / ${account.account_name} / ${publicationTypeText[account.publication_type]}`,
      value: account.id,
    })),
    [accounts],
  )

  const loadData = useCallback(async (filters?: ArticleDistributionArticleFilters) => {
    setLoading(true)
    try {
      const [nextAccounts, nextArticles] = await Promise.all([
        articleApi.listArticleAccounts(),
        articleApi.listArticles(filters),
      ])
      setAccounts(nextAccounts)
      setArticles(nextArticles)
      setSelectedArticleId((current) => {
        if (!nextArticles.length) return null
        if (current && nextArticles.some((article) => article.id === current)) return current
        return nextArticles[0].id
      })
    } catch (error) {
      message.error(resolveErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const handleAccountSubmit = async (values: ArticleDistributionAccountPayload) => {
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
      await loadData(buildFilters())
    } catch (error) {
      message.error(resolveErrorMessage(error))
    }
  }

  const handleDeleteAccount = async (accountId: number) => {
    try {
      await articleApi.deleteArticleAccount(accountId)
      message.success('账号已删除')
      await loadData(buildFilters())
    } catch (error) {
      message.error(resolveErrorMessage(error))
    }
  }

  const buildFilters = (): ArticleDistributionArticleFilters => {
    const values = filterForm.getFieldsValue()
    const range = values.date_range as [dayjs.Dayjs, dayjs.Dayjs] | undefined
    return {
      account_id: values.account_id,
      publish_status: values.publish_status,
      publication_type: values.publication_type,
      scheduled_from: range?.[0]?.format('YYYY-MM-DD'),
      scheduled_to: range?.[1]?.format('YYYY-MM-DD'),
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
      title: article.title,
      scheduled_date: dayjs(article.scheduled_date),
      markdown_content: article.markdown_content,
    })
    setArticleEditModalOpen(true)
  }

  const handleArticleEditSubmit = async (values: ArticleEditFormValues) => {
    if (!selectedArticle) return
    try {
      const updated = await articleApi.updateAdminArticle(selectedArticle.id, {
        account_id: values.account_id,
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
      await loadData(buildFilters())
    } catch (error) {
      message.error(resolveErrorMessage(error))
    }
  }

  const copyAction = async (type: 'markdown' | 'plain' | 'html' | 'wechat') => {
    if (!selectedArticle) return
    try {
      const plainText = markdownToPlainText(selectedArticle.markdown_content)
      if (type === 'markdown') await copyText(selectedArticle.markdown_content)
      if (type === 'plain') await copyText(plainText)
      if (type === 'html') {
        const html = buildStyledArticleHtml(selectedArticle.markdown_content)
        await copyHtml(html, html)
      }
      if (type === 'wechat') {
        await copyHtml(buildWechatHtml(selectedArticle.markdown_content), plainText, {
          preferRenderedSelection: true,
        })
      }
      setCopyMenuOpen(false)
      message.success('已复制')
    } catch {
      message.error('复制失败')
    }
  }

  const handleDownloadImagePackage = async () => {
    if (!selectedArticle) return
    setDownloadingImages(true)
    try {
      const count = await downloadMarkdownImagesAsZip(selectedArticle.markdown_content, selectedArticle.title)
      if (count === 0) {
        message.warning('文章中没有图片')
      } else {
        message.success(`已下载 ${count} 张图片`)
      }
    } catch {
      message.error('图片包下载失败')
    } finally {
      setDownloadingImages(false)
    }
  }

  return (
    <Flex vertical gap={18} className="article-workspace">
      <Flex align="center" justify="space-between" gap={16} wrap="wrap">
        <div>
          <Typography.Title level={2} style={{ margin: 0 }}>
            文章分发
          </Typography.Title>
          <Typography.Text type="secondary">
            按账号、日期和发布状态管理待分发内容。
          </Typography.Text>
        </div>
        <Space wrap>
          <Button icon={<ReloadOutlined />} loading={loading} onClick={() => void loadData(buildFilters())}>
            刷新
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingAccount(null)
              accountForm.resetFields()
              setAccountModalOpen(true)
            }}
          >
            新建账号
          </Button>
        </Space>
      </Flex>

      <div className="article-shell">
        <aside className="article-side">
          <Flex vertical gap={18}>
            <Flex gap={12}>
              <Statistic title="待发布" value={unreadCount} />
              <Statistic title="已发布" value={publishedCount} />
              <Statistic title="文档失效" value={invalidCount} />
            </Flex>

            <Form form={filterForm} layout="vertical">
              <Form.Item label="账号" name="account_id">
                <Select allowClear placeholder="全部账号" options={accountOptions} />
              </Form.Item>
              <Form.Item label="发布类型" name="publication_type">
                <Select allowClear placeholder="全部类型" options={publicationTypeOptions} />
              </Form.Item>
              <Form.Item label="发布状态" name="publish_status">
                <Select allowClear placeholder="全部状态" options={publishStatusOptions} />
              </Form.Item>
              <Form.Item label="日期" name="date_range">
                <DatePicker.RangePicker style={{ width: '100%' }} />
              </Form.Item>
              <Space>
                <Button type="primary" onClick={() => void loadData(buildFilters())}>筛选</Button>
                <Button onClick={() => {
                  filterForm.resetFields()
                  void loadData()
                }}>重置</Button>
              </Space>
            </Form>

            <div>
              <Typography.Text strong>账号</Typography.Text>
              <Flex vertical gap={8} style={{ marginTop: 10 }}>
                {accounts.map((account) => (
                  <div key={account.id} className="article-list-item">
                    <Flex justify="space-between" gap={8} align="start">
                      <div>
                        <Typography.Text strong>{account.account_name}</Typography.Text>
                        <div>
                          <Typography.Text type="secondary">
                            {account.platform} · {publicationTypeText[account.publication_type]}
                          </Typography.Text>
                        </div>
                        {isAdmin && <Typography.Text type="secondary">用户 {account.user_id}</Typography.Text>}
                      </div>
                      <Space size={4}>
                        <Button
                          size="small"
                          icon={<EditOutlined />}
                          onClick={() => {
                            setEditingAccount(account)
                            accountForm.setFieldsValue(account)
                            setAccountModalOpen(true)
                          }}
                        />
                        <Popconfirm title="删除这个账号？" onConfirm={() => void handleDeleteAccount(account.id)}>
                          <Button size="small" danger icon={<DeleteOutlined />} />
                        </Popconfirm>
                      </Space>
                    </Flex>
                  </div>
                ))}
              </Flex>
            </div>
          </Flex>
        </aside>

        <section className="article-list-panel">
          <Flex align="center" justify="space-between" style={{ marginBottom: 12 }}>
            <Typography.Text strong>文章队列</Typography.Text>
            <Tag>{articles.length} 篇</Tag>
          </Flex>
          <Flex vertical gap={8}>
            {articles.map((article) => (
              <button
                key={article.id}
                type="button"
                className={`article-list-item ${selectedArticle?.id === article.id ? 'article-list-item--active' : ''}`}
                onClick={() => setSelectedArticleId(article.id)}
              >
                <Flex vertical gap={6}>
                  <Flex justify="space-between" gap={8} align="center">
                    <Typography.Text strong ellipsis style={{ maxWidth: 240 }}>
                      {article.title}
                    </Typography.Text>
                    {publishStatusTag(article.publish_status)}
                  </Flex>
                  <Typography.Text type="secondary">
                    {article.scheduled_date} · {article.account?.platform ?? '未知平台'} / {article.account?.account_name ?? article.account_id}
                  </Typography.Text>
                </Flex>
              </button>
            ))}
            {!articles.length && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无文章" />}
          </Flex>
        </section>

        <main className="article-preview-panel">
          {selectedArticle ? (
            <>
              <div className="article-preview-header">
                <Flex justify="space-between" align="start" gap={16} wrap="wrap">
                  <div style={{ minWidth: 0 }}>
                    <Typography.Title level={2} style={{ marginTop: 0, marginBottom: 8 }}>
                      {selectedArticle.title}
                    </Typography.Title>
                    <Space wrap>
                      <Tag icon={<FileTextOutlined />}>{selectedArticle.scheduled_date}</Tag>
                      {publishStatusTag(selectedArticle.publish_status)}
                      <Tag>{selectedArticle.account?.platform ?? '平台'} / {selectedArticle.account?.account_name ?? selectedArticle.account_id}</Tag>
                    </Space>
                  </div>
                  <Space wrap>
                    <Button
                      type={selectedArticle.publish_status === 'unpublished' ? 'primary' : 'default'}
                      onClick={() => void handleDirectStatusChange(selectedArticle, 'unpublished')}
                    >
                      未发布
                    </Button>
                    <Button
                      type={selectedArticle.publish_status === 'published' ? 'primary' : 'default'}
                      onClick={() => openPublishModal(selectedArticle)}
                    >
                      已发布
                    </Button>
                    <Button
                      danger
                      type={selectedArticle.publish_status === 'invalid' ? 'primary' : 'default'}
                      onClick={() => void handleDirectStatusChange(selectedArticle, 'invalid')}
                    >
                      文档失效
                    </Button>
                  </Space>
                </Flex>
                <Descriptions size="small" column={3} style={{ marginTop: 16 }}>
                  <Descriptions.Item label="发布类型">
                    {selectedArticle.account ? publicationTypeText[selectedArticle.account.publication_type] : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="来源">{selectedArticle.source}</Descriptions.Item>
                  <Descriptions.Item label="文章 ID">{selectedArticle.id}</Descriptions.Item>
                  <Descriptions.Item label="发布地址">
                    {selectedArticle.published_url ? (
                      <Typography.Link href={selectedArticle.published_url} target="_blank" rel="noreferrer">
                        打开链接
                      </Typography.Link>
                    ) : '-'}
                  </Descriptions.Item>
                </Descriptions>
                <Space wrap style={{ marginTop: 16 }}>
                  <Popover
                    trigger="click"
                    open={copyMenuOpen}
                    onOpenChange={setCopyMenuOpen}
                    content={(
                      <Space direction="vertical">
                        <Button block icon={<CopyOutlined />} onClick={() => void copyAction('markdown')}>复制源码</Button>
                        <Button block icon={<CopyOutlined />} onClick={() => void copyAction('plain')}>复制纯文本</Button>
                        <Button block icon={<CopyOutlined />} onClick={() => void copyAction('html')}>复制 HTML</Button>
                        <Button block icon={<CopyOutlined />} onClick={() => void copyAction('wechat')}>复制为公众号</Button>
                      </Space>
                    )}
                  >
                    <Button icon={<CopyOutlined />}>复制</Button>
                  </Popover>
                  <Button
                    icon={<DownloadOutlined />}
                    loading={downloadingImages}
                    onClick={() => void handleDownloadImagePackage()}
                  >
                    图片包
                  </Button>
                  <Button
                    icon={<DownloadOutlined />}
                    onClick={() => void downloadMarkdownAsDocx(selectedArticle.markdown_content, selectedArticle.title)}
                  >
                    DOCX
                  </Button>
                  {isAdmin && (
                    <>
                      <Button icon={<EditOutlined />} onClick={() => openArticleEditModal(selectedArticle)}>
                        编辑文章
                      </Button>
                      <Popconfirm title="删除这篇文章？" onConfirm={() => void handleDeleteArticle(selectedArticle)}>
                        <Button danger icon={<DeleteOutlined />}>
                          删除文章
                        </Button>
                      </Popconfirm>
                    </>
                  )}
                </Space>
              </div>
              <div className="article-preview-body">
                <Tabs
                  defaultActiveKey="preview"
                  items={[
                    {
                      key: 'preview',
                      label: '预览',
                      children: <MarkdownArticleViewer markdown={selectedArticle.markdown_content} />,
                    },
                    {
                      key: 'source',
                      label: '源码',
                      children: <pre className="article-source">{selectedArticle.markdown_content}</pre>,
                    },
                  ]}
                />
              </div>
            </>
          ) : (
            <Flex align="center" justify="center" style={{ minHeight: 560 }}>
              <Empty description="选择一篇文章开始阅读" />
            </Flex>
          )}
        </main>
      </div>

      <Modal
        title={editingAccount ? '编辑账号' : '新建账号'}
        open={accountModalOpen}
        onCancel={() => setAccountModalOpen(false)}
        onOk={() => accountForm.submit()}
        destroyOnClose
      >
        <Form form={accountForm} layout="vertical" onFinish={(values) => void handleAccountSubmit(values)}>
          {isAdmin && (
            <Form.Item label="用户 ID" name="user_id">
              <Input type="number" placeholder="留空则使用当前管理员" />
            </Form.Item>
          )}
          <Form.Item label="平台" name="platform" rules={[{ required: true, message: '请输入平台' }]}>
            <Input placeholder="知乎、公众号、小红书等" />
          </Form.Item>
          <Form.Item label="账号名称" name="account_name" rules={[{ required: true, message: '请输入账号名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="发布类型" name="publication_type" rules={[{ required: true, message: '请选择发布类型' }]}>
            <Select options={publicationTypeOptions} />
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        title="填写发布地址"
        open={publishModalOpen}
        onCancel={() => setPublishModalOpen(false)}
        onOk={() => publishForm.submit()}
        destroyOnClose
      >
        <Form form={publishForm} layout="vertical" onFinish={(values) => void handlePublishSubmit(values)}>
          <Form.Item
            label="发布地址"
            name="published_url"
            rules={[
              { required: true, message: '请输入发布地址' },
              { type: 'url', message: '请输入有效 URL' },
            ]}
          >
            <Input placeholder="https://..." />
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        title="编辑文章"
        open={articleEditModalOpen}
        onCancel={() => setArticleEditModalOpen(false)}
        onOk={() => articleEditForm.submit()}
        width={820}
        destroyOnClose
      >
        <Form form={articleEditForm} layout="vertical" onFinish={(values) => void handleArticleEditSubmit(values)}>
          <Form.Item label="账号" name="account_id" rules={[{ required: true, message: '请选择账号' }]}>
            <Select options={accountOptions} />
          </Form.Item>
          <Form.Item label="标题" name="title" rules={[{ required: true, message: '请输入标题' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="发布日期" name="scheduled_date" rules={[{ required: true, message: '请选择发布日期' }]}>
            <DatePicker />
          </Form.Item>
          <Form.Item label="Markdown" name="markdown_content" rules={[{ required: true, message: '请输入 Markdown' }]}>
            <Input.TextArea rows={14} />
          </Form.Item>
        </Form>
      </Modal>
    </Flex>
  )
}

function normalizeAccountPayload(values: ArticleDistributionAccountPayload): ArticleDistributionAccountPayload {
  return {
    ...values,
    user_id: values.user_id ? Number(values.user_id) : undefined,
  }
}

function resolveErrorMessage(error: unknown): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: unknown } } }).response
    const detail = response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return '操作失败'
}
