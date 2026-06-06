import type { ArticleDistributionArticle } from '../../../lib/types'
import {
  buildStyledArticleHtml,
  buildWechatHtml,
  copyHtml,
  copyText,
  downloadMarkdownImagesAsZip,
  markdownToPlainText,
} from '../../../lib/articleDistributionExport'
import { buildImagePackageProgressState } from './progress'
import type { ImagePackageProgressState } from './types'

type MessageApi = {
  error: (content: string) => void
  success: (content: string) => void
  warning: (content: string) => void
}

export async function copyArticleContent({
  article,
  message,
  type,
  onCopied,
}: {
  article: ArticleDistributionArticle
  message: MessageApi
  type: 'markdown' | 'plain' | 'html' | 'wechat'
  onCopied: () => void
}) {
  try {
    const plainText = markdownToPlainText(article.markdown_content)
    if (type === 'markdown') await copyText(article.markdown_content)
    if (type === 'plain') await copyText(plainText)
    if (type === 'html') {
      const html = buildStyledArticleHtml(article.markdown_content)
      await copyHtml(html, html)
    }
    if (type === 'wechat') {
      await copyHtml(buildWechatHtml(article.markdown_content), plainText, {
        preferRenderedSelection: true,
      })
    }
    onCopied()
    message.success('已复制')
  } catch {
    message.error('复制失败')
  }
}

export async function downloadArticleImagePackage({
  article,
  message,
  setDownloadingImages,
  setImagePackageProgress,
}: {
  article: ArticleDistributionArticle
  message: MessageApi
  setDownloadingImages: (downloading: boolean) => void
  setImagePackageProgress: (progress: ImagePackageProgressState | null) => void
}) {
  setDownloadingImages(true)
  setImagePackageProgress({ percent: 0, title: '准备下载图片包', detail: '正在解析文章图片' })
  try {
    const count = await downloadMarkdownImagesAsZip(article.markdown_content, article.title, {
      onProgress: (progress) => setImagePackageProgress(buildImagePackageProgressState(progress)),
    })
    if (count === 0) {
      message.warning('文章中没有图片')
    } else {
      setImagePackageProgress({ percent: 100, title: '图片包已生成', detail: `已下载 ${count} 张图片` })
      message.success(`已下载 ${count} 张图片`)
    }
  } catch {
    message.error('图片包下载失败')
  } finally {
    setDownloadingImages(false)
    setImagePackageProgress(null)
  }
}
