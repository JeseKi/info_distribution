import type {
  ArticleDistributionOverview,
  ArticleDistributionOverviewSummary,
  ArticleDistributionOverviewView,
  ArticlePublicationType,
} from '../../../lib/types'

export const metadataScope = 'article_distribution:metadata_dashboard:read'

export const publicationTypeOptions = [
  { label: '视频', value: 'video' },
  { label: '文章', value: 'article' },
  { label: '图文', value: 'image_text' },
]

export const accountStatusOptions = [
  { label: '启用', value: 'active' },
  { label: '停用', value: 'inactive' },
  { label: '全部', value: 'all' },
]

export const publishStatusOptions = [
  { label: '未发布', value: 'unpublished' },
  { label: '已发布', value: 'published' },
  { label: '文档失效', value: 'invalid' },
]

export const viewOptions: { label: string; value: ArticleDistributionOverviewView }[] = [
  { label: '用户汇总', value: 'users' },
  { label: '文章明细', value: 'articles' },
  { label: '选题汇总', value: 'topics' },
]

export const publicationTypeText: Record<ArticlePublicationType, string> = {
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
  comment_count: 0,
}

export const defaultOverview: ArticleDistributionOverview = {
  view: 'users',
  summary: defaultSummary,
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
}

export const defaultVisibleColumns: Record<ArticleDistributionOverviewView, string[]> = {
  users: [
    'user',
    'wechat_nickname',
    'wechat_id',
    'remaining_count',
    'published_count',
    'invalid_count',
    'missing_count',
    'read_count',
    'like_count',
    'favorite_count',
    'share_count',
    'comment_count',
  ],
  articles: [
    'article',
    'user',
    'wechat_nickname',
    'wechat_id',
    'account',
    'publish_status',
    'scheduled_date',
    'missing_traffic',
    'read_count',
    'like_count',
    'favorite_count',
    'share_count',
    'comment_count',
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
    'comment_count',
  ],
}

export const defaultVisibleSummaryMetrics = [
  'total_users',
  'total_articles',
  'published_articles',
  'unpublished_articles',
  'missing_articles',
  'topic_count',
  'material_count',
  'read_count',
  'like_count',
  'favorite_count',
  'share_count',
  'comment_count',
]

export const summaryMetricLabels: Record<string, string> = {
  total_users: '用户数',
  total_articles: '文章数',
  published_articles: '已发布',
  unpublished_articles: '未发布',
  invalid_articles: '文档失效',
  inactive_account_articles: '停用账号文章',
  missing_articles: '未填流量',
  topic_count: '选题数',
  material_count: '素材数',
  read_count: '阅读量',
  like_count: '点赞量',
  favorite_count: '收藏量',
  share_count: '转发量',
  comment_count: '评论量',
}

export const columnLabels: Record<ArticleDistributionOverviewView, Record<string, string>> = {
  users: {
    user: '用户',
    wechat_nickname: '微信昵称',
    wechat_id: '微信号',
    remaining_count: '剩余未发布',
    published_count: '已发布',
    invalid_count: '失效',
    missing_count: '未填流量',
    read_count: '阅读量',
    like_count: '点赞量',
    favorite_count: '收藏量',
    share_count: '转发量',
    comment_count: '评论量',
  },
  articles: {
    article: '文章',
    user: '用户',
    wechat_nickname: '微信昵称',
    wechat_id: '微信号',
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
    comment_count: '评论量',
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
    comment_count: '评论量',
  },
}
