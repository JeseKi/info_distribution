import ReactMarkdown from 'react-markdown'
import rehypeRaw from 'rehype-raw'
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize'
import remarkGfm from 'remark-gfm'

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
                img: ({ src, alt, title }) => (
                  <figure {...dataToolProps}>
                    <img src={src} alt={alt ?? ''} title={title ?? undefined} />
                    {alt ? <figcaption>{alt}</figcaption> : null}
                  </figure>
                ),
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
