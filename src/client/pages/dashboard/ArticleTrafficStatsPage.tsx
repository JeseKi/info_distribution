import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  App,
  Button,
  Card,
  DatePicker,
  Empty,
  Flex,
  Form,
  InputNumber,
  Modal,
  Pagination,
  Popconfirm,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { TableColumnsType } from 'antd'
import {
  CommentOutlined,
  DeleteOutlined,
  LineChartOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import * as articleApi from '../../lib/articleDistribution'
import { resolveApiErrorMessage } from '../../lib/error'
import type {
  ArticleDistributionAccount,
  ArticleDistributionArticleFilters,
  ArticleDistributionTrafficStat,
  ArticleDistributionTrafficStatPayload,
  ArticleDistributionTrafficSummary,
  ArticlePublicationType,
  ArticlePublishStatus,
} from '../../lib/types'

const defaultPageSize = 10

const publicationTypeText: Record<ArticlePublicationType, string> = {
  video: '视频',
  article: '文章',
  image_text: '图文',
}

const publishStatusOptions = [
  { label: '未发布', value: 'unpublished' },
  { label: '已发布', value: 'published' },
  { label: '文档失效', value: 'invalid' },
]

function publishStatusTag(status: ArticlePublishStatus) {
  if (status === 'published') return <Tag color="green">已发布</Tag>
  if (status === 'invalid') return <Tag color="red">文档失效</Tag>
  return <Tag>未发布</Tag>
}

interface FilterValues {
  account_id?: number
  publish_status?: ArticlePublishStatus
  date_range?: [dayjs.Dayjs, dayjs.Dayjs]
}

interface StatFormValues {
  read_count: number
  like_count: number
  favorite_count: number
  share_count: number
  comment_count: number
  recorded_at: dayjs.Dayjs
}

export default function ArticleTrafficStatsPage() {
  const { message } = App.useApp()
  const [filterForm] = Form.useForm<FilterValues>()
  const [statForm] = Form.useForm<StatFormValues>()
  const [accounts, setAccounts] = useState<ArticleDistributionAccount[]>([])
  const [items, setItems] = useState<ArticleDistributionTrafficSummary[]>([])
  const [history, setHistory] = useState<ArticleDistributionTrafficStat[]>([])
  const [loading, setLoading] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [selectedSummary, setSelectedSummary] = useState<ArticleDistributionTrafficSummary | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(defaultPageSize)
  const [total, setTotal] = useState(0)

  const accountOptions = useMemo(
    () => accounts.map((account) => ({
      label: `${account.platform} / ${account.account_name} / ${publicationTypeText[account.publication_type]}`,
      value: account.id,
    })),
    [accounts],
  )

  const totals = useMemo(() => items.reduce(
    (acc, item) => {
      const stat = item.latest_stat
      if (!stat) return acc
      return {
        read_count: acc.read_count + stat.read_count,
        like_count: acc.like_count + stat.like_count,
        favorite_count: acc.favorite_count + stat.favorite_count,
        share_count: acc.share_count + stat.share_count,
        comment_count:
          acc.comment_count + stat.comment_count,
      }
    },
    {
      read_count: 0,
      like_count: 0,
      favorite_count: 0,
      share_count: 0,
      comment_count: 0,
    },
  ), [items])

  const buildFilters = (): ArticleDistributionArticleFilters => {
    const values = filterForm.getFieldsValue()
    const range = values.date_range
    return {
      account_id: values.account_id,
      publish_status: values.publish_status,
      scheduled_from: range?.[0]?.format('YYYY-MM-DD'),
      scheduled_to: range?.[1]?.format('YYYY-MM-DD'),
    }
  }

  const loadData = useCallback(async (
    filters?: ArticleDistributionArticleFilters,
    pagination: { page: number; pageSize: number } = { page: 1, pageSize: defaultPageSize },
  ) => {
    setLoading(true)
    try {
      const [nextAccounts, nextPage] = await Promise.all([
        articleApi.listArticleAccounts(),
        articleApi.listArticleTrafficSummaries({
          ...filters,
          page: pagination.page,
          page_size: pagination.pageSize,
        }),
      ])
      setAccounts(nextAccounts)
      setItems(nextPage.items)
      setTotal(nextPage.total)
      setPage(nextPage.page)
      setPageSize(nextPage.page_size)
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '流量统计加载失败'))
    } finally {
      setLoading(false)
    }
  }, [message])

  const loadHistory = useCallback(async (articleId: number) => {
    setHistoryLoading(true)
    try {
      setHistory(await articleApi.listArticleTrafficStats(articleId))
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '统计记录加载失败'))
    } finally {
      setHistoryLoading(false)
    }
  }, [message])

  useEffect(() => {
    void loadData(undefined, { page: 1, pageSize: defaultPageSize })
  }, [loadData])

  const openStatModal = (summary: ArticleDistributionTrafficSummary) => {
    setSelectedSummary(summary)
    setModalOpen(true)
    statForm.setFieldsValue({
      read_count: summary.latest_stat?.read_count ?? 0,
      like_count: summary.latest_stat?.like_count ?? 0,
      favorite_count: summary.latest_stat?.favorite_count ?? 0,
      share_count: summary.latest_stat?.share_count ?? 0,
      comment_count: summary.latest_stat?.comment_count ?? 0,
      recorded_at: dayjs(),
    })
    void loadHistory(summary.article.id)
  }

  const handleCreateStat = async (values: StatFormValues) => {
    if (!selectedSummary) return
    const payload: ArticleDistributionTrafficStatPayload = {
      read_count: values.read_count ?? 0,
      like_count: values.like_count ?? 0,
      favorite_count: values.favorite_count ?? 0,
      share_count: values.share_count ?? 0,
      comment_count: values.comment_count ?? 0,
      recorded_at: values.recorded_at?.toISOString(),
    }
    setSaving(true)
    try {
      await articleApi.createArticleTrafficStat(selectedSummary.article.id, payload)
      message.success('统计记录已添加')
      await Promise.all([
        loadHistory(selectedSummary.article.id),
        loadData(buildFilters(), { page, pageSize }),
      ])
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '统计记录保存失败'))
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteStat = async (statId: number) => {
    if (!selectedSummary) return
    try {
      await articleApi.deleteArticleTrafficStat(statId)
      message.success('统计记录已删除')
      await Promise.all([
        loadHistory(selectedSummary.article.id),
        loadData(buildFilters(), { page, pageSize }),
      ])
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '统计记录删除失败'))
    }
  }

  const columns: TableColumnsType<ArticleDistributionTrafficSummary> = [
    {
      title: '文章',
      key: 'article',
      width: 320,
      render: (_, record) => (
        <Space direction="vertical" size={2}>
          <Typography.Text strong ellipsis style={{ maxWidth: 300 }}>{record.article.title}</Typography.Text>
          <Typography.Text type="secondary">
            {record.article.scheduled_date} · {record.article.account?.platform ?? '-'} / {record.article.account?.account_name ?? record.article.account_id}
          </Typography.Text>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: ['article', 'publish_status'],
      key: 'publish_status',
      width: 110,
      render: (value: ArticlePublishStatus) => publishStatusTag(value),
    },
    {
      title: '阅读量',
      key: 'read_count',
      width: 110,
      sorter: (a, b) => (a.latest_stat?.read_count ?? 0) - (b.latest_stat?.read_count ?? 0),
      render: (_, record) => record.latest_stat?.read_count ?? '-',
    },
    {
      title: '点赞量',
      key: 'like_count',
      width: 110,
      sorter: (a, b) => (a.latest_stat?.like_count ?? 0) - (b.latest_stat?.like_count ?? 0),
      render: (_, record) => record.latest_stat?.like_count ?? '-',
    },
    {
      title: '收藏量',
      key: 'favorite_count',
      width: 110,
      sorter: (a, b) => (a.latest_stat?.favorite_count ?? 0) - (b.latest_stat?.favorite_count ?? 0),
      render: (_, record) => record.latest_stat?.favorite_count ?? '-',
    },
    {
      title: '转发量',
      key: 'share_count',
      width: 110,
      sorter: (a, b) => (a.latest_stat?.share_count ?? 0) - (b.latest_stat?.share_count ?? 0),
      render: (_, record) => record.latest_stat?.share_count ?? '-',
    },
    {
      title: '评论量',
      key: 'comment_count',
      width: 130,
      sorter: (a, b) => (
        (a.latest_stat?.comment_count ?? 0)
        - (b.latest_stat?.comment_count ?? 0)
      ),
      render: (_, record) => record.latest_stat?.comment_count ?? '-',
    },
    {
      title: '记录时间',
      key: 'recorded_at',
      width: 180,
      render: (_, record) => record.latest_stat ? dayjs(record.latest_stat.recorded_at).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '历史',
      dataIndex: 'record_count',
      key: 'record_count',
      width: 90,
      render: (value: number) => <Tag>{value} 条</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right',
      width: 130,
      render: (_, record) => (
        <Button icon={<PlusOutlined />} onClick={() => openStatModal(record)}>
          添加数据
        </Button>
      ),
    },
  ]

  const historyColumns: TableColumnsType<ArticleDistributionTrafficStat> = [
    {
      title: '记录时间',
      dataIndex: 'recorded_at',
      key: 'recorded_at',
      width: 180,
      render: (value: string) => dayjs(value).format('YYYY-MM-DD HH:mm:ss'),
    },
    { title: '阅读量', dataIndex: 'read_count', key: 'read_count', width: 100 },
    { title: '点赞量', dataIndex: 'like_count', key: 'like_count', width: 100 },
    { title: '收藏量', dataIndex: 'favorite_count', key: 'favorite_count', width: 100 },
    { title: '转发量', dataIndex: 'share_count', key: 'share_count', width: 100 },
    {
      title: '评论量',
      dataIndex: 'comment_count',
      key: 'comment_count',
      width: 120,
    },
    {
      title: '操作',
      key: 'actions',
      width: 90,
      render: (_, record) => (
        <Popconfirm title="删除这条统计记录？" onConfirm={() => void handleDeleteStat(record.id)}>
          <Button danger size="small" icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ]

  return (
    <Flex vertical gap={18}>
      <Flex align="center" justify="space-between" gap={16} wrap="wrap">
        <div>
          <Typography.Title level={2} style={{ margin: 0 }}>
            流量统计
          </Typography.Title>
          <Typography.Text type="secondary">
            按文章记录阅读、点赞、收藏、转发和评论数据。
          </Typography.Text>
        </div>
        <Button icon={<ReloadOutlined />} loading={loading} onClick={() => void loadData(buildFilters(), { page, pageSize })}>
          刷新
        </Button>
      </Flex>

      <Card>
        <Flex gap={18} wrap="wrap">
          <Statistic title="阅读量" value={totals.read_count} prefix={<LineChartOutlined />} />
          <Statistic title="点赞量" value={totals.like_count} />
          <Statistic title="收藏量" value={totals.favorite_count} />
          <Statistic title="转发量" value={totals.share_count} />
          <Statistic
            title="评论量"
            value={totals.comment_count}
            prefix={<CommentOutlined />}
          />
        </Flex>
      </Card>

      <Card>
        <Form form={filterForm} layout="inline" style={{ marginBottom: 16 }}>
          <Form.Item label="账号" name="account_id">
            <Select allowClear placeholder="全部账号" options={accountOptions} style={{ width: 260 }} />
          </Form.Item>
          <Form.Item label="发布状态" name="publish_status">
            <Select allowClear placeholder="全部状态" options={publishStatusOptions} style={{ width: 160 }} />
          </Form.Item>
          <Form.Item label="计划日期" name="date_range">
            <DatePicker.RangePicker />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" onClick={() => void loadData(buildFilters(), { page: 1, pageSize })}>筛选</Button>
              <Button onClick={() => {
                filterForm.resetFields()
                void loadData(undefined, { page: 1, pageSize })
              }}>重置</Button>
            </Space>
          </Form.Item>
        </Form>

        <Table
          rowKey={(record) => record.article.id}
          loading={loading}
          columns={columns}
          dataSource={items}
          pagination={false}
          scroll={{ x: 1410 }}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无文章" /> }}
        />
        {total > 0 && (
          <Pagination
            current={page}
            pageSize={pageSize}
            total={total}
            showSizeChanger
            pageSizeOptions={[10, 20, 50]}
            style={{ marginTop: 16, textAlign: 'right' }}
            onChange={(nextPage, nextPageSize) => void loadData(buildFilters(), { page: nextPage, pageSize: nextPageSize })}
          />
        )}
      </Card>

      <Modal
        title={selectedSummary ? `统计数据：${selectedSummary.article.title}` : '统计数据'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        width={920}
        destroyOnClose
      >
        <Form
          form={statForm}
          layout="inline"
          onFinish={(values) => void handleCreateStat(values)}
          style={{ marginBottom: 18 }}
        >
          <Form.Item label="阅读量" name="read_count" rules={[{ required: true, message: '请输入阅读量' }]}>
            <InputNumber min={0} precision={0} />
          </Form.Item>
          <Form.Item label="点赞量" name="like_count" rules={[{ required: true, message: '请输入点赞量' }]}>
            <InputNumber min={0} precision={0} />
          </Form.Item>
          <Form.Item label="收藏量" name="favorite_count" rules={[{ required: true, message: '请输入收藏量' }]}>
            <InputNumber min={0} precision={0} />
          </Form.Item>
          <Form.Item label="转发量" name="share_count" rules={[{ required: true, message: '请输入转发量' }]}>
            <InputNumber min={0} precision={0} />
          </Form.Item>
          <Form.Item
            label="评论量"
            name="comment_count"
            rules={[{ required: true, message: '请输入评论量' }]}
          >
            <InputNumber min={0} precision={0} />
          </Form.Item>
          <Form.Item label="统计时间" name="recorded_at" rules={[{ required: true, message: '请选择统计时间' }]}>
            <DatePicker showTime />
          </Form.Item>
          <Form.Item>
            <Button type="primary" icon={<PlusOutlined />} htmlType="submit" loading={saving}>
              添加
            </Button>
          </Form.Item>
        </Form>

        <Table
          rowKey="id"
          size="small"
          loading={historyLoading}
          columns={historyColumns}
          dataSource={history}
          pagination={{ pageSize: 8, hideOnSinglePage: true }}
          scroll={{ x: 840 }}
        />
      </Modal>
    </Flex>
  )
}
