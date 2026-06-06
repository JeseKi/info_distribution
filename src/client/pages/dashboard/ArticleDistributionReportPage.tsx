import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  App,
  Button,
  Card,
  Checkbox,
  DatePicker,
  Descriptions,
  Empty,
  Flex,
  Form,
  Input,
  Modal,
  Popover,
  Segmented,
  Select,
  Space,
  Statistic,
  Table,
  Tabs,
  Tag,
  Typography,
} from 'antd'
import type { TableColumnsType } from 'antd'
import { ReloadOutlined, SearchOutlined, SettingOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import * as articleApi from '../../lib/articleDistribution'
import { useAuth } from '../../hooks/useAuth'
import MarkdownArticleViewer from '../../components/article/MarkdownArticleViewer'
import type {
  ArticleDistributionAccountStatusFilter,
  ArticleDistributionOverview,
  ArticleDistributionOverviewArticle,
  ArticleDistributionOverviewItem,
  ArticleDistributionOverviewParams,
  ArticleDistributionOverviewSummary,
  ArticleDistributionOverviewTopic,
  ArticleDistributionOverviewUser,
  ArticleDistributionOverviewView,
  ArticleDistributionPlatformSummary,
  ArticlePublicationType,
  ArticlePublishStatus,
} from '../../lib/types'
import { resolveApiErrorMessage } from '../../lib/error'

const metadataScope = 'article_distribution:metadata_dashboard:read'

const publicationTypeOptions = [
  { label: '视频', value: 'video' },
  { label: '文章', value: 'article' },
  { label: '图文', value: 'image_text' },
]

const accountStatusOptions = [
  { label: '启用', value: 'active' },
  { label: '停用', value: 'inactive' },
  { label: '全部', value: 'all' },
]

const publishStatusOptions = [
  { label: '未发布', value: 'unpublished' },
  { label: '已发布', value: 'published' },
  { label: '文档失效', value: 'invalid' },
]

const viewOptions: { label: string; value: ArticleDistributionOverviewView }[] = [
  { label: '用户汇总', value: 'users' },
  { label: '文章明细', value: 'articles' },
  { label: '选题汇总', value: 'topics' },
]

const publicationTypeText: Record<ArticlePublicationType, string> = {
  video: '视频',
  article: '文章',
  image_text: '图文',
}

const defaultSummary: ArticleDistributionOverviewSummary = {
  total_users: 0,
  total_articles: 0,
  published_articles: 0,
  unpublished_articles: 0,
  invalid_articles: 0,
  inactive_account_articles: 0,
  missing_articles: 0,
  topic_count: 0,
  material_count: 0,
  read_count: 0,
  like_count: 0,
  favorite_count: 0,
  share_count: 0,
}

const defaultOverview: ArticleDistributionOverview = {
  view: 'users',
  summary: defaultSummary,
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
}

const defaultVisibleColumns: Record<ArticleDistributionOverviewView, string[]> = {
  users: [
    'user',
    'remaining_count',
    'published_count',
    'invalid_count',
    'missing_count',
    'read_count',
    'like_count',
    'favorite_count',
    'share_count',
  ],
  articles: [
    'article',
    'user',
    'account',
    'publish_status',
    'scheduled_date',
    'missing_traffic',
    'read_count',
    'like_count',
    'favorite_count',
    'share_count',
    'published_url',
    'actions',
  ],
  topics: [
    'topic',
    'article_count',
    'materials',
    'read_count',
    'like_count',
    'favorite_count',
    'share_count',
  ],
}

const columnLabels: Record<ArticleDistributionOverviewView, Record<string, string>> = {
  users: {
    user: '用户',
    remaining_count: '剩余未发布',
    published_count: '已发布',
    invalid_count: '失效',
    missing_count: '未填流量',
    read_count: '阅读量',
    like_count: '点赞量',
    favorite_count: '收藏量',
    share_count: '转发量',
  },
  articles: {
    article: '文章',
    user: '用户',
    account: '账号',
    publish_status: '状态',
    scheduled_date: '计划日期',
    missing_traffic: '未填流量',
    topic: '选题',
    article_role: '角色',
    read_count: '阅读量',
    like_count: '点赞量',
    favorite_count: '收藏量',
    share_count: '转发量',
    traffic_recorded_at: '统计时间',
    published_url: '发布链接',
    actions: '操作',
  },
  topics: {
    topic: '选题',
    article_count: '文章',
    materials: '素材',
    read_count: '阅读量',
    like_count: '点赞量',
    favorite_count: '收藏量',
    share_count: '转发量',
  },
}

interface FilterValues {
  keyword?: string
  platform?: string
  publication_type?: ArticlePublicationType
  publish_status?: ArticlePublishStatus
  account_status?: ArticleDistributionAccountStatusFilter
  date_range?: [dayjs.Dayjs, dayjs.Dayjs]
  missing_traffic_only?: boolean
  traffic_date?: dayjs.Dayjs
}

function publishStatusTag(status: ArticlePublishStatus) {
  if (status === 'published') return <Tag color="green">已发布</Tag>
  if (status === 'invalid') return <Tag color="red">文档失效</Tag>
  return <Tag>未发布</Tag>
}

function renderTrafficValue(value: number | undefined) {
  return typeof value === 'number' ? value : '-'
}

function isUserItem(item: ArticleDistributionOverviewItem): item is ArticleDistributionOverviewUser {
  return item.item_type === 'user'
}

function isArticleItem(item: ArticleDistributionOverviewItem): item is ArticleDistributionOverviewArticle {
  return item.item_type === 'article'
}

function isTopicItem(item: ArticleDistributionOverviewItem): item is ArticleDistributionOverviewTopic {
  return item.item_type === 'topic'
}

function localStorageKey(view: ArticleDistributionOverviewView) {
  return `article-distribution-report-columns:${view}`
}

function readVisibleColumns(view: ArticleDistributionOverviewView) {
  try {
    const raw = window.localStorage.getItem(localStorageKey(view))
    if (!raw) return defaultVisibleColumns[view]
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return defaultVisibleColumns[view]
    const allowed = new Set(Object.keys(columnLabels[view]))
    const selected = parsed.filter((value): value is string => (
      typeof value === 'string' && allowed.has(value)
    ))
    return selected.length ? selected : defaultVisibleColumns[view]
  } catch {
    return defaultVisibleColumns[view]
  }
}

function filterColumns<T extends object>(
  columns: TableColumnsType<T>,
  visibleKeys: string[],
): TableColumnsType<T> {
  return columns.filter((column) => {
    const key = typeof column.key === 'string' ? column.key : undefined
    return !key || visibleKeys.includes(key)
  })
}

function tableScroll<T extends object>(columns: TableColumnsType<T>) {
  const width = columns.reduce((total, column) => (
    total + (typeof column.width === 'number' ? column.width : 0)
  ), 0)
  return width > 0 ? { x: width } : undefined
}

function ColumnSelector({
  view,
  visibleKeys,
  onChange,
}: {
  view: ArticleDistributionOverviewView
  visibleKeys: string[]
  onChange: (keys: string[]) => void
}) {
  const labels = columnLabels[view]
  return (
    <Popover
      trigger="click"
      placement="bottomRight"
      content={(
        <Checkbox.Group
          value={visibleKeys}
          options={Object.entries(labels).map(([value, label]) => ({ value, label }))}
          onChange={(values) => onChange(values.map(String))}
          style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(110px, 1fr))', gap: 8 }}
        />
      )}
    >
      <Button icon={<SettingOutlined />}>显示字段</Button>
    </Popover>
  )
}

