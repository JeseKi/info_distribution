import { Button, Space, Tag, Typography } from 'antd'
import type { TableColumnsType } from 'antd'
import dayjs from 'dayjs'
import type {
  ArticleDistributionOverviewArticle,
  ArticlePublishStatus,
} from '../../../lib/types'
import { publicationTypeText } from './constants'
import { publishStatusTag, renderTrafficValue } from './tableUtils'

export function buildArticleColumns({
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
