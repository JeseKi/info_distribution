import { DownloadOutlined } from '@ant-design/icons'
import { App, Button, Modal, Space, Tooltip } from 'antd'
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeRaw from 'rehype-raw'
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize'
import remarkGfm from 'remark-gfm'
import api from '../../lib/api'

const sanitizeSchema = {
  ...defaultSchema,
  tagNames: [
    ...(defaultSchema.tagNames ?? []),
    'details',
    'summary',
    'kbd',
    'video',
    'audio',
    'source',
    'iframe',
    'figure',
    'figcaption',
    'section',
    'span',
    'mark',
  ],
  attributes: {
    ...defaultSchema.attributes,
    '*': [
      ...(defaultSchema.attributes?.['*'] ?? []),
      'className',
      'class',
      'data-tool',
    ],
    p: [...(defaultSchema.attributes?.p ?? []), 'align'],
    div: [...(defaultSchema.attributes?.div ?? []), 'align'],
    img: [
      ...(defaultSchema.attributes?.img ?? []),
      'src',
      'alt',
      'title',
      'width',
      'height',
      'align',
      'loading',
    ],
    video: [
      ...(defaultSchema.attributes?.video ?? []),
      'src',
      'controls',
      'autoplay',
      'muted',
      'loop',
      'playsinline',
      'poster',
      'width',
      'height',
      'preload',
    ],
    audio: [
      ...(defaultSchema.attributes?.audio ?? []),
      'src',
      'controls',
      'autoplay',
      'muted',
      'loop',
      'preload',
    ],
    source: [
      ...(defaultSchema.attributes?.source ?? []),
      'src',
      'type',
      'media',
    ],
    iframe: [
      ...(defaultSchema.attributes?.iframe ?? []),
      'src',
      'width',
      'height',
      'title',
      'allow',
      'allowfullscreen',
      'frameborder',
      'referrerpolicy',
    ],
  },
}

const dataToolProps = { 'data-tool': 'WeMD编辑器' }

