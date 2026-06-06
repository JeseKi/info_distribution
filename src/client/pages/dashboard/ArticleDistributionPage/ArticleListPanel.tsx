import { Empty, Flex, Pagination, Tag, Typography } from 'antd'
import type { ArticleDistributionArticle } from '../../../lib/types'
import { inactiveAccountTag, publishStatusTag } from './statusTags'

export function ArticleListPanel({
  articles,
  articlePage,
  articlePageSize,
  articleTotal,
  selectedArticle,
  onPageChange,
  onSelectArticle,
}: {
  articles: ArticleDistributionArticle[]
  articlePage: number
  articlePageSize: number
  articleTotal: number
  selectedArticle: ArticleDistributionArticle | null
  onPageChange: (page: number, pageSize: number) => void
  onSelectArticle: (articleId: number) => void
}) {
  return (
    <section className="article-list-panel">
      <Flex align="center" justify="space-between" style={{ marginBottom: 12 }}>
        <Typography.Text strong>文章队列</Typography.Text>
        <Tag>{articleTotal} 篇</Tag>
      </Flex>
      <Flex vertical gap={8}>
        {articles.map((article) => (
          <button
            key={article.id}
            type="button"
            className={`article-list-item ${selectedArticle?.id === article.id ? 'article-list-item--active' : ''}`}
            onClick={() => onSelectArticle(article.id)}
          >
            <Flex vertical gap={6}>
              <Flex justify="space-between" gap={8} align="center">
                <Typography.Text strong ellipsis style={{ maxWidth: 240 }}>
                  {article.title}
                </Typography.Text>
                {publishStatusTag(article.publish_status)}
              </Flex>
              <Typography.Text type="secondary">
                {article.scheduled_date} · {article.account?.platform ?? '未知平台'} / {article.account?.account_name ?? article.account_id}
                {inactiveAccountTag(article.account?.is_active)}
              </Typography.Text>
            </Flex>
          </button>
        ))}
        {!articles.length && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无文章" />}
      </Flex>
      {articleTotal > 0 && (
        <Pagination
          size="small"
          current={articlePage}
          pageSize={articlePageSize}
          total={articleTotal}
          showSizeChanger
          pageSizeOptions={[10, 20, 50]}
          style={{ marginTop: 16, textAlign: 'center' }}
          onChange={onPageChange}
        />
      )}
    </section>
  )
}
