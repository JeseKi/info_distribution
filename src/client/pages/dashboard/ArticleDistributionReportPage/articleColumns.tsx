import { Button, Space, Tag, Typography } from 'antd'
import {
  BarChartOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  CommentOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  FileTextOutlined,
  IdcardOutlined,
  LikeOutlined,
  LinkOutlined,
  ProfileOutlined,
  ReadOutlined,
  ShareAltOutlined,
  StarOutlined,
  TagsOutlined,
  TeamOutlined,
  WechatOutlined,
} from '@ant-design/icons'
import type { TableColumnsType } from 'antd'
import dayjs from 'dayjs'
import type {
  ArticleDistributionOverviewArticle,
  ArticlePublishStatus,
} from '../../../lib/types'
import { publicationTypeText } from './constants'
import { columnTitle, publishStatusTag, remoteSortOrder, renderTrafficValue } from './tableUtils'
import type { ReportSortState } from './tableUtils'

export function buildArticleColumns({
  includeUser,
  includeActions,
  sortState,
  onSelectArticle,
}: {
  includeUser: boolean
  includeActions: boolean
  sortState?: ReportSortState
  onSelectArticle: (article: ArticleDistributionOverviewArticle) => void
}): TableColumnsType<ArticleDistributionOverviewArticle> {
  const columns: TableColumnsType<ArticleDistributionOverviewArticle> = [
    {
      title: columnTitle('文章', <FileTextOutlined />),
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
    columns.push(
      {
        title: columnTitle('用户', <TeamOutlined />),
        key: 'user',
        width: 240,
        render: (_, record) => (
          <Space direction="vertical" size={0}>
            <Typography.Text>{record.name || record.username}</Typography.Text>
            <Typography.Text type="secondary">{record.email}</Typography.Text>
          </Space>
        ),
      },
      {
        title: columnTitle('微信昵称', <WechatOutlined />),
        dataIndex: 'wechat_nickname',
        key: 'wechat_nickname',
        width: 140,
        render: (value: string | null) => value || '-',
      },
      {
        title: columnTitle('微信号', <IdcardOutlined />),
        dataIndex: 'wechat_id',
        key: 'wechat_id',
        width: 150,
        render: (value: string | null) => value || '-',
      },
    )
  }

  columns.push(
    {
      title: columnTitle('账号', <IdcardOutlined />),
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
      title: columnTitle('状态', <CheckCircleOutlined />),
      dataIndex: 'publish_status',
      key: 'publish_status',
      width: 110,
      render: (value: ArticlePublishStatus) => publishStatusTag(value),
    },
    {
      title: columnTitle('关键词', <TagsOutlined />),
      dataIndex: 'keyword',
      key: 'keyword',
      width: 140,
      render: (value: string) => value || '-',
    },
    {
      title: columnTitle('计划日期', <CalendarOutlined />),
      dataIndex: 'scheduled_date',
      key: 'scheduled_date',
      width: 130,
      sorter: true,
      sortOrder: remoteSortOrder('scheduled_date', sortState),
    },
    {
      title: columnTitle('未填流量', <BarChartOutlined />),
      dataIndex: 'missing_traffic',
      key: 'missing_traffic',
      width: 110,
      render: (value: boolean) => <Tag color={value ? 'orange' : 'default'}>{value ? '是' : '否'}</Tag>,
    },
    {
      title: columnTitle('选题', <TagsOutlined />),
      key: 'topic',
      width: 220,
      render: (_, record) => record.topic || record.output_id || '-',
    },
    {
      title: columnTitle('角色', <ProfileOutlined />),
      key: 'article_role',
      width: 120,
      render: (_, record) => record.article_role ?? '-',
    },
    {
      title: columnTitle('阅读量', <ReadOutlined />),
      key: 'read_count',
      width: 100,
      sorter: true,
      sortOrder: remoteSortOrder('read_count', sortState),
      render: (_, record) => renderTrafficValue(record.latest_traffic_stat?.read_count),
    },
    {
      title: columnTitle('点赞量', <LikeOutlined />),
      key: 'like_count',
      width: 100,
      sorter: true,
      sortOrder: remoteSortOrder('like_count', sortState),
      render: (_, record) => renderTrafficValue(record.latest_traffic_stat?.like_count),
    },
    {
      title: columnTitle('收藏量', <StarOutlined />),
      key: 'favorite_count',
      width: 100,
      sorter: true,
      sortOrder: remoteSortOrder('favorite_count', sortState),
      render: (_, record) => renderTrafficValue(record.latest_traffic_stat?.favorite_count),
    },
    {
      title: columnTitle('转发量', <ShareAltOutlined />),
      key: 'share_count',
      width: 100,
      sorter: true,
      sortOrder: remoteSortOrder('share_count', sortState),
      render: (_, record) => renderTrafficValue(record.latest_traffic_stat?.share_count),
    },
    {
      title: columnTitle('评论量', <CommentOutlined />),
      key: 'comment_count',
      width: 130,
      sorter: true,
      sortOrder: remoteSortOrder('comment_count', sortState),
      render: (_, record) => renderTrafficValue(
        record.latest_traffic_stat?.comment_count,
      ),
    },
    {
      title: columnTitle('统计时间', <ClockCircleOutlined />),
      key: 'traffic_recorded_at',
      width: 150,
      render: (_, record) => record.latest_traffic_stat
        ? dayjs(record.latest_traffic_stat.recorded_at).format('YYYY-MM-DD HH:mm')
        : '-',
    },
    {
      title: columnTitle('发布链接', <LinkOutlined />),
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
      title: columnTitle('操作', <EyeOutlined />),
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
