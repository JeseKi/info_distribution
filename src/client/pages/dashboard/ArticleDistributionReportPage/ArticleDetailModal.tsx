import { Descriptions, Flex, Modal, Tabs, Typography } from 'antd'
import type { ArticleDistributionOverviewArticle } from '../../../lib/types'
import MarkdownArticleViewer from '../../../components/article/MarkdownArticleViewer'
import { publicationTypeText } from './constants'
import { publishStatusTag, renderTrafficValue } from './tableUtils'

export function ArticleDetailModal({
  article,
  onClose,
}: {
  article: ArticleDistributionOverviewArticle | null
  onClose: () => void
}) {
  if (!article) return null

  return (
    <Modal
      open
      width="min(96vw, 1180px)"
      title={article.title}
      footer={null}
      onCancel={onClose}
      destroyOnClose
    >
      <Flex vertical gap={14}>
        <Descriptions size="small" column={{ xs: 1, sm: 2, md: 4 }}>
          <Descriptions.Item label="文章 ID">{article.id}</Descriptions.Item>
          <Descriptions.Item label="用户">{article.name || article.username}</Descriptions.Item>
          <Descriptions.Item label="账号">{article.platform} / {article.account_name}</Descriptions.Item>
          <Descriptions.Item label="发布类型">{publicationTypeText[article.publication_type]}</Descriptions.Item>
          <Descriptions.Item label="计划日期">{article.scheduled_date}</Descriptions.Item>
          <Descriptions.Item label="文章角色">{article.article_role ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="角度">{article.angle_label ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="受众">{article.audience_label ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="状态">{publishStatusTag(article.publish_status)}</Descriptions.Item>
          <Descriptions.Item label="未填流量">{article.missing_traffic ? '是' : '否'}</Descriptions.Item>
          <Descriptions.Item label="阅读量">{renderTrafficValue(article.latest_traffic_stat?.read_count)}</Descriptions.Item>
          <Descriptions.Item label="点赞量">{renderTrafficValue(article.latest_traffic_stat?.like_count)}</Descriptions.Item>
          <Descriptions.Item label="收藏量">
            {renderTrafficValue(article.latest_traffic_stat?.favorite_count)}
          </Descriptions.Item>
          <Descriptions.Item label="转发量">{renderTrafficValue(article.latest_traffic_stat?.share_count)}</Descriptions.Item>
          <Descriptions.Item label="发布链接">
            {article.published_url ? (
              <Typography.Link href={article.published_url} target="_blank" rel="noreferrer">
                检查
              </Typography.Link>
            ) : '-'}
          </Descriptions.Item>
        </Descriptions>
        <div>
          <Typography.Text strong>痛点解决方案</Typography.Text>
          <Typography.Paragraph style={{ margin: '6px 0 0' }}>
            {article.summary || '-'}
          </Typography.Paragraph>
        </div>
        <Tabs
          items={[
            {
              key: 'preview',
              label: '正文预览',
              children: (
                <div style={{ maxHeight: '60vh', overflow: 'auto', paddingRight: 8 }}>
                  <MarkdownArticleViewer markdown={article.markdown_content} />
                </div>
              ),
            },
            {
              key: 'source',
              label: '正文源码',
              children: <PreBlock content={article.markdown_content} maxHeight="60vh" />,
            },
            {
              key: 'metadata',
              label: '元数据',
              children: <PreBlock content={JSON.stringify(article.metadata ?? {}, null, 2)} maxHeight="60vh" />,
            },
          ]}
        />
      </Flex>
    </Modal>
  )
}

function PreBlock({ content, maxHeight }: { content: string; maxHeight: string }) {
  return (
    <pre
      style={{
        margin: 0,
        boxSizing: 'border-box',
        maxWidth: '100%',
        maxHeight,
        overflow: 'auto',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        padding: 12,
        borderRadius: 6,
        background: 'var(--ant-color-fill-quaternary)',
      }}
    >
      {content}
    </pre>
  )
}
