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
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { TableColumnsType } from 'antd'
import { ReloadOutlined, SearchOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import * as articleApi from '../../lib/articleDistribution'
import type {
  ArticleDistributionPendingArticle,
  ArticleDistributionPendingReportFilters,
  ArticleDistributionPendingUser,
  ArticlePublicationType,
} from '../../lib/types'
import { resolveApiErrorMessage } from '../../lib/error'

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

interface FilterValues {
  keyword?: string
  platform?: string
  publication_type?: ArticlePublicationType
  date_range?: [dayjs.Dayjs, dayjs.Dayjs]
}

export default function ArticleDistributionReportPage() {
  const { message } = App.useApp()
  const [form] = Form.useForm<FilterValues>()
  const [loading, setLoading] = useState(false)
  const [rows, setRows] = useState<ArticleDistributionPendingUser[]>([])

  const loadReport = useCallback(async (filters?: ArticleDistributionPendingReportFilters) => {
    setLoading(true)
    try {
      setRows(await articleApi.listUnpublishedArticleReport(filters))
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '分发进度加载失败'))
    } finally {
      setLoading(false)
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
        ...row.articles.map((article) =>
          [
            article.title,
            article.account_name,
            article.platform,
            article.scheduled_date,
          ].join(' '),
        ),
      ].join(' ').toLowerCase().includes(normalized),
    )
  }, [keyword, rows])

  const remainingTotal = filteredRows.reduce(
    (total, row) => total + row.remaining_count,
    0,
  )

  const userColumns: TableColumnsType<ArticleDistributionPendingUser> = [
    {
      title: '用户',
      key: 'user',
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
      sorter: (a, b) => a.remaining_count - b.remaining_count,
      render: (value: number) => <Tag color={value > 0 ? 'volcano' : 'default'}>{value} 篇</Tag>,
    },
  ]

  const articleColumns: TableColumnsType<ArticleDistributionPendingArticle> = [
    {
      title: '文章',
      dataIndex: 'title',
      key: 'title',
      render: (value: string) => <Typography.Text strong>{value}</Typography.Text>,
    },
    {
      title: '计划日期',
      dataIndex: 'scheduled_date',
      key: 'scheduled_date',
      sorter: (a, b) => a.scheduled_date.localeCompare(b.scheduled_date),
    },
    {
      title: '目标平台',
      dataIndex: 'platform',
      key: 'platform',
      render: (value: string) => <Tag>{value}</Tag>,
    },
    {
      title: '目标账号',
      dataIndex: 'account_name',
      key: 'account_name',
    },
    {
      title: '类型',
      dataIndex: 'publication_type',
      key: 'publication_type',
      render: (value: ArticlePublicationType) => publicationTypeText[value],
    },
  ]

  const renderArticleDetail = (article: ArticleDistributionPendingArticle) => (
    <Flex vertical gap={12}>
      <Descriptions size="small" column={{ xs: 1, sm: 2, md: 4 }}>
        <Descriptions.Item label="目标平台">{article.platform}</Descriptions.Item>
        <Descriptions.Item label="目标账号">{article.account_name}</Descriptions.Item>
        <Descriptions.Item label="发布类型">
          {publicationTypeText[article.publication_type]}
        </Descriptions.Item>
        <Descriptions.Item label="计划日期">{article.scheduled_date}</Descriptions.Item>
      </Descriptions>
      <Typography.Text strong>{article.title}</Typography.Text>
      <pre
        style={{
          margin: 0,
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

  const expandedArticleTable = (record: ArticleDistributionPendingUser) => (
    <Table
      rowKey="id"
      columns={articleColumns}
      dataSource={record.articles}
      pagination={false}
      size="small"
      expandable={{
        expandedRowRender: renderArticleDetail,
      }}
    />
  )

  return (
    <Flex vertical gap={18}>
      <Flex align="center" justify="space-between" gap={16} wrap="wrap">
        <div>
          <Typography.Title level={2} style={{ margin: 0 }}>
            分发进度后台
          </Typography.Title>
          <Typography.Text type="secondary">
            查看所有用户的未发布文章余量和明细。
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
          <Statistic title="涉及用户" value={filteredRows.length} />
          <Statistic title="未发布文章" value={remainingTotal} />
        </Flex>
        <Form form={form} layout="vertical" style={{ marginTop: 18 }}>
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
          defaultExpandAllRows: true,
        }}
        locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无未发布文章" /> }}
        pagination={{ pageSize: 10 }}
        scroll={{ x: 'max-content' }}
      />
    </Flex>
  )
}