function sanitizeFilename(filename: string): string {
  const normalized = filename.trim() || 'image'
  return normalized.replace(/[\\/:*?"<>|]+/g, '_').slice(0, 80)
}

function imageFilename(src: string | undefined, alt: string | undefined): string {
  const fallback = sanitizeFilename(alt || 'article-image')
  if (!src || src.startsWith('data:')) return `${fallback}.png`

  try {
    const parsed = new URL(src, window.location.href)
    const pathname = parsed.pathname.split('/').filter(Boolean).at(-1)
    return sanitizeFilename(pathname || fallback)
  } catch {
    return fallback
  }
}

async function fetchImageBlob(src: string): Promise<Blob> {
  if (src.startsWith('data:')) {
    return fetch(src).then((response) => response.blob())
  }

  try {
    const directResponse = await fetch(src, { credentials: 'include' })
    if (directResponse.ok) {
      return directResponse.blob()
    }
  } catch {
    // Remote images often block browser downloads via CORS; use the image proxy below.
  }

  if (!/^https?:\/\//i.test(src)) {
    throw new Error('图片下载失败')
  }

  const response = await api.get<ArrayBuffer>('/article-distribution/image-proxy', {
    params: { url: src },
    responseType: 'arraybuffer',
  })
  return new Blob([response.data], {
    type: String(response.headers['content-type'] ?? 'application/octet-stream'),
  })
}

async function downloadImage(src: string, filename: string): Promise<void> {
  const blob = await fetchImageBlob(src)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function Heading({
  level,
  children,
}: {
  level: 1 | 2 | 3 | 4 | 5 | 6
  children: React.ReactNode
}) {
  const Tag = `h${level}` as const
  return (
    <Tag {...dataToolProps}>
      <span className="prefix" />
      <span className="content">{children}</span>
      <span className="suffix" />
    </Tag>
  )
}

function ArticleImage({
  src,
  alt,
  title,
}: {
  src?: string
  alt?: string
  title?: string | null
}) {
  const { message } = App.useApp()
  const [open, setOpen] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const filename = imageFilename(src, alt)

  const handleDownload = async () => {
    if (!src) return
    setDownloading(true)
    try {
      await downloadImage(src, filename)
      message.success('图片已下载')
    } catch {
      message.error('图片下载失败')
    } finally {
      setDownloading(false)
    }
  }

  if (!src) {
    return null
  }

  return (
    <figure {...dataToolProps}>
      <button
        type="button"
        className="article-image-trigger"
        onClick={() => setOpen(true)}
        aria-label={alt ? `打开图片：${alt}` : '打开图片'}
      >
        <img src={src} alt={alt ?? ''} title={title ?? undefined} />
      </button>
      {alt ? <figcaption>{alt}</figcaption> : null}
      <Modal
        centered
        open={open}
        footer={null}
        width="min(96vw, 1040px)"
        onCancel={() => setOpen(false)}
        className="article-image-lightbox"
        title={
          <Space size={8}>
            <span>{alt || title || '图片预览'}</span>
            <Tooltip title="下载图片">
              <Button
                aria-label="下载图片"
                icon={<DownloadOutlined />}
                loading={downloading}
                onClick={() => void handleDownload()}
              />
            </Tooltip>
          </Space>
        }
      >
        <img className="article-image-lightbox__image" src={src} alt={alt ?? ''} />
      </Modal>
    </figure>
  )
}

export default function MarkdownArticleViewer({ markdown }: { markdown: string }) {
  return (
    <div className="wechat-preview">
      <div className="wechat-preview-container">
        <div className="wechat-preview-content">
          <section id="wemd">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw, [rehypeSanitize, sanitizeSchema]]}
              components={{
                p: ({ children, ...props }) => (
                  <p {...props} {...dataToolProps}>
                    {children}
                  </p>
                ),
                h1: ({ children }) => <Heading level={1}>{children}</Heading>,
                h2: ({ children }) => <Heading level={2}>{children}</Heading>,
                h3: ({ children }) => <Heading level={3}>{children}</Heading>,
                h4: ({ children }) => <Heading level={4}>{children}</Heading>,
                h5: ({ children }) => <Heading level={5}>{children}</Heading>,
                h6: ({ children }) => <Heading level={6}>{children}</Heading>,
                ul: ({ children }) => <ul {...dataToolProps}>{children}</ul>,
                ol: ({ children }) => <ol {...dataToolProps}>{children}</ol>,
                li: ({ children }) => (
                  <li {...dataToolProps}>
                    <section>{children}</section>
                  </li>
                ),
                blockquote: ({ children }) => (
                  <blockquote {...dataToolProps} className="multiquote-1">
                    {children}
                  </blockquote>
                ),
                a: ({ children, ...props }) => (
                  <a {...props} target="_blank" rel="noreferrer">
                    {children}
                  </a>
                ),
                img: ({ src, alt, title }) => <ArticleImage src={src} alt={alt ?? undefined} title={title} />,
                pre: ({ children }) => (
                  <pre className="custom">
                    <div className="code-toolbar">
                      <span className="code-toolbar-dot code-toolbar-dot-close" />
                      <span className="code-toolbar-dot code-toolbar-dot-minimize" />
                      <span className="code-toolbar-dot code-toolbar-dot-expand" />
                    </div>
                    {children}
                  </pre>
                ),
                table: ({ children }) => (
                  <div className="table-container">
                    <table>{children}</table>
                  </div>
                ),
                video: ({ ...props }) => <video {...props} controls={props.controls ?? true} />,
                audio: ({ ...props }) => <audio {...props} controls={props.controls ?? true} />,
                source: ({ ...props }) => <source {...props} />,
                iframe: ({ ...props }) => <iframe {...props} />,
              }}
            >
              {markdown}
            </ReactMarkdown>
          </section>
        </div>
      </div>
    </div>
  )
}
