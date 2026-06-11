import { Descriptions, Flex, Modal, Spin, Tabs, Typography } from 'antd'
import type {
  ArticleDistributionOverviewArticle,
  ArticleDistributionOverviewArticleDetail,
} from '../../../lib/types'
import MarkdownArticleViewer from '../../../components/article/MarkdownArticleViewer'
import { publicationTypeText } from './constants'
import { publishStatusTag, renderTrafficValue } from './tableUtils'

export function ArticleDetailModal({
  article,
  detail,
  loading,
  onClose,
}: {
  article: ArticleDistributionOverviewArticle | null
  detail: ArticleDistributionOverviewArticleDetail | null
  loading: boolean
  onClose: () => void
}) {
  if (!article) return null
  const displayArticle = detail ?? article

  return (
    <Modal
      open
      width="min(96vw, 1180px)"
      title={displayArticle.title}
      footer={null}
      onCancel={onClose}
      destroyOnClose
    >
      <Flex vertical gap={14}>
        <Descriptions size="small" column={{ xs: 1, sm: 2, md: 4 }}>
          <Descriptions.Item label="文章 ID">{displayArticle.id}</Descriptions.Item>
          <Descriptions.Item label="用户">{displayArticle.name || displayArticle.username}</Descriptions.Item>
          <Descriptions.Item label="账号">{displayArticle.platform} / {displayArticle.account_name}</Descriptions.Item>
          <Descriptions.Item label="发布类型">{publicationTypeText[displayArticle.publication_type]}</Descriptions.Item>
          <Descriptions.Item label="计划日期">{displayArticle.scheduled_date}</Descriptions.Item>
          <Descriptions.Item label="文章角色">{displayArticle.article_role ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="角度">{displayArticle.angle_label ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="受众">{displayArticle.audience_label ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="状态">{publishStatusTag(displayArticle.publish_status)}</Descriptions.Item>
          <Descriptions.Item label="未填流量">{displayArticle.missing_traffic ? '是' : '否'}</Descriptions.Item>
          <Descriptions.Item label="阅读量">{renderTrafficValue(displayArticle.latest_traffic_stat?.read_count)}</Descriptions.Item>
          <Descriptions.Item label="点赞量">{renderTrafficValue(displayArticle.latest_traffic_stat?.like_count)}</Descriptions.Item>
          <Descriptions.Item label="收藏量">
            {renderTrafficValue(displayArticle.latest_traffic_stat?.favorite_count)}
          </Descriptions.Item>
          <Descriptions.Item label="转发量">
            {renderTrafficValue(displayArticle.latest_traffic_stat?.share_count)}
          </Descriptions.Item>
          <Descriptions.Item label="评论量">
            {renderTrafficValue(displayArticle.latest_traffic_stat?.comment_count)}
          </Descriptions.Item>
          <Descriptions.Item label="发布链接">
            {displayArticle.published_url ? (
              <Typography.Link href={displayArticle.published_url} target="_blank" rel="noreferrer">
                检查
              </Typography.Link>
            ) : '-'}
          </Descriptions.Item>
        </Descriptions>
        <div>
          <Typography.Text strong>痛点解决方案</Typography.Text>
          <Typography.Paragraph style={{ margin: '6px 0 0' }}>
            {loading ? '加载中...' : detail?.summary || '-'}
          </Typography.Paragraph>
        </div>
        <Tabs
          items={[
            {
              key: 'preview',
              label: '正文预览',
              children: (
                <div style={{ maxHeight: '60vh', overflow: 'auto', paddingRight: 8 }}>
                  {detail ? <MarkdownArticleViewer markdown={detail.markdown_content} /> : <LoadingDetail />}
                </div>
              ),
            },
            {
              key: 'source',
              label: '正文源码',
              children: detail
                ? <PreBlock content={detail.markdown_content} maxHeight="60vh" />
                : <LoadingDetail />,
            },
            {
              key: 'metadata',
              label: '元数据',
              children: detail
                ? <PreBlock content={JSON.stringify(detail.metadata ?? {}, null, 2)} maxHeight="60vh" />
                : <LoadingDetail />,
            },
          ]}
        />
      </Flex>
    </Modal>
  )
}

function LoadingDetail() {
  return (
    <Flex align="center" justify="center" style={{ minHeight: 180 }}>
      <Spin />
    </Flex>
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
