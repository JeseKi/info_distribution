import { Button, Descriptions, Dropdown, Empty, Flex, Popconfirm, Popover, Progress, Space, Tabs, Tag, Typography } from 'antd'
import type { MenuProps } from 'antd'
import {
  CopyOutlined,
  DeleteOutlined,
  DownOutlined,
  DownloadOutlined,
  EditOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import type { ArticleDistributionArticle, ArticlePublishStatus } from '../../../lib/types'
import MarkdownArticleViewer from '../../../components/article/MarkdownArticleViewer'
import { downloadMarkdownAsDocx } from '../../../lib/articleDistributionExport'
import { publicationTypeText } from './constants'
import { inactiveAccountTag, publishStatusTag } from './statusTags'
import type { ImagePackageDownloadMode } from './articleOperations'
import type { ImagePackageProgressState } from './types'

export function ArticlePreviewPanel({
  copyMenuOpen,
  downloadingImages,
  imagePackageProgress,
  isAdmin,
  selectedArticle,
  onCopyAction,
  onCopyMenuOpenChange,
  onDeleteArticle,
  onDownloadImagePackage,
  onEditArticle,
  onOpenPublishModal,
  onStatusChange,
}: {
  copyMenuOpen: boolean
  downloadingImages: boolean
  imagePackageProgress: ImagePackageProgressState | null
  isAdmin: boolean
  selectedArticle: ArticleDistributionArticle | null
  onCopyAction: (type: 'markdown' | 'plain' | 'html' | 'wechat') => void
  onCopyMenuOpenChange: (open: boolean) => void
  onDeleteArticle: (article: ArticleDistributionArticle) => void
  onDownloadImagePackage: (mode: ImagePackageDownloadMode) => void
  onEditArticle: (article: ArticleDistributionArticle) => void
  onOpenPublishModal: (article: ArticleDistributionArticle) => void
  onStatusChange: (article: ArticleDistributionArticle, publishStatus: ArticlePublishStatus) => void
}) {
  return (
    <main className="article-preview-panel">
      {selectedArticle ? (
        <>
          <PreviewHeader
            copyMenuOpen={copyMenuOpen}
            downloadingImages={downloadingImages}
            imagePackageProgress={imagePackageProgress}
            isAdmin={isAdmin}
            selectedArticle={selectedArticle}
            onCopyAction={onCopyAction}
            onCopyMenuOpenChange={onCopyMenuOpenChange}
            onDeleteArticle={onDeleteArticle}
            onDownloadImagePackage={onDownloadImagePackage}
            onEditArticle={onEditArticle}
            onOpenPublishModal={onOpenPublishModal}
            onStatusChange={onStatusChange}
          />
          <div className="article-preview-body">
            <Tabs
              defaultActiveKey="preview"
              items={[
                {
                  key: 'preview',
                  label: '预览',
                  children: <MarkdownArticleViewer markdown={selectedArticle.markdown_content} />,
                },
                {
                  key: 'source',
                  label: '源码',
                  children: <pre className="article-source">{selectedArticle.markdown_content}</pre>,
                },
              ]}
            />
          </div>
        </>
      ) : (
        <Flex align="center" justify="center" style={{ minHeight: 560 }}>
          <Empty description="选择一篇文章开始阅读" />
        </Flex>
      )}
    </main>
  )
}

function PreviewHeader({
  copyMenuOpen,
  downloadingImages,
  imagePackageProgress,
  isAdmin,
  selectedArticle,
  onCopyAction,
  onCopyMenuOpenChange,
  onDeleteArticle,
  onDownloadImagePackage,
  onEditArticle,
  onOpenPublishModal,
  onStatusChange,
}: {
  copyMenuOpen: boolean
  downloadingImages: boolean
  imagePackageProgress: ImagePackageProgressState | null
  isAdmin: boolean
  selectedArticle: ArticleDistributionArticle
  onCopyAction: (type: 'markdown' | 'plain' | 'html' | 'wechat') => void
  onCopyMenuOpenChange: (open: boolean) => void
  onDeleteArticle: (article: ArticleDistributionArticle) => void
  onDownloadImagePackage: (mode: ImagePackageDownloadMode) => void
  onEditArticle: (article: ArticleDistributionArticle) => void
  onOpenPublishModal: (article: ArticleDistributionArticle) => void
  onStatusChange: (article: ArticleDistributionArticle, publishStatus: ArticlePublishStatus) => void
}) {
  return (
    <div className="article-preview-header">
      <Flex justify="space-between" align="start" gap={16} wrap="wrap">
        <div style={{ minWidth: 0 }}>
          <Typography.Title level={2} style={{ marginTop: 0, marginBottom: 8 }}>
            {selectedArticle.title}
          </Typography.Title>
          <Space wrap>
            <Tag icon={<FileTextOutlined />}>{selectedArticle.scheduled_date}</Tag>
            {publishStatusTag(selectedArticle.publish_status)}
            <Tag>{selectedArticle.account?.platform ?? '平台'} / {selectedArticle.account?.account_name ?? selectedArticle.account_id}</Tag>
            {inactiveAccountTag(selectedArticle.account?.is_active)}
          </Space>
        </div>
        <StatusButtons
          selectedArticle={selectedArticle}
          onOpenPublishModal={onOpenPublishModal}
          onStatusChange={onStatusChange}
        />
      </Flex>
      <Descriptions size="small" column={3} style={{ marginTop: 16 }}>
        <Descriptions.Item label="发布类型">
          {selectedArticle.account ? publicationTypeText[selectedArticle.account.publication_type] : '-'}
        </Descriptions.Item>
        <Descriptions.Item label="来源">{selectedArticle.source}</Descriptions.Item>
        <Descriptions.Item label="文章 ID">{selectedArticle.id}</Descriptions.Item>
        <Descriptions.Item label="发布地址">
          {selectedArticle.published_url ? (
            <Typography.Link href={selectedArticle.published_url} target="_blank" rel="noreferrer">
              打开链接
            </Typography.Link>
          ) : '-'}
        </Descriptions.Item>
      </Descriptions>
      <PreviewActions
        copyMenuOpen={copyMenuOpen}
        downloadingImages={downloadingImages}
        isAdmin={isAdmin}
        selectedArticle={selectedArticle}
        onCopyAction={onCopyAction}
        onCopyMenuOpenChange={onCopyMenuOpenChange}
        onDeleteArticle={onDeleteArticle}
        onDownloadImagePackage={onDownloadImagePackage}
        onEditArticle={onEditArticle}
      />
      {imagePackageProgress && (
        <ImagePackageProgress progress={imagePackageProgress} downloadingImages={downloadingImages} />
      )}
    </div>
  )
}

function StatusButtons({
  selectedArticle,
  onOpenPublishModal,
  onStatusChange,
}: {
  selectedArticle: ArticleDistributionArticle
  onOpenPublishModal: (article: ArticleDistributionArticle) => void
  onStatusChange: (article: ArticleDistributionArticle, publishStatus: ArticlePublishStatus) => void
}) {
  return (
    <Space wrap>
      <Button
        type={selectedArticle.publish_status === 'unpublished' ? 'primary' : 'default'}
        onClick={() => onStatusChange(selectedArticle, 'unpublished')}
      >
        未发布
      </Button>
      <Button
        type={selectedArticle.publish_status === 'published' ? 'primary' : 'default'}
        onClick={() => onOpenPublishModal(selectedArticle)}
      >
        已发布
      </Button>
      <Button
        danger
        type={selectedArticle.publish_status === 'invalid' ? 'primary' : 'default'}
        onClick={() => onStatusChange(selectedArticle, 'invalid')}
      >
        文档失效
      </Button>
    </Space>
  )
}

function PreviewActions({
  copyMenuOpen,
  downloadingImages,
  isAdmin,
  selectedArticle,
  onCopyAction,
  onCopyMenuOpenChange,
  onDeleteArticle,
  onDownloadImagePackage,
  onEditArticle,
}: {
  copyMenuOpen: boolean
  downloadingImages: boolean
  isAdmin: boolean
  selectedArticle: ArticleDistributionArticle
  onCopyAction: (type: 'markdown' | 'plain' | 'html' | 'wechat') => void
  onCopyMenuOpenChange: (open: boolean) => void
  onDeleteArticle: (article: ArticleDistributionArticle) => void
  onDownloadImagePackage: (mode: ImagePackageDownloadMode) => void
  onEditArticle: (article: ArticleDistributionArticle) => void
}) {
  const imagePackageMenu: MenuProps = {
    items: [
      { key: 'zip', label: '下载为压缩包' },
      { key: 'images', label: '下载为多张图片' },
    ],
    onClick: ({ key }) => onDownloadImagePackage(key as ImagePackageDownloadMode),
  }

  return (
    <Space wrap style={{ marginTop: 16 }}>
      <Popover
        trigger="click"
        open={copyMenuOpen}
        onOpenChange={onCopyMenuOpenChange}
        content={(
          <Space direction="vertical">
            <Button block icon={<CopyOutlined />} onClick={() => onCopyAction('markdown')}>复制源码</Button>
            <Button block icon={<CopyOutlined />} onClick={() => onCopyAction('plain')}>复制纯文本</Button>
            <Button block icon={<CopyOutlined />} onClick={() => onCopyAction('html')}>复制 HTML</Button>
            <Button block icon={<CopyOutlined />} onClick={() => onCopyAction('wechat')}>复制为公众号</Button>
          </Space>
        )}
      >
        <Button icon={<CopyOutlined />}>复制</Button>
      </Popover>
      <Dropdown menu={imagePackageMenu} trigger={['click']} disabled={downloadingImages}>
        <Button icon={<DownloadOutlined />} loading={downloadingImages}>
          图片包 <DownOutlined />
        </Button>
      </Dropdown>
      <Button
        icon={<DownloadOutlined />}
        onClick={() => void downloadMarkdownAsDocx(selectedArticle.markdown_content, selectedArticle.title)}
      >
        DOCX
      </Button>
      {isAdmin && (
        <>
          <Button icon={<EditOutlined />} onClick={() => onEditArticle(selectedArticle)}>
            编辑文章
          </Button>
          <Popconfirm title="删除这篇文章？" onConfirm={() => onDeleteArticle(selectedArticle)}>
            <Button danger icon={<DeleteOutlined />}>
              删除文章
            </Button>
          </Popconfirm>
        </>
      )}
    </Space>
  )
}

function ImagePackageProgress({
  downloadingImages,
  progress,
}: {
  downloadingImages: boolean
  progress: ImagePackageProgressState
}) {
  return (
    <div style={{ maxWidth: 420, marginTop: 12 }}>
      <Flex justify="space-between" gap={12}>
        <Typography.Text type="secondary">{progress.title}</Typography.Text>
        <Typography.Text type="secondary">{progress.percent}%</Typography.Text>
      </Flex>
      <Progress
        percent={progress.percent}
        size="small"
        status={downloadingImages ? 'active' : 'success'}
        showInfo={false}
      />
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        {progress.detail}
      </Typography.Text>
    </div>
  )
}
