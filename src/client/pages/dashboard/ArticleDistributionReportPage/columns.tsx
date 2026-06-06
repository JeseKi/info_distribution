import { Flex, Popover, Space, Tag, Typography } from 'antd'
import type { TableColumnsType } from 'antd'
import type {
  ArticleDistributionOverviewArticle,
  ArticleDistributionOverviewTopic,
  ArticleDistributionOverviewUser,
  ArticleDistributionPlatformSummary,
} from '../../../lib/types'
import { publicationTypeText } from './constants'
import { renderMaterials, trafficColumn } from './tableUtils'

export function buildUserColumns(): TableColumnsType<ArticleDistributionOverviewUser> {
  return [
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
}

export function buildTopicColumns(): TableColumnsType<ArticleDistributionOverviewTopic> {
  return [
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
}

export function buildPlatformColumns(
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
