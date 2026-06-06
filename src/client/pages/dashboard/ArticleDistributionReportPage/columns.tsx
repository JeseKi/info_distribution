import { Space, Tag, Typography } from 'antd'
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  LinkOutlined,
  LikeOutlined,
  ReadOutlined,
  ShareAltOutlined,
  StarOutlined,
  TagsOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import type { TableColumnsType } from 'antd'
import type {
  ArticleDistributionOverviewTopic,
  ArticleDistributionOverviewUser,
  ArticleDistributionPlatformSummary,
} from '../../../lib/types'
import { publicationTypeText } from './constants'
import { columnTitle, renderMaterials, trafficColumn } from './tableUtils'

export function buildUserColumns(): TableColumnsType<ArticleDistributionOverviewUser> {
  return [
    {
      title: columnTitle('用户', <TeamOutlined />),
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
      title: columnTitle('剩余未发布', <ExclamationCircleOutlined />),
      dataIndex: 'remaining_count',
      key: 'remaining_count',
      width: 140,
      sorter: (a, b) => a.remaining_count - b.remaining_count,
      render: (value: number) => <Tag color={value > 0 ? 'volcano' : 'default'}>{value} 篇</Tag>,
    },
    {
      title: columnTitle('已发布', <CheckCircleOutlined />),
      dataIndex: 'published_count',
      key: 'published_count',
      width: 120,
      sorter: (a, b) => a.published_count - b.published_count,
      render: (value: number) => <Tag color="green">{value} 篇</Tag>,
    },
    {
      title: columnTitle('失效', <FileTextOutlined />),
      dataIndex: 'invalid_count',
      key: 'invalid_count',
      width: 100,
      sorter: (a, b) => a.invalid_count - b.invalid_count,
      render: (value: number) => <Tag color={value > 0 ? 'red' : 'default'}>{value} 篇</Tag>,
    },
    {
      title: columnTitle('未填流量', <ExclamationCircleOutlined />),
      dataIndex: 'missing_count',
      key: 'missing_count',
      width: 120,
      sorter: (a, b) => a.missing_count - b.missing_count,
      render: (value: number) => <Tag color={value > 0 ? 'orange' : 'default'}>{value} 篇</Tag>,
    },
    trafficColumn('阅读量', 'read_count', <ReadOutlined />),
    trafficColumn('点赞量', 'like_count', <LikeOutlined />),
    trafficColumn('收藏量', 'favorite_count', <StarOutlined />),
    trafficColumn('转发量', 'share_count', <ShareAltOutlined />),
  ]
}

export function buildTopicColumns(): TableColumnsType<ArticleDistributionOverviewTopic> {
  return [
    {
      title: columnTitle('选题', <TagsOutlined />),
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
      title: columnTitle('文章', <FileTextOutlined />),
      dataIndex: 'article_count',
      key: 'article_count',
      width: 100,
      sorter: (a, b) => a.article_count - b.article_count,
      render: (value: number) => <Tag>{value} 篇</Tag>,
    },
    {
      title: columnTitle('素材', <FileTextOutlined />),
      key: 'materials',
      width: 300,
      render: (_, record) => renderMaterials(record.materials),
    },
    trafficColumn('阅读量', 'read_count', <ReadOutlined />),
    trafficColumn('点赞量', 'like_count', <LikeOutlined />),
    trafficColumn('收藏量', 'favorite_count', <StarOutlined />),
    trafficColumn('转发量', 'share_count', <ShareAltOutlined />),
  ]
}

export function buildPlatformColumns(): TableColumnsType<ArticleDistributionPlatformSummary> {
  return [
    {
      title: columnTitle('发布平台', <TagsOutlined />),
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
      title: columnTitle('发布数量', <CheckCircleOutlined />),
      dataIndex: 'published_count',
      key: 'published_count',
      width: 120,
      render: (value: number) => <Tag color="green">{value}</Tag>,
    },
    {
      title: columnTitle('剩余未发布', <ExclamationCircleOutlined />),
      dataIndex: 'unpublished_count',
      key: 'unpublished_count',
      width: 140,
      render: (value: number) => <Tag color={value > 0 ? 'volcano' : 'default'}>{value}</Tag>,
    },
    {
      title: columnTitle('失效数量', <FileTextOutlined />),
      dataIndex: 'invalid_count',
      key: 'invalid_count',
      width: 120,
      render: (value: number) => <Tag color={value > 0 ? 'red' : 'default'}>{value}</Tag>,
    },
    {
      title: columnTitle('最新链接', <LinkOutlined />),
      key: 'latest_published_url',
      width: 140,
      render: (_, record) => record.latest_published_url ? (
        <Typography.Link href={record.latest_published_url} target="_blank" rel="noreferrer">
          检查
        </Typography.Link>
      ) : '-',
    },
  ]
}