export default function ArticleDistributionReportPage() {
  const { message } = App.useApp()
  const { user } = useAuth()
  const [form] = Form.useForm<FilterValues>()
  const [view, setView] = useState<ArticleDistributionOverviewView>('users')
  const [loading, setLoading] = useState(false)
  const [overview, setOverview] = useState<ArticleDistributionOverview>(defaultOverview)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [selectedArticle, setSelectedArticle] = useState<ArticleDistributionOverviewArticle | null>(null)
  const [visibleColumns, setVisibleColumns] = useState<Record<ArticleDistributionOverviewView, string[]>>(() => ({
    users: readVisibleColumns('users'),
    articles: readVisibleColumns('articles'),
    topics: readVisibleColumns('topics'),
  }))

  const canViewTopics = Boolean(user?.effective_scopes.includes(metadataScope))
  const missingTrafficOnly = Form.useWatch('missing_traffic_only', form)

  const buildParams = useCallback((
    nextPage: number,
    nextPageSize: number,
  ): ArticleDistributionOverviewParams => {
    const values = form.getFieldsValue()
    const scheduledRange = values.date_range
    const params: ArticleDistributionOverviewParams = {
      view,
      page: nextPage,
      page_size: nextPageSize,
      keyword: values.keyword?.trim() || undefined,
      platform: values.platform?.trim() || undefined,
      publication_type: values.publication_type,
      publish_status: values.publish_status,
      account_status: values.account_status ?? 'active',
      scheduled_from: scheduledRange?.[0]?.format('YYYY-MM-DD'),
      scheduled_to: scheduledRange?.[1]?.format('YYYY-MM-DD'),
      missing_traffic_only: Boolean(values.missing_traffic_only),
    }
    if (values.missing_traffic_only) {
      const trafficDate = values.traffic_date ?? dayjs()
      params.recorded_from = trafficDate.startOf('day').toISOString()
      params.recorded_to = trafficDate.add(1, 'day').startOf('day').toISOString()
    }
    return params
  }, [form, view])

  const loadOverview = useCallback(async (nextPage = page, nextPageSize = pageSize) => {
    if (view === 'topics' && !canViewTopics) {
      setOverview({ ...defaultOverview, view: 'topics' })
      return
    }
    setLoading(true)
    try {
      const report = await articleApi.listReportOverview(buildParams(nextPage, nextPageSize))
      setOverview(report)
      setPage(report.page)
      setPageSize(report.page_size)
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '统一报表加载失败'))
    } finally {
      setLoading(false)
    }
  }, [buildParams, canViewTopics, message, page, pageSize, view])

  useEffect(() => {
    void loadOverview(page, pageSize)
  }, [loadOverview, page, pageSize])

  const setVisibleKeys = useCallback((keys: string[]) => {
    setVisibleColumns((current) => {
      const next = { ...current, [view]: keys }
      window.localStorage.setItem(localStorageKey(view), JSON.stringify(keys))
      return next
    })
  }, [view])

  const handleApplyFilters = () => {
    setPage(1)
    void loadOverview(1, pageSize)
  }

  const handleResetFilters = () => {
    form.resetFields()
    setPage(1)
    void loadOverview(1, pageSize)
  }

  const handleViewChange = (nextView: ArticleDistributionOverviewView) => {
    setView(nextView)
    setPage(1)
  }

  const summary = overview.summary
  const users = useMemo(() => overview.items.filter(isUserItem), [overview.items])
  const articles = useMemo(() => overview.items.filter(isArticleItem), [overview.items])
  const topics = useMemo(() => overview.items.filter(isTopicItem), [overview.items])

  const userColumns: TableColumnsType<ArticleDistributionOverviewUser> = [
    {
      title: '用户',
      key: 'user',
      width: 320,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Typography.Text strong>{record.name || record.username}</Typography.Text>
          <Typography.Text type="secondary">
            {record.username} · {record.email}
          </Typography.Text>
        </Space>
      ),
    },
    {
      title: '剩余未发布',
      dataIndex: 'remaining_count',
      key: 'remaining_count',
      width: 140,
      sorter: (a, b) => a.remaining_count - b.remaining_count,
      render: (value: number) => <Tag color={value > 0 ? 'volcano' : 'default'}>{value} 篇</Tag>,
    },
    {
      title: '已发布',
      dataIndex: 'published_count',
      key: 'published_count',
      width: 120,
      sorter: (a, b) => a.published_count - b.published_count,
      render: (value: number) => <Tag color="green">{value} 篇</Tag>,
    },
    {
      title: '失效',
      dataIndex: 'invalid_count',
      key: 'invalid_count',
      width: 100,
      sorter: (a, b) => a.invalid_count - b.invalid_count,
      render: (value: number) => <Tag color={value > 0 ? 'red' : 'default'}>{value} 篇</Tag>,
    },
    {
      title: '未填流量',
      dataIndex: 'missing_count',
      key: 'missing_count',
      width: 120,
      sorter: (a, b) => a.missing_count - b.missing_count,
      render: (value: number) => <Tag color={value > 0 ? 'orange' : 'default'}>{value} 篇</Tag>,
    },
    trafficColumn('阅读量', 'read_count'),
    trafficColumn('点赞量', 'like_count'),
    trafficColumn('收藏量', 'favorite_count'),
    trafficColumn('转发量', 'share_count'),
  ]

  const articleColumns = buildArticleColumns({
    includeUser: true,
    includeActions: true,
    onSelectArticle: setSelectedArticle,
  })

  const topicColumns: TableColumnsType<ArticleDistributionOverviewTopic> = [
    {
      title: '选题',
      key: 'topic',
      width: 360,
      render: (_, record) => (
        <Space direction="vertical" size={2}>
          <Typography.Text strong>{record.topic}</Typography.Text>
          <Typography.Text type="secondary">{record.output_id ?? '无 output_id'}</Typography.Text>
        </Space>
      ),
    },
    {
      title: '文章',
      dataIndex: 'article_count',
      key: 'article_count',
      width: 100,
      sorter: (a, b) => a.article_count - b.article_count,
      render: (value: number) => <Tag>{value} 篇</Tag>,
    },
    {
      title: '素材',
      key: 'materials',
      width: 300,
      render: (_, record) => renderMaterials(record.materials),
    },
    trafficColumn('阅读量', 'read_count'),
    trafficColumn('点赞量', 'like_count'),
    trafficColumn('收藏量', 'favorite_count'),
    trafficColumn('转发量', 'share_count'),
  ]

  const pagination = {
    current: page,
    pageSize,
    total: overview.total,
    showSizeChanger: true,
    pageSizeOptions: [10, 20, 50, 100],
    showTotal: (_: number, range: [number, number]) => `第 ${range[0]}-${range[1]} 条，共 ${overview.total} 条`,
    onChange: (nextPage: number, nextPageSize: number) => {
      setPage(nextPage)
      setPageSize(nextPageSize)
    },
  }
  const visibleUserColumns = filterColumns(userColumns, visibleColumns.users)
  const visibleArticleColumns = filterColumns(articleColumns, visibleColumns.articles)
  const visibleTopicColumns = filterColumns(topicColumns, visibleColumns.topics)
  const expandedUserArticleColumns = buildArticleColumns({
    includeUser: false,
    includeActions: true,
    onSelectArticle: setSelectedArticle,
  })
  const expandedTopicArticleColumns = buildArticleColumns({
    includeUser: true,
    includeActions: true,
    onSelectArticle: setSelectedArticle,
  })

  return (
    <Flex vertical gap={18}>
      <Flex align="center" justify="space-between" gap={16} wrap="wrap">
        <div>
          <Typography.Title level={2} style={{ margin: 0 }}>
            分发后台
          </Typography.Title>
          <Typography.Text type="secondary">
            用统一筛选查看用户进度、文章明细、未填流量和选题汇总。
          </Typography.Text>
        </div>
        <Space wrap>
          <Segmented
            value={view}
            options={viewOptions.map((option) => ({
              ...option,
              disabled: option.value === 'topics' && !canViewTopics,
            }))}
            onChange={(value) => handleViewChange(value as ArticleDistributionOverviewView)}
          />
          <ColumnSelector
            view={view}
            visibleKeys={visibleColumns[view]}
            onChange={setVisibleKeys}
          />
          <Button
            icon={<ReloadOutlined />}
            loading={loading}
            onClick={() => void loadOverview(page, pageSize)}
          >
            刷新
          </Button>
        </Space>
      </Flex>

      {!canViewTopics && (
        <Alert
          type="info"
          showIcon
          message="选题汇总需要额外权限"
          description={`需要 ${metadataScope} scope。`}
        />
      )}

      <Card>
        <Flex gap={24} wrap="wrap">
          <Statistic title="用户数" value={summary.total_users} />
          <Statistic title="文章数" value={summary.total_articles} />
          <Statistic title="已发布" value={summary.published_articles} />
          <Statistic title="未发布" value={summary.unpublished_articles} />
          <Statistic title="未填流量" value={summary.missing_articles} />
          <Statistic title="选题数" value={summary.topic_count} />
          <Statistic title="素材数" value={summary.material_count} />
          <Statistic title="阅读量" value={summary.read_count} />
          <Statistic title="点赞量" value={summary.like_count} />
          <Statistic title="收藏量" value={summary.favorite_count} />
          <Statistic title="转发量" value={summary.share_count} />
        </Flex>

        <Form
          form={form}
          layout="vertical"
          initialValues={{
            account_status: 'active',
            missing_traffic_only: false,
            traffic_date: dayjs(),
          }}
          style={{ marginTop: 18 }}
        >
          <Flex gap={16} wrap="wrap" align="end">
            <Form.Item label="搜索" name="keyword" style={{ minWidth: 240 }}>
              <Input prefix={<SearchOutlined />} allowClear placeholder="用户、文章、账号或链接" />
            </Form.Item>
            <Form.Item label="平台" name="platform" style={{ minWidth: 180 }}>
              <Input allowClear placeholder="wechat、zhihu..." />
            </Form.Item>
            <Form.Item label="发布类型" name="publication_type" style={{ minWidth: 150 }}>
              <Select allowClear options={publicationTypeOptions} placeholder="全部类型" />
            </Form.Item>
            <Form.Item label="发布状态" name="publish_status" style={{ minWidth: 150 }}>
              <Select allowClear options={publishStatusOptions} placeholder="全部状态" />
            </Form.Item>
            <Form.Item label="账号状态" name="account_status" style={{ minWidth: 130 }}>
              <Select options={accountStatusOptions} />
            </Form.Item>
            <Form.Item label="计划日期" name="date_range" style={{ minWidth: 260 }}>
              <DatePicker.RangePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="missing_traffic_only" valuePropName="checked">
              <Checkbox>只看未填流量</Checkbox>
            </Form.Item>
            {missingTrafficOnly && (
              <Form.Item label="流量日期" name="traffic_date" style={{ minWidth: 180 }}>
                <DatePicker allowClear={false} style={{ width: '100%' }} />
              </Form.Item>
            )}
            <Form.Item>
              <Space>
                <Button type="primary" onClick={handleApplyFilters}>
                  筛选
                </Button>
                <Button onClick={handleResetFilters}>
                  重置
                </Button>
              </Space>
            </Form.Item>
          </Flex>
        </Form>
      </Card>

      {view === 'users' && (
        <Table
          rowKey="user_id"
          loading={loading}
          columns={visibleUserColumns}
          dataSource={users}
          expandable={{
            expandedRowRender: (record) => (
              <Flex vertical gap={12} style={{ minWidth: 0, width: '100%', overflow: 'hidden' }}>
                <Table
                  rowKey="account_id"
                  columns={buildPlatformColumns(record)}
                  dataSource={record.platform_summaries}
                  pagination={false}
                  size="small"
                  tableLayout="fixed"
                  scroll={tableScroll(buildPlatformColumns(record))}
                />
                <Table
                  rowKey="id"
                  columns={expandedUserArticleColumns}
                  dataSource={record.articles}
                  pagination={false}
                  size="small"
                  tableLayout="fixed"
                  scroll={tableScroll(expandedUserArticleColumns)}
                />
              </Flex>
            ),
          }}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无用户数据" /> }}
          pagination={pagination}
          tableLayout="fixed"
          scroll={tableScroll(visibleUserColumns)}
        />
      )}

      {view === 'articles' && (
        <Table
          rowKey="id"
          loading={loading}
          columns={visibleArticleColumns}
          dataSource={articles}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无文章数据" /> }}
          pagination={pagination}
          tableLayout="fixed"
          scroll={tableScroll(visibleArticleColumns)}
        />
      )}

      {view === 'topics' && (
        <Table
          rowKey="key"
          loading={loading}
          columns={visibleTopicColumns}
          dataSource={topics}
          expandable={{
            expandedRowRender: (record) => (
              <Table
                rowKey="id"
                size="small"
                columns={expandedTopicArticleColumns}
                dataSource={record.articles}
                pagination={false}
                tableLayout="fixed"
                scroll={tableScroll(expandedTopicArticleColumns)}
              />
            ),
          }}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无选题数据" /> }}
          pagination={pagination}
          tableLayout="fixed"
          scroll={tableScroll(visibleTopicColumns)}
        />
      )}

      <ArticleDetailModal
        article={selectedArticle}
        onClose={() => setSelectedArticle(null)}
      />
    </Flex>
  )
}

