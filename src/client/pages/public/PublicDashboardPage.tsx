import { useCallback, useEffect, useState } from 'react'
import {
  App,
  Button,
  Card,
  DatePicker,
  Empty,
  Flex,
  Form,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { TableColumnsType } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import * as articleApi from '../../lib/articleDistribution'
import { resolveApiErrorMessage } from '../../lib/error'
import type {
  ArticleDistributionPendingReportFilters,
  ArticleDistributionPublicArticle,
  ArticleDistributionReportSummary,
  ArticlePublicationType,
} from '../../lib/types'

const defaultPageSize = 10

const publicationTypeOptions = [
  { label: '视频', value: 'video' },
  { label: '文章', value: 'article' },
  { label: '图文', value: 'image_text' },
]

const publicationTypeText: Record<ArticlePublicationType, string> = {
  video: '视频',
  article: '文章',
  image_text: '图文',
}

const emptySummary: ArticleDistributionReportSummary = {
  total_users: 0,
  unpublished_users: 0,
  published_articles: 0,
  unpublished_articles: 0,
  invalid_articles: 0,
  inactive_account_articles: 0,
  read_count: 0,
  like_count: 0,
  favorite_count: 0,
  share_count: 0,
}

interface FilterValues {
  publication_type?: ArticlePublicationType
  date_range?: [dayjs.Dayjs, dayjs.Dayjs]
}

export default function PublicDashboardPage() {
  const { message } = App.useApp()
  const [form] = Form.useForm<FilterValues>()
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState<ArticleDistributionReportSummary>(emptySummary)
  const [articles, setArticles] = useState<ArticleDistributionPublicArticle[]>([])
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(defaultPageSize)
  const [total, setTotal] = useState(0)

  const buildFilters = (): Pick<ArticleDistributionPendingReportFilters, 'scheduled_from' | 'scheduled_to' | 'publication_type'> => {
    const values = form.getFieldsValue()
    const range = values.date_range
    return {
      publication_type: values.publication_type,
      scheduled_from: range?.[0]?.format('YYYY-MM-DD'),
      scheduled_to: range?.[1]?.format('YYYY-MM-DD'),
    }
  }

  const loadDashboard = useCallback(async (
    filters?: Pick<ArticleDistributionPendingReportFilters, 'scheduled_from' | 'scheduled_to' | 'publication_type'>,
    pagination: { page: number; pageSize: number } = { page: 1, pageSize: defaultPageSize },
  ) => {
    setLoading(true)
    try {
      const dashboard = await articleApi.listPublicArticleDashboard({
        ...filters,
        page: pagination.page,
        page_size: pagination.pageSize,
      })
      setSummary(dashboard.summary)
      setArticles(dashboard.articles)
      setPage(dashboard.page)
      setPageSize(dashboard.page_size)
      setTotal(dashboard.total)
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '公开看板加载失败'))
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    void loadDashboard()
  }, [loadDashboard])

  const columns: TableColumnsType<ArticleDistributionPublicArticle> = [
    {
      title: '文章标题',
      dataIndex: 'title',
      key: 'title',
      width: 360,
      ellipsis: true,
      render: (value: string) => <Typography.Text strong ellipsis>{value}</Typography.Text>,
    },
    {
      title: '发布时间',
      dataIndex: 'published_at',
      key: 'published_at',
      width: 140,
      sorter: (a, b) => a.published_at.localeCompare(b.published_at),
    },
    {
      title: '发布类型',
      dataIndex: 'publication_type',
      key: 'publication_type',
      width: 110,
      render: (value: ArticlePublicationType) => publicationTypeText[value],
    },
    {
      title: '平台',
      dataIndex: 'platform',
      key: 'platform',
      width: 130,
      render: (value: string) => <Tag>{value}</Tag>,
    },
    {
      title: '链接',
      dataIndex: 'published_url',
      key: 'published_url',
      width: 110,
      fixed: 'right',
      render: (value: string) => (
        <Typography.Link href={value} target="_blank" rel="noreferrer">
          打开
        </Typography.Link>
      ),
    },
  ]

  return (
    <div style={{ minHeight: '100vh', padding: '24px 16px 48px', background: 'var(--app-bg)' }}>
      <Flex vertical gap={18} style={{ maxWidth: 1180, margin: '0 auto' }}>
        <Flex align="center" justify="space-between" gap={16} wrap="wrap">
          <div>
            <Typography.Title level={2} style={{ margin: 0 }}>
              分发公开看板
            </Typography.Title>
            <Typography.Text type="secondary">
              查看已发布文章与分发进度统计。
            </Typography.Text>
          </div>
          <Button icon={<ReloadOutlined />} loading={loading} onClick={() => void loadDashboard(buildFilters(), { page, pageSize })}>
            刷新
          </Button>
        </Flex>

        <Card>
          <Flex gap={24} wrap="wrap">
            <Statistic title="发布的文章总数" value={summary.published_articles} />
            <Statistic title="未发布的文章总数" value={summary.unpublished_articles} />
          </Flex>

          <Form form={form} layout="vertical" style={{ marginTop: 18 }}>
            <Flex gap={16} wrap="wrap" align="end">
              <Form.Item label="发布类型" name="publication_type" style={{ minWidth: 180 }}>
                <Select allowClear options={publicationTypeOptions} placeholder="全部类型" />
              </Form.Item>
              <Form.Item label="发布时间" name="date_range" style={{ minWidth: 260 }}>
                <DatePicker.RangePicker style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item>
                <Space>
                  <Button type="primary" onClick={() => void loadDashboard(buildFilters(), { page: 1, pageSize })}>
                    筛选
                  </Button>
                  <Button
                    onClick={() => {
                      form.resetFields()
                      void loadDashboard(undefined, { page: 1, pageSize })
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
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={articles}
          tableLayout="fixed"
          scroll={{ x: 850 }}
          pagination={{
            current: page,
            pageSize,
            total,
            pageSizeOptions: [10, 20, 50, 100],
            showSizeChanger: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 篇，共 ${total} 篇`,
            onChange: (nextPage, nextPageSize) => void loadDashboard(
              buildFilters(),
              { page: nextPage, pageSize: nextPageSize },
            ),
          }}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无已发布文章" /> }}
        />
      </Flex>
    </div>
  )
}
