import type {
  ArticleDistributionOverviewArticle,
  ArticleDistributionOverviewItem,
  ArticleDistributionOverviewTopic,
  ArticleDistributionOverviewUser,
} from '../../../lib/types'

export function isUserItem(item: ArticleDistributionOverviewItem): item is ArticleDistributionOverviewUser {
  return item.item_type === 'user'
}

export function isArticleItem(item: ArticleDistributionOverviewItem): item is ArticleDistributionOverviewArticle {
  return item.item_type === 'article'
}

export function isTopicItem(item: ArticleDistributionOverviewItem): item is ArticleDistributionOverviewTopic {
  return item.item_type === 'topic'
}