function trafficColumn<T extends object, K extends keyof T & string>(
  title: string,
  dataIndex: K,
) {
  const valueOf = (record: T) => Number(record[dataIndex] ?? 0)
  return {
    title,
    dataIndex,
    key: dataIndex,
    width: 110,
    sorter: (a: T, b: T) => valueOf(a) - valueOf(b),
    render: (value: T[K]) => renderTrafficValue(Number(value)),
  }
}

function buildPlatformColumns(
  user: ArticleDistributionOverviewUser,
): TableColumnsType<ArticleDistributionPlatformSummary> {
  return [
    {
      title: '发布平台',
      key: 'platform',
      width: 320,
      render: (_, record) => (
        <Space>
          <Tag>{record.platform}</Tag>
          <Typography.Text type="secondary">{record.account_name}</Typography.Text>
          <Typography.Text type="secondary">{publicationTypeText[record.publication_type]}</Typography.Text>
        </Space>
      ),
    },
    {
      title: '发布数量',
      dataIndex: 'published_count',
      key: 'published_count',
      width: 120,
      render: (value: number) => <Tag color="green">{value}</Tag>,
    },
    {
      title: '剩余未发布',
      dataIndex: 'unpublished_count',
      key: 'unpublished_count',
      width: 140,
      render: (value: number) => <Tag color={value > 0 ? 'volcano' : 'default'}>{value}</Tag>,
    },
    {
      title: '失效数量',
      dataIndex: 'invalid_count',
      key: 'invalid_count',
      width: 120,
      render: (value: number) => <Tag color={value > 0 ? 'red' : 'default'}>{value}</Tag>,
    },
    {
      title: '文章链接',
      key: 'published_article_links',
      width: 140,
      render: (_, record) => renderPublishedArticleLinks(user, record),
    },
  ]
}

