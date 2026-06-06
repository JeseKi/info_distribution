import type {
  ArticleDistributionArticleStatusCounts,
  ArticlePublicationType,
} from '../../../lib/types'

export const defaultArticlePageSize = 10

export const defaultArticleStatusCounts: ArticleDistributionArticleStatusCounts = {
  unpublished: 0,
  published: 0,
  invalid: 0,
}

export const publicationTypeOptions = [
  { label: '视频', value: 'video' },
  { label: '文章', value: 'article' },
  { label: '图文', value: 'image_text' },
]

export const publishStatusOptions = [
  { label: '未发布', value: 'unpublished' },
  { label: '已发布', value: 'published' },
  { label: '文档失效', value: 'invalid' },
]

export const publicationTypeText: Record<ArticlePublicationType, string> = {
  video: '视频',
  article: '文章',
  image_text: '图文',
}
