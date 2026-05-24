import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  App,
  Button,
  Card,
  DatePicker,
  Descriptions,
  Empty,
  Flex,
  Form,
  Input,
  Popover,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { TableColumnsType, TablePaginationConfig } from 'antd'
import { ReloadOutlined, SearchOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import * as articleApi from '../../lib/articleDistribution'
import type {
  ArticleDistributionAccountStatusFilter,
  ArticleDistributionPendingArticle,
  ArticleDistributionPendingReportFilters,
  ArticleDistributionPendingUser,
  ArticleDistributionPlatformSummary,
  ArticleDistributionReportSummary,
  ArticlePublicationType,
  ArticlePublishStatus,
} from '../../lib/types'
import { resolveApiErrorMessage } from '../../lib/error'

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

function inactiveAccountTag(isActive?: boolean) {
  return isActive === false ? <Tag color="red">已停用</Tag> : null
}

function renderTrafficValue(value: number | undefined) {
  return typeof value === 'number' ? value : '-'
}

const emptySummary: ArticleDistributionReportSummary = {
  total_users: 0,
  unpublished_users: 0,
  published_articles: 0,
  unpublished_articles: 0,
  invalid_articles: 0,
  inactive_account_articles: 0,
}

interface FilterValues {
  keyword?: string
  platform?: string
  publication_type?: ArticlePublicationType
  account_status?: ArticleDistributionAccountStatusFilter
  date_range?: [dayjs.Dayjs, dayjs.Dayjs]
}

export default function ArticleDistributionReportPage() {
  const { message } = App.useApp()
  const [form] = Form.useForm<FilterValues>()
  const [loading, setLoading] = useState(false)
  const [rows, setRows] = useState<ArticleDistributionPendingUser[]>([])
  const [summary, setSummary] = useState<ArticleDistributionReportSummary>(emptySummary)
  const [userDetails, setUserDetails] = useState<Record<number, ArticleDistributionPendingUser>>({})
  const [detailLoadingUserIds, setDetailLoadingUserIds] = useState<Set<number>>(() => new Set())
  const [expandedRowKeys, setExpandedRowKeys] = useState<number[]>([])

  const loadReport = useCallback(async (filters?: ArticleDistributionPendingReportFilters) => {
    setLoading(true)
    try {
      const report = await articleApi.listUnpublishedArticleReport(filters)
      setRows(report.users)
      setSummary(report.summary)
      setUserDetails({})
      setExpandedRowKeys([])
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '分发进度加载失败'))
    } finally {
      setLoading(false)
    }
  }, [message])

  const loadUserDetail = useCallback(async (userId: number) => {
    setDetailLoadingUserIds((current) => new Set(current).add(userId))
    try {
      const detail = await articleApi.getUnpublishedArticleReportUser(userId, buildFilters())
      setUserDetails((current) => ({ ...current, [userId]: detail }))
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '用户分发明细加载失败'))
    } finally {
      setDetailLoadingUserIds((current) => {
        const next = new Set(current)
        next.delete(userId)
        return next
      })
    }
  }, [message])

  useEffect(() => {
    void loadReport()
  }, [loadReport])

  const buildFilters = (): ArticleDistributionPendingReportFilters => {
    const values = form.getFieldsValue()
    const range = values.date_range
    return {
      platform: values.platform?.trim() || undefined,
      publication_type: values.publication_type,
      account_status: values.account_status ?? 'active',
      scheduled_from: range?.[0]?.format('YYYY-MM-DD'),
      scheduled_to: range?.[1]?.format('YYYY-MM-DD'),
    }
  }

  const keyword = Form.useWatch('keyword', form)
  const filteredRows = useMemo(() => {
    const normalized = keyword?.trim().toLowerCase()
    if (!normalized) {
      return rows
    }
    return rows.filter((row) =>
      [
        row.username,
        row.name ?? '',
        row.email,
      ].join(' ').toLowerCase().includes(normalized),
    )
  }, [keyword, rows])

  const filteredSummary = useMemo<ArticleDistributionReportSummary>(() => {
    if (filteredRows.length === rows.length) return summary
    return {
      total_users: filteredRows.length,
      unpublished_users: filteredRows.filter((row) => row.remaining_count > 0).length,
      published_articles: filteredRows.reduce((total, row) => total + row.published_count, 0),
      unpublished_articles: filteredRows.reduce((total, row) => total + row.remaining_count, 0),
      invalid_articles: filteredRows.reduce((total, row) => total + row.invalid_count, 0),
      inactive_account_articles: filteredRows.reduce(
        (total, row) => total + row.inactive_account_articles,
        0,
      ),
    }
  }, [filteredRows, rows.length, summary])

  const userPagination = useMemo<TablePaginationConfig>(() => ({
    pageSize: 10,
    pageSizeOptions: [10, 20, 50, 100],
    showSizeChanger: true,
    hideOnSinglePage: false,
    responsive: true,
    showTotal: (total, range) => `第 ${range[0]}-${range[1]} 位，共 ${total} 人`,
    total: filteredRows.length,
  }), [filteredRows.length])

  const userColumns: TableColumnsType<ArticleDistributionPendingUser> = [
    {
      title: '用户',
      key: 'user',
      width: 360,
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
      width: 160,
      sorter: (a, b) => a.remaining_count - b.remaining_count,
      render: (value: number) => <Tag color={value > 0 ? 'volcano' : 'default'}>{value} 篇</Tag>,
    },
    {
      title: '已发布',
      dataIndex: 'published_count',
      key: 'published_count',
      width: 160,
      sorter: (a, b) => a.published_count - b.published_count,
      render: (value: number) => <Tag color="green">{value} 篇</Tag>,
    },
    {
      title: '失效',
      dataIndex: 'invalid_count',
      key: 'invalid_count',
      width: 160,
      sorter: (a, b) => a.invalid_count - b.invalid_count,
      render: (value: number) => <Tag color={value > 0 ? 'red' : 'default'}>{value} 篇</Tag>,
    },
  ]

  const articleColumns: TableColumnsType<ArticleDistributionPendingArticle> = [
    {
      title: '文章',
      dataIndex: 'title',
      key: 'title',
      width: 520,
      ellipsis: true,
      render: (value: string) => <Typography.Text strong ellipsis>{value}</Typography.Text>,
    },
    {
      title: '状态',
      dataIndex: 'publish_status',
      key: 'publish_status',
      width: 120,
      render: (value: ArticlePublishStatus) => publishStatusTag(value),
    },
    {
      title: '计划日期',
      dataIndex: 'scheduled_date',
      key: 'scheduled_date',
      width: 150,
      sorter: (a, b) => a.scheduled_date.localeCompare(b.scheduled_date),
    },
    {
      title: '目标平台',
      dataIndex: 'platform',
      key: 'platform',
      width: 140,
      render: (value: string) => <Tag>{value}</Tag>,
    },
    {
      title: '目标账号',
      dataIndex: 'account_name',
      key: 'account_name',
      width: 140,
      ellipsis: true,
      render: (value: string, record) => (
        <Space size={4}>
          <Typography.Text ellipsis>{value}</Typography.Text>
          {inactiveAccountTag(record.account_is_active)}
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'publication_type',
      key: 'publication_type',
      width: 100,
      render: (value: ArticlePublicationType) => publicationTypeText[value],
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
      sorter: (a, b) => (a.latest_traffic_stat?.like_count ?? 0) - (b.latest_traffic_stat?.like_count ?? 0),
      render: (_, record) => renderTrafficValue(record.latest_traffic_stat?.like_count),
    },
    {
      title: '收藏量',
      key: 'favorite_count',
      width: 100,
      sorter: (a, b) => (a.latest_traffic_stat?.favorite_count ?? 0) - (b.latest_traffic_stat?.favorite_count ?? 0),
      render: (_, record) => renderTrafficValue(record.latest_traffic_stat?.favorite_count),
    },
    {
      title: '转发量',
      key: 'share_count',
      width: 100,
      sorter: (a, b) => (a.latest_traffic_stat?.share_count ?? 0) - (b.latest_traffic_stat?.share_count ?? 0),
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
      width: 120,
      render: (value: string | null) => value ? (
        <Typography.Link href={value} target="_blank" rel="noreferrer">
          检查
        </Typography.Link>
      ) : '-',
    },
  ]

  const buildPlatformColumns = (
    user: ArticleDistributionPendingUser,
  ): TableColumnsType<ArticleDistributionPlatformSummary> => [
      {
        title: '发布平台',
        key: 'platform',
        width: 360,
        render: (_, record) => (
          <Space>
            <Tag>{record.platform}</Tag>
            <Typography.Text>{record.account_name}</Typography.Text>
            {inactiveAccountTag(record.account_is_active)}
            <Typography.Text type="secondary">{publicationTypeText[record.publication_type]}</Typography.Text>
          </Space>
        ),
      },
      {
        title: '发布数量',
        dataIndex: 'published_count',
        key: 'published_count',
        width: 140,
        render: (value: number) => <Tag color="green">{value}</Tag>,
      },
      {
        title: '剩余未发布',
        dataIndex: 'unpublished_count',
        key: 'unpublished_count',
        width: 160,
        render: (value: number) => <Tag color={value > 0 ? 'volcano' : 'default'}>{value}</Tag>,
      },
      {
        title: '失效数量',
        dataIndex: 'invalid_count',
        key: 'invalid_count',
        width: 140,
        render: (value: number) => <Tag color={value > 0 ? 'red' : 'default'}>{value}</Tag>,
      },
      {
        title: '文章链接',
        key: 'published_article_links',
        width: 160,
        render: (_, record) => renderPublishedArticleLinks(user, record),
      },
    ]

  const renderPublishedArticleLinks = (
    user: ArticleDistributionPendingUser,
    platformSummary: ArticleDistributionPlatformSummary,
  ) => {
    const articles = user.articles.filter(
      (article): article is ArticleDistributionPendingArticle & { published_url: string } =>
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

  const renderArticleDetail = (article: ArticleDistributionPendingArticle) => (
    <Flex vertical gap={12} style={{ minWidth: 0, width: '100%', overflow: 'hidden' }}>
      <Descriptions size="small" column={{ xs: 1, sm: 2, md: 4 }}>
        <Descriptions.Item label="目标平台">{article.platform}</Descriptions.Item>
        <Descriptions.Item label="目标账号">
          <Space size={4}>
            <span>{article.account_name}</span>
            {inactiveAccountTag(article.account_is_active)}
          </Space>
        </Descriptions.Item>
        <Descriptions.Item label="发布类型">
          {publicationTypeText[article.publication_type]}
        </Descriptions.Item>
        <Descriptions.Item label="计划日期">{article.scheduled_date}</Descriptions.Item>
        <Descriptions.Item label="状态">{publishStatusTag(article.publish_status)}</Descriptions.Item>
        <Descriptions.Item label="阅读量">{renderTrafficValue(article.latest_traffic_stat?.read_count)}</Descriptions.Item>
        <Descriptions.Item label="点赞量">{renderTrafficValue(article.latest_traffic_stat?.like_count)}</Descriptions.Item>
        <Descriptions.Item label="收藏量">{renderTrafficValue(article.latest_traffic_stat?.favorite_count)}</Descriptions.Item>
        <Descriptions.Item label="转发量">{renderTrafficValue(article.latest_traffic_stat?.share_count)}</Descriptions.Item>
        <Descriptions.Item label="统计时间">
          {article.latest_traffic_stat ? dayjs(article.latest_traffic_stat.recorded_at).format('YYYY-MM-DD HH:mm') : '-'}
        </Descriptions.Item>
        <Descriptions.Item label="发布链接">
          {article.published_url ? (
            <Typography.Link href={article.published_url} target="_blank" rel="noreferrer">
              检查
            </Typography.Link>
          ) : '-'}
        </Descriptions.Item>
      </Descriptions>
      <Typography.Text strong>{article.title}</Typography.Text>
      <pre
        style={{
          margin: 0,
          boxSizing: 'border-box',
          maxWidth: '100%',
          maxHeight: 360,
          overflow: 'auto',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          padding: 12,
          borderRadius: 6,
          background: 'var(--ant-color-fill-quaternary)',
        }}
      >
        {article.markdown_content}
      </pre>
    </Flex>
  )

  const expandedArticleTable = (record: ArticleDistributionPendingUser) => {
    const detail = userDetails[record.user_id]
    const loadingDetail = detailLoadingUserIds.has(record.user_id)

    if (!detail && !loadingDetail) {
      return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="展开后加载明细" />
    }

    return (
      <Flex vertical gap={12} style={{ minWidth: 0, width: '100%', overflow: 'hidden' }}>
        <Table
          rowKey="account_id"
          columns={buildPlatformColumns(detail ?? record)}
          dataSource={detail?.platform_summaries ?? []}
          pagination={false}
          size="small"
          tableLayout="fixed"
          loading={loadingDetail}
          scroll={{ x: 960 }}
        />
        <Table
          rowKey="id"
          columns={articleColumns}
          dataSource={detail?.articles ?? []}
          pagination={false}
          size="small"
          tableLayout="fixed"
          loading={loadingDetail}
          scroll={{ x: 1790 }}
          expandable={{
            expandedRowRender: renderArticleDetail,
          }}
        />
      </Flex>
    )
  }

  return (
    <Flex vertical gap={18}>
      <Flex align="center" justify="space-between" gap={16} wrap="wrap">
        <div>
          <Typography.Title level={2} style={{ margin: 0 }}>
            分发进度后台
          </Typography.Title>
          <Typography.Text type="secondary">
            查看所有用户的文章发布进度、失效文档和发布链接核验入口。
          </Typography.Text>
        </div>
        <Button
          icon={<ReloadOutlined />}
          loading={loading}
          onClick={() => void loadReport(buildFilters())}
        >
          刷新
        </Button>
      </Flex>

      <Card>
        <Flex gap={24} wrap="wrap">
          <Statistic title="总人数" value={filteredSummary.total_users} />
          <Statistic title="未发布人数" value={filteredSummary.unpublished_users} />
          <Statistic title="发布的文章总数" value={filteredSummary.published_articles} />
          <Statistic title="未发布文章总数" value={filteredSummary.unpublished_articles} />
          <Statistic title="已停用账号文章总数" value={filteredSummary.inactive_account_articles} />
          <Statistic title="失效文章总数" value={filteredSummary.invalid_articles} />
        </Flex>
        <Form form={form} layout="vertical" initialValues={{ account_status: 'active' }} style={{ marginTop: 18 }}>
          <Flex gap={16} wrap="wrap" align="end">
            <Form.Item label="搜索" name="keyword" style={{ minWidth: 240 }}>
              <Input prefix={<SearchOutlined />} allowClear placeholder="用户、账号或文章" />
            </Form.Item>
            <Form.Item label="平台" name="platform" style={{ minWidth: 180 }}>
              <Input allowClear placeholder="wechat、zhihu..." />
            </Form.Item>
            <Form.Item label="发布类型" name="publication_type" style={{ minWidth: 160 }}>
              <Select allowClear options={publicationTypeOptions} placeholder="全部类型" />
            </Form.Item>
            <Form.Item label="账号类型" name="account_status" style={{ minWidth: 140 }}>
              <Select options={accountStatusOptions} />
            </Form.Item>
            <Form.Item label="计划日期" name="date_range" style={{ minWidth: 260 }}>
              <DatePicker.RangePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button type="primary" onClick={() => void loadReport(buildFilters())}>
                  筛选
                </Button>
                <Button
                  onClick={() => {
                    form.resetFields()
                    void loadReport()
                  }}
                >
                  重置
                </Button>
              </Space>
            </Form.Item>
          </Flex>
        </Form>
      </Card>

      <Table
        rowKey="user_id"
        loading={loading}
        columns={userColumns}
        dataSource={filteredRows}
        expandable={{
          expandedRowRender: expandedArticleTable,
          expandedRowKeys,
          onExpand: (expanded, record) => {
            setExpandedRowKeys((current) => (
              expanded
                ? [...current, record.user_id]
                : current.filter((key) => key !== record.user_id)
            ))
            if (expanded && !userDetails[record.user_id]) {
              void loadUserDetail(record.user_id)
            }
          },
        }}
        locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无文章" /> }}
        pagination={userPagination}
        tableLayout="fixed"
        scroll={{ x: 840 }}
      />
    </Flex>
  )
}