function renderPublishedArticleLinks(
  user: ArticleDistributionOverviewUser,
  platformSummary: ArticleDistributionPlatformSummary,
) {
  const articles = user.articles.filter(
    (article): article is ArticleDistributionOverviewArticle & { published_url: string } =>
      article.account_id === platformSummary.account_id &&
      article.publish_status === 'published' &&
      Boolean(article.published_url),
  )
  if (!articles.length) return '-'

  return (
    <Popover
      trigger="click"
      placement="bottomRight"
      title="已发布文章链接"
      content={(
        <Flex vertical gap={12} style={{ width: 420, maxWidth: '70vw', maxHeight: 360, overflow: 'auto' }}>
          {articles.map((article) => (
            <Space key={article.id} direction="vertical" size={0} style={{ minWidth: 0, width: '100%' }}>
              <Typography.Text strong ellipsis>
                {article.title}
              </Typography.Text>
              <Typography.Text type="secondary">{article.scheduled_date}</Typography.Text>
              <Typography.Link href={article.published_url} target="_blank" rel="noreferrer" ellipsis>
                {article.published_url}
              </Typography.Link>
            </Space>
          ))}
        </Flex>
      )}
    >
      <Typography.Link>查看 {articles.length} 篇</Typography.Link>
    </Popover>
  )
}

function buildArticleColumns({
  includeUser,
  includeActions,
  onSelectArticle,
}: {
  includeUser: boolean
  includeActions: boolean
  onSelectArticle: (article: ArticleDistributionOverviewArticle) => void
}): TableColumnsType<ArticleDistributionOverviewArticle> {
  const columns: TableColumnsType<ArticleDistributionOverviewArticle> = [
    {
      title: '文章',
      key: 'article',
      width: 320,
      render: (_, record) => (
        <Space direction="vertical" size={2}>
          <Typography.Text strong ellipsis style={{ maxWidth: 300 }}>
            {record.title}
          </Typography.Text>
          <Typography.Text type="secondary">
            {record.article_role ?? '-'} · {record.angle_label ?? record.audience_label ?? '-'}
          </Typography.Text>
        </Space>
      ),
    },
  ]

  if (includeUser) {
    columns.push({
      title: '用户',
      key: 'user',
      width: 240,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Typography.Text>{record.name || record.username}</Typography.Text>
          <Typography.Text type="secondary">{record.email}</Typography.Text>
        </Space>
      ),
    })
  }

  columns.push(
    {
      title: '账号',
      key: 'account',
      width: 220,
      render: (_, record) => (
        <Space>
          <Tag>{record.platform}</Tag>
          <Typography.Text type="secondary">{record.account_name}</Typography.Text>
          <Typography.Text type="secondary">{publicationTypeText[record.publication_type]}</Typography.Text>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'publish_status',
      key: 'publish_status',
      width: 110,
      render: (value: ArticlePublishStatus) => publishStatusTag(value),
    },
    {
      title: '计划日期',
      dataIndex: 'scheduled_date',
      key: 'scheduled_date',
      width: 130,
      sorter: (a, b) => a.scheduled_date.localeCompare(b.scheduled_date),
    },
    {
      title: '未填流量',
      dataIndex: 'missing_traffic',
      key: 'missing_traffic',
      width: 110,
      render: (value: boolean) => <Tag color={value ? 'orange' : 'default'}>{value ? '是' : '否'}</Tag>,
    },
    {
      title: '选题',
      key: 'topic',
      width: 220,
      render: (_, record) => record.topic || record.output_id || '-',
    },
    {
      title: '角色',
      key: 'article_role',
      width: 120,
      render: (_, record) => record.article_role ?? '-',
    },
    {
      title: '阅读量',
      key: 'read_count',
      width: 100,
      sorter: (a, b) => (a.latest_traffic_stat?.read_count ?? 0) - (b.latest_traffic_stat?.read_count ?? 0),
      render: (_, record) => renderTrafficValue(record.latest_traffic_stat?.read_count),
    },
    {
      title: '点赞量',
      key: 'like_count',
      width: 100,
      render: (_, record) => renderTrafficValue(record.latest_traffic_stat?.like_count),
    },
    {
      title: '收藏量',
      key: 'favorite_count',
      width: 100,
      render: (_, record) => renderTrafficValue(record.latest_traffic_stat?.favorite_count),
    },
    {
      title: '转发量',
      key: 'share_count',
      width: 100,
      render: (_, record) => renderTrafficValue(record.latest_traffic_stat?.share_count),
    },
    {
      title: '统计时间',
      key: 'traffic_recorded_at',
      width: 150,
      render: (_, record) => record.latest_traffic_stat
        ? dayjs(record.latest_traffic_stat.recorded_at).format('YYYY-MM-DD HH:mm')
        : '-',
    },
    {
      title: '发布链接',
      dataIndex: 'published_url',
      key: 'published_url',
      width: 110,
      render: (value: string | null) => value ? (
        <Typography.Link href={value} target="_blank" rel="noreferrer">
          检查
        </Typography.Link>
      ) : '-',
    },
  )

  if (includeActions) {
    columns.push({
      title: '操作',
      key: 'actions',
      fixed: 'right',
      width: 90,
      render: (_, record) => (
        <Button size="small" onClick={() => onSelectArticle(record)}>
          详情
        </Button>
      ),
    })
  }
  return columns
}

function ArticleDetailModal({
  article,
  onClose,
}: {
  article: ArticleDistributionOverviewArticle | null
  onClose: () => void
}) {
  if (!article) return null

  return (
    <Modal
      open
      width="min(96vw, 1180px)"
      title={article.title}
      footer={null}
      onCancel={onClose}
      destroyOnClose
    >
      <Flex vertical gap={14}>
        <Descriptions size="small" column={{ xs: 1, sm: 2, md: 4 }}>
          <Descriptions.Item label="文章 ID">{article.id}</Descriptions.Item>
          <Descriptions.Item label="用户">{article.name || article.username}</Descriptions.Item>
          <Descriptions.Item label="账号">{article.platform} / {article.account_name}</Descriptions.Item>
          <Descriptions.Item label="发布类型">{publicationTypeText[article.publication_type]}</Descriptions.Item>
          <Descriptions.Item label="计划日期">{article.scheduled_date}</Descriptions.Item>
          <Descriptions.Item label="文章角色">{article.article_role ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="角度">{article.angle_label ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="受众">{article.audience_label ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="状态">{publishStatusTag(article.publish_status)}</Descriptions.Item>
          <Descriptions.Item label="未填流量">{article.missing_traffic ? '是' : '否'}</Descriptions.Item>
          <Descriptions.Item label="阅读量">{renderTrafficValue(article.latest_traffic_stat?.read_count)}</Descriptions.Item>
          <Descriptions.Item label="点赞量">{renderTrafficValue(article.latest_traffic_stat?.like_count)}</Descriptions.Item>
          <Descriptions.Item label="收藏量">{renderTrafficValue(article.latest_traffic_stat?.favorite_count)}</Descriptions.Item>
          <Descriptions.Item label="转发量">{renderTrafficValue(article.latest_traffic_stat?.share_count)}</Descriptions.Item>
          <Descriptions.Item label="发布链接">
            {article.published_url ? (
              <Typography.Link href={article.published_url} target="_blank" rel="noreferrer">
                检查
              </Typography.Link>
            ) : '-'}
          </Descriptions.Item>
        </Descriptions>
        <div>
          <Typography.Text strong>痛点解决方案</Typography.Text>
          <Typography.Paragraph style={{ margin: '6px 0 0' }}>
            {article.summary || '-'}
          </Typography.Paragraph>
        </div>
        <Tabs
          items={[
            {
              key: 'preview',
              label: '正文预览',
              children: (
                <div style={{ maxHeight: '60vh', overflow: 'auto', paddingRight: 8 }}>
                  <MarkdownArticleViewer markdown={article.markdown_content} />
                </div>
              ),
            },
            {
              key: 'source',
              label: '正文源码',
              children: <PreBlock content={article.markdown_content} maxHeight="60vh" />,
            },
            {
              key: 'metadata',
              label: '元数据',
              children: <PreBlock content={JSON.stringify(article.metadata ?? {}, null, 2)} maxHeight="60vh" />,
            },
          ]}
        />
      </Flex>
    </Modal>
  )
}

function PreBlock({ content, maxHeight }: { content: string; maxHeight: string }) {
  return (
    <pre
      style={{
        margin: 0,
        boxSizing: 'border-box',
        maxWidth: '100%',
        maxHeight,
        overflow: 'auto',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        padding: 12,
        borderRadius: 6,
        background: 'var(--ant-color-fill-quaternary)',
      }}
    >
      {content}
    </pre>
  )
}

function renderMaterials(materials: string[]) {
  if (!materials.length) return '-'
  const visible = materials.slice(0, 2)
  return (
    <Space direction="vertical" size={2}>
      {visible.map((material) => (
        <Typography.Text key={material} ellipsis style={{ maxWidth: 280 }}>
          {material}
        </Typography.Text>
      ))}
      {materials.length > visible.length && (
        <Typography.Text type="secondary">另 {materials.length - visible.length} 条</Typography.Text>
      )}
    </Space>
  )
}
