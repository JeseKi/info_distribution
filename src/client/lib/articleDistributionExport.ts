import {
  AlignmentType,
  BorderStyle,
  Document,
  ExternalHyperlink,
  HeadingLevel,
  ImageRun,
  LevelFormat,
  Packer,
  Paragraph,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
  type IRunOptions,
  type ParagraphChild,
} from 'docx'
import { marked, type Token, type Tokens } from 'marked'
import api from './api'
import { getAccessToken } from './tokenStorage'

const copyFrameClass = 'wechat-preview'
const copyContainerClass = 'wechat-preview-container'
const copyContentClass = 'wechat-preview-content'
const wemdDataTool = 'WeMD编辑器'
const docxOrderedListReference = 'article-numbered-list'
const docxBulletListReference = 'article-bullet-list'

type DocxBlock = Paragraph | Table

interface DocxBlockContext {
  indent: number
  listLevel: number
  quote: boolean
}

interface InlineStyle {
  bold?: boolean
  italics?: boolean
  strike?: boolean
  color?: string
}

interface DocxImage {
  data: ArrayBuffer
  contentType: string | null
  width: number
  height: number
}

interface ArticlePackageImage {
  data: ArrayBuffer
  contentType: string | null
}

interface ImageFetchProgress {
  loadedBytes: number
  totalBytes?: number
}

export interface ImagePackageDownloadProgress {
  phase: 'downloading' | 'compressing'
  totalImages: number
  processedImages: number
  savedImages: number
  loadedBytes: number
  currentImageIndex?: number
  currentLoadedBytes: number
  currentTotalBytes?: number
  zipPercent?: number
}

interface ImagePackageDownloadOptions {
  onProgress?: (progress: ImagePackageDownloadProgress) => void
}

const docxTheme = {
  text: '2C2C2C',
  muted: '5F5A52',
  heading: '3B3B38',
  accent: 'C8A062',
  accentDark: '8A6B41',
  quoteBg: 'FBF7F0',
  codeBg: '1F2937',
  codeText: 'E5E7EB',
  inlineCodeBg: 'F3EADB',
  tableBorder: 'ECE3D6',
  tableHeaderBg: 'F7F2E8',
  tableStripeBg: 'FFFAF2',
}

const defaultDocxContext: DocxBlockContext = {
  indent: 0,
  listLevel: 0,
  quote: false,
}

const inlineStyleProperties = [
  'display',
  'box-sizing',
  'max-width',
  'margin-top',
  'margin-right',
  'margin-bottom',
  'margin-left',
  'padding-top',
  'padding-right',
  'padding-bottom',
  'padding-left',
  'border-top-width',
  'border-right-width',
  'border-bottom-width',
  'border-left-width',
  'border-top-style',
  'border-right-style',
  'border-bottom-style',
  'border-left-style',
  'border-top-color',
  'border-right-color',
  'border-bottom-color',
  'border-left-color',
  'border-top-left-radius',
  'border-top-right-radius',
  'border-bottom-right-radius',
  'border-bottom-left-radius',
  'background',
  'background-color',
  'box-shadow',
  'color',
  'font-family',
  'font-size',
  'font-style',
  'font-weight',
  'line-height',
  'letter-spacing',
  'text-align',
  'text-decoration-line',
  'text-decoration-color',
  'text-decoration-style',
  'text-underline-offset',
  'word-break',
  'word-wrap',
  'white-space',
  'overflow',
  'overflow-x',
  'overflow-y',
  'border-collapse',
  'table-layout',
  'list-style-type',
  'list-style-position',
  'vertical-align',
  'opacity',
]

export function markdownToHtml(markdown: string): string {
  return marked.parse(markdown, { async: false, gfm: true }) as string
}

export function markdownToPlainText(markdown: string): string {
  return markdown
    .replace(/!\[[^\]]*]\([^)]+\)/g, '')
    .replace(/\[([^\]]+)]\([^)]+\)/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^[>\-*+]\s+/gm, '')
    .replace(/`{1,3}([^`]+)`{1,3}/g, '$1')
    .replace(/[*_~>#|]/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

export function buildWechatHtml(markdown: string): string {
  return buildStyledArticleHtml(markdown, { wechatCompat: true })
}

export function buildStyledArticleHtml(
  markdown: string,
  options: { wechatCompat?: boolean } = {},
): string {
  const html = `<section id="wemd">${markdownToHtml(markdown)}</section>`
  if (typeof document === 'undefined' || typeof window === 'undefined') {
    return html
  }

  const host = document.createElement('div')
  host.style.position = 'fixed'
  host.style.left = '-10000px'
  host.style.top = '0'
  host.style.width = '760px'
  host.style.pointerEvents = 'none'
  host.style.opacity = '0'
  host.innerHTML = [
    `<div class="${copyFrameClass}">`,
    `<div class="${copyContainerClass}">`,
    `<div class="${copyContentClass}">`,
    html,
    '</div>',
    '</div>',
    '</div>',
  ].join('')

  document.body.appendChild(host)
  try {
    const root = host.querySelector<HTMLElement>('#wemd')
    if (!root) return html
    normalizeArticleCopyTree(root, Boolean(options.wechatCompat))
    inlineComputedStyles(root)
    const copyRoot = options.wechatCompat ? normalizeWechatCopyTree(root) : root
    return copyRoot.outerHTML
  } finally {
    document.body.removeChild(host)
  }
}

export async function copyText(text: string): Promise<void> {
  await navigator.clipboard.writeText(text)
}

export async function copyHtml(
  html: string,
  fallbackText: string,
  options: { preferRenderedSelection?: boolean } = {},
): Promise<void> {
  if (options.preferRenderedSelection && copyRenderedHtml(html)) {
    return
  }

  const clipboard = navigator.clipboard as Clipboard & {
    write?: (items: ClipboardItem[]) => Promise<void>
  }
  if (typeof ClipboardItem !== 'undefined' && clipboard.write) {
    await clipboard.write([
      new ClipboardItem({
        'text/html': new Blob([html], { type: 'text/html' }),
        'text/plain': new Blob([fallbackText], { type: 'text/plain' }),
      }),
    ])
    return
  }

  if (copyRenderedHtml(html)) {
    return
  }

  await navigator.clipboard.writeText(fallbackText)
}

function normalizeArticleCopyTree(root: HTMLElement, wechatCompat: boolean): void {
  root.querySelectorAll<HTMLElement>(
    'p,h1,h2,h3,h4,h5,h6,ul,ol,li,blockquote,pre,table,thead,tbody,tr,th,td,figure,figcaption',
  ).forEach((element) => {
    element.dataset.tool = wemdDataTool
  })

  root.querySelectorAll<HTMLElement>('blockquote').forEach((blockquote) => {
    blockquote.classList.add('multiquote-1')
  })

  root.querySelectorAll<HTMLElement>('pre').forEach((pre) => {
    pre.classList.add('custom')
  })

  root.querySelectorAll<HTMLTableElement>('table').forEach((table) => {
    if (table.parentElement?.classList.contains('table-container')) return
    const wrapper = document.createElement('div')
    wrapper.className = 'table-container'
    table.replaceWith(wrapper)
    wrapper.appendChild(table)
  })

  root.querySelectorAll<HTMLAnchorElement>('a[href]').forEach((link) => {
    link.target = '_blank'
    link.rel = 'noreferrer'
  })

  if (!wechatCompat) return

  root.querySelectorAll<HTMLInputElement>('input[type="checkbox"]').forEach((checkbox) => {
    checkbox.replaceWith(document.createTextNode(`${checkbox.checked ? '✅' : '⬜'}\u00a0`))
  })
}

function inlineComputedStyles(root: HTMLElement): void {
  const elements = [root, ...Array.from(root.querySelectorAll<HTMLElement>('*'))]
  elements.forEach((element) => {
    const computed = window.getComputedStyle(element)
    const style = inlineStyleProperties
      .map((property) => {
        const value = computed.getPropertyValue(property)
        if (!value) return ''
        const priority = computed.getPropertyPriority(property)
        return `${property}:${value}${priority ? ` !${priority}` : ''}`
      })
      .filter(Boolean)
      .join(';')
    if (style) {
      element.setAttribute('style', style)
    }
  })
}

function isZeroSpacing(value: string): boolean {
  const normalized = value.trim().toLowerCase()
  if (!normalized) return true
  if (normalized === '0' || normalized === '0px' || normalized === '0%') return true
  return normalized.split(/\s+/).every((token) => token === '0' || token === '0px' || token === '0%')
}

function parseAlpha(token: string): number | null {
  const trimmed = token.trim()
  if (!trimmed) return null
  if (trimmed.endsWith('%')) {
    const percent = Number.parseFloat(trimmed.slice(0, -1))
    return Number.isFinite(percent) ? percent / 100 : null
  }
  const value = Number.parseFloat(trimmed)
  return Number.isFinite(value) ? value : null
}

function getFunctionalColorAlpha(normalized: string): number | null {
  const match = normalized.match(/^(rgba?|hsla?)\((.*)\)$/)
  if (!match) return null
  const fnName = match[1]
  const body = match[2].trim()
  if (body.includes('/')) {
    return parseAlpha(body.slice(body.lastIndexOf('/') + 1))
  }
  if (fnName === 'rgba' || fnName === 'hsla') {
    const commaParts = body.split(',')
    if (commaParts.length === 4) return parseAlpha(commaParts[3])
  }
  return null
}

function isTransparentBackground(value: string): boolean {
  const normalized = value.replace(/\s+/g, '').toLowerCase()
  if (normalized === 'transparent' || normalized.startsWith('transparent')) return true
  if (/^#[0-9a-f]{4}$/.test(normalized)) return normalized[4] === '0'
  if (/^#[0-9a-f]{8}$/.test(normalized)) return normalized.slice(6, 8) === '00'
  const alpha = getFunctionalColorAlpha(normalized)
  return alpha !== null && alpha <= 0
}

function hasExplicitBackgroundImage(value: string): boolean {
  const normalized = value.trim().toLowerCase()
  if (!normalized || /^none(\s*,\s*none)*$/.test(normalized)) return false
  return !['initial', 'inherit', 'unset', 'revert', 'revert-layer'].includes(normalized)
}

function mergeHorizontalOffset(existingValue: string, rootPadding: string): string {
  const normalized = existingValue.trim().toLowerCase()
  if (['auto', 'inherit', 'initial', 'unset', 'revert', 'revert-layer'].includes(normalized)) {
    return rootPadding
  }
  if (isZeroSpacing(existingValue)) return rootPadding
  return `calc(${existingValue} + ${rootPadding})`
}

function shouldUseMarginForHorizontalOffset(node: HTMLElement): boolean {
  const tagName = node.tagName
  return (
    tagName === 'H1' ||
    tagName === 'H2' ||
    tagName === 'H3' ||
    tagName === 'H4' ||
    tagName === 'H5' ||
    tagName === 'H6' ||
    tagName === 'BLOCKQUOTE' ||
    tagName === 'PRE' ||
    node.classList.contains('callout')
  )
}

function relocateRootPadding(root: HTMLElement): void {
  const paddingLeft = root.style.getPropertyValue('padding-left').trim()
  const paddingRight = root.style.getPropertyValue('padding-right').trim()
  const paddingTop = root.style.getPropertyValue('padding-top').trim()
  const paddingBottom = root.style.getPropertyValue('padding-bottom').trim()
  const hasHorizontalPadding = !isZeroSpacing(paddingLeft) || !isZeroSpacing(paddingRight)
  const hasVerticalPadding = !isZeroSpacing(paddingTop) || !isZeroSpacing(paddingBottom)

  if (hasHorizontalPadding) {
    Array.from(root.children).forEach((child) => {
      if (!(child instanceof HTMLElement)) return
      const useMargin = shouldUseMarginForHorizontalOffset(child)
      if (!isZeroSpacing(paddingLeft)) {
        const property = useMargin ? 'margin-left' : 'padding-left'
        child.style.setProperty(property, mergeHorizontalOffset(child.style.getPropertyValue(property), paddingLeft))
      }
      if (!isZeroSpacing(paddingRight)) {
        const property = useMargin ? 'margin-right' : 'padding-right'
        child.style.setProperty(property, mergeHorizontalOffset(child.style.getPropertyValue(property), paddingRight))
      }
    })
  }

  if (hasVerticalPadding) {
    const innerWrapper = document.createElement('div')
    innerWrapper.style.display = 'block'
    innerWrapper.style.width = '100%'
    innerWrapper.style.boxSizing = 'border-box'
    if (!isZeroSpacing(paddingTop)) innerWrapper.style.setProperty('padding-top', paddingTop)
    if (!isZeroSpacing(paddingBottom)) innerWrapper.style.setProperty('padding-bottom', paddingBottom)
    while (root.firstChild) innerWrapper.appendChild(root.firstChild)
    root.appendChild(innerWrapper)
  }

  root.style.removeProperty('padding')
  root.style.removeProperty('padding-left')
  root.style.removeProperty('padding-right')
  root.style.removeProperty('padding-top')
  root.style.removeProperty('padding-bottom')
}

function extractRootBackgroundColor(root: HTMLElement): string | null {
  const background = root.style.getPropertyValue('background')
  const backgroundColor = root.style.getPropertyValue('background-color')
  let effectiveBackground: string | null = null
  if (backgroundColor && !isTransparentBackground(backgroundColor)) {
    effectiveBackground = backgroundColor
  } else if (background && !isTransparentBackground(background)) {
    effectiveBackground = background
  }
  if (background) root.style.removeProperty('background')
  if (backgroundColor) root.style.removeProperty('background-color')
  return effectiveBackground
}

function hasAncestorWithExplicitBackground(node: HTMLElement, root: HTMLElement): boolean {
  let current = node.parentElement
  while (current && current !== root) {
    const background = current.style.getPropertyValue('background')
    const backgroundColor = current.style.getPropertyValue('background-color')
    const backgroundImage = current.style.getPropertyValue('background-image')
    if (
      (background && !isTransparentBackground(background)) ||
      (backgroundColor && !isTransparentBackground(backgroundColor)) ||
      hasExplicitBackgroundImage(backgroundImage)
    ) {
      return true
    }
    current = current.parentElement
  }
  return false
}

function normalizeBlockBackgrounds(root: HTMLElement, rootBackgroundColor: string | null): void {
  root.querySelectorAll<HTMLElement>('p,h1,h2,h3,h4,h5,h6,ul,ol,li,section,figure,figcaption').forEach((node) => {
    const background = node.style.getPropertyValue('background')
    const backgroundColor = node.style.getPropertyValue('background-color')
    const backgroundImage = node.style.getPropertyValue('background-image')
    const hasExplicitBackground =
      (background && !isTransparentBackground(background)) ||
      (backgroundColor && !isTransparentBackground(backgroundColor)) ||
      hasExplicitBackgroundImage(backgroundImage)
    if (hasExplicitBackground || hasAncestorWithExplicitBackground(node, root)) return

    if (rootBackgroundColor) {
      node.style.setProperty('background-color', rootBackgroundColor, 'important')
    } else {
      node.style.setProperty('background', 'transparent', 'important')
      node.style.setProperty('background-color', 'transparent', 'important')
    }
    node.style.setProperty('background-image', 'none', 'important')
  })
}

function transformWechatRootToDiv(root: HTMLElement): HTMLElement {
  if (root.tagName !== 'SECTION') return root
  const wrapper = document.createElement('div')
  Array.from(root.attributes).forEach((attr) => {
    wrapper.setAttribute(attr.name, attr.value)
  })
  while (root.firstChild) wrapper.appendChild(root.firstChild)
  root.replaceWith(wrapper)
  return wrapper
}

function normalizeWechatCopyTree(sourceRoot: HTMLElement): HTMLElement {
  const root = transformWechatRootToDiv(sourceRoot)
  root.removeAttribute('id')
  root.querySelectorAll<HTMLElement>('[data-tool]').forEach((node) => {
    node.removeAttribute('data-tool')
  })
  const rootBackgroundColor = extractRootBackgroundColor(root)
  relocateRootPadding(root)
  normalizeBlockBackgrounds(root, rootBackgroundColor)
  return root
}

function copyRenderedHtml(html: string): boolean {
  if (typeof document === 'undefined' || typeof window === 'undefined') {
    return false
  }

  const selection = window.getSelection()
  if (!selection) return false

  const container = document.createElement('div')
  container.style.position = 'fixed'
  container.style.left = '-10000px'
  container.style.top = '0'
  container.style.width = '760px'
  container.style.pointerEvents = 'none'
  container.innerHTML = html
  document.body.appendChild(container)

  const range = document.createRange()
  range.selectNodeContents(container)
  selection.removeAllRanges()
  selection.addRange(range)
  try {
    return document.execCommand('copy')
  } catch {
    return false
  } finally {
    selection.removeAllRanges()
    document.body.removeChild(container)
  }
}

export async function downloadMarkdownAsDocx(markdown: string, filename: string): Promise<void> {
  const children = await buildDocxBlocks(markdown)
  const doc = new Document({
    creator: 'Info Distribution',
    numbering: {
      config: [
        {
          reference: docxOrderedListReference,
          levels: buildNumberingLevels(LevelFormat.DECIMAL, '%1.'),
        },
        {
          reference: docxBulletListReference,
          levels: buildNumberingLevels(LevelFormat.BULLET, '•'),
        },
      ],
    },
    styles: {
      default: {
        document: {
          run: {
            font: {
              ascii: 'Aptos',
              eastAsia: 'Microsoft YaHei',
              hAnsi: 'Aptos',
            },
            size: 24,
            color: docxTheme.text,
          },
          paragraph: {
            spacing: { line: 360, after: 180 },
          },
        },
        heading1: {
          run: {
            size: 40,
            bold: true,
            color: docxTheme.heading,
            font: { eastAsia: 'Microsoft YaHei' },
          },
          paragraph: { spacing: { before: 240, after: 220 } },
        },
        heading2: {
          run: {
            size: 32,
            bold: true,
            color: docxTheme.accent,
            font: { eastAsia: 'Microsoft YaHei' },
          },
          paragraph: { spacing: { before: 360, after: 180 } },
        },
        heading3: {
          run: {
            size: 28,
            bold: true,
            color: docxTheme.accentDark,
            font: { eastAsia: 'Microsoft YaHei' },
          },
          paragraph: { spacing: { before: 280, after: 160 } },
        },
        hyperlink: {
          run: {
            color: 'B8874A',
            underline: {},
          },
        },
      },
    },
    sections: [
      {
        properties: {
          page: {
            margin: {
              top: 1080,
              right: 1080,
              bottom: 1080,
              left: 1080,
            },
          },
        },
        children,
      },
    ],
  })
  const blob = await Packer.toBlob(doc)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${sanitizeFilename(filename || 'article')}.docx`
  link.click()
  URL.revokeObjectURL(url)
}

export async function downloadMarkdownImagesAsZip(
  markdown: string,
  filename: string,
  options: ImagePackageDownloadOptions = {},
): Promise<number> {
  const images = extractMarkdownImages(markdown)
  if (images.length === 0) return 0

  const { default: JSZip } = await import('jszip')
  const zip = new JSZip()
  const usedNames = new Set<string>()
  let savedCount = 0
  let processedImages = 0
  let loadedBytes = 0

  const emitProgress = (progress: Omit<ImagePackageDownloadProgress, 'totalImages'>) => {
    options.onProgress?.({
      totalImages: images.length,
      ...progress,
    })
  }

  for (const [index, image] of images.entries()) {
    let currentLoadedBytes = 0
    let currentTotalBytes: number | undefined
    emitProgress({
      phase: 'downloading',
      processedImages,
      savedImages: savedCount,
      loadedBytes,
      currentImageIndex: index + 1,
      currentLoadedBytes,
      currentTotalBytes,
    })

    const packageImage = await fetchImageForPackage(image.href, (progress) => {
      currentLoadedBytes = progress.loadedBytes
      currentTotalBytes = progress.totalBytes
      emitProgress({
        phase: 'downloading',
        processedImages,
        savedImages: savedCount,
        loadedBytes: loadedBytes + currentLoadedBytes,
        currentImageIndex: index + 1,
        currentLoadedBytes,
        currentTotalBytes,
      })
    })
    processedImages += 1
    if (!packageImage) {
      emitProgress({
        phase: 'downloading',
        processedImages,
        savedImages: savedCount,
        loadedBytes,
        currentLoadedBytes: 0,
      })
      continue
    }

    loadedBytes += packageImage.data.byteLength
    zip.file(
      uniqueImageFilename(image, index + 1, packageImage.contentType, usedNames),
      packageImage.data,
    )
    savedCount += 1
    emitProgress({
      phase: 'downloading',
      processedImages,
      savedImages: savedCount,
      loadedBytes,
      currentLoadedBytes: 0,
    })
  }

  if (savedCount === 0) {
    throw new Error('图片包下载失败')
  }

  const blob = await zip.generateAsync({ type: 'blob' }, (metadata) => {
    emitProgress({
      phase: 'compressing',
      processedImages,
      savedImages: savedCount,
      loadedBytes,
      currentLoadedBytes: 0,
      zipPercent: metadata.percent,
    })
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${sanitizeFilename(filename || 'article') || 'article'}-images.zip`
  link.click()
  URL.revokeObjectURL(url)
  return savedCount
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export async function downloadMarkdownImagesAsFiles(
  markdown: string,
  _filename: string,
  options: ImagePackageDownloadOptions = {},
): Promise<number> {
  const images = extractMarkdownImages(markdown)
  if (images.length === 0) return 0

  const usedNames = new Set<string>()
  let savedCount = 0
  let processedImages = 0
  let loadedBytes = 0

  const emitProgress = (progress: Omit<ImagePackageDownloadProgress, 'totalImages'>) => {
    options.onProgress?.({
      totalImages: images.length,
      ...progress,
    })
  }

  for (const [index, image] of images.entries()) {
    let currentLoadedBytes = 0
    let currentTotalBytes: number | undefined
    emitProgress({
      phase: 'downloading',
      processedImages,
      savedImages: savedCount,
      loadedBytes,
      currentImageIndex: index + 1,
      currentLoadedBytes,
      currentTotalBytes,
    })

    const packageImage = await fetchImageForPackage(image.href, (progress) => {
      currentLoadedBytes = progress.loadedBytes
      currentTotalBytes = progress.totalBytes
      emitProgress({
        phase: 'downloading',
        processedImages,
        savedImages: savedCount,
        loadedBytes: loadedBytes + currentLoadedBytes,
        currentImageIndex: index + 1,
        currentLoadedBytes,
        currentTotalBytes,
      })
    })
    processedImages += 1
    if (!packageImage) {
      emitProgress({
        phase: 'downloading',
        processedImages,
        savedImages: savedCount,
        loadedBytes,
        currentLoadedBytes: 0,
      })
      continue
    }

    loadedBytes += packageImage.data.byteLength
    downloadBlob(
      new Blob([packageImage.data], { type: packageImage.contentType ?? 'application/octet-stream' }),
      uniqueImageFilename(image, index + 1, packageImage.contentType, usedNames),
    )
    savedCount += 1
    emitProgress({
      phase: 'downloading',
      processedImages,
      savedImages: savedCount,
      loadedBytes,
      currentLoadedBytes: 0,
    })
  }

  if (savedCount === 0) {
    throw new Error('图片下载失败')
  }

  return savedCount
}

async function buildDocxBlocks(markdown: string): Promise<DocxBlock[]> {
  const tokens = marked.lexer(markdown, { gfm: true })
  const blocks: DocxBlock[] = []
  for (const token of tokens) {
    blocks.push(...await blockTokenToDocx(token, defaultDocxContext))
  }
  return blocks.length > 0 ? blocks : [new Paragraph('')]
}

async function blockTokenToDocx(token: Token, context: DocxBlockContext): Promise<DocxBlock[]> {
  switch (token.type) {
    case 'space':
    case 'def':
      return []
    case 'heading':
      return [await headingToDocx(token as Tokens.Heading, context)]
    case 'paragraph':
      return [await paragraphToDocx((token as Tokens.Paragraph).tokens ?? [], context)]
    case 'text':
      return [await paragraphToDocx((token as Tokens.Text).tokens ?? [token], context)]
    case 'blockquote':
      return blockquoteToDocx(token as Tokens.Blockquote, context)
    case 'list':
      return listToDocx(token as Tokens.List, context)
    case 'code':
      return [codeBlockToDocx(token as Tokens.Code, context)]
    case 'hr':
      return [horizontalRuleToDocx(context)]
    case 'table':
      return [await tableToDocx(token as Tokens.Table)]
    case 'html':
      return htmlTokenToDocx(token as Tokens.HTML | Tokens.Tag, context)
    default:
      return token.raw?.trim()
        ? [new Paragraph({ children: [styledTextRun(stripHtml(token.raw), context)], spacing: paragraphSpacing() })]
        : []
  }
}

async function headingToDocx(token: Tokens.Heading, context: DocxBlockContext): Promise<Paragraph> {
  const heading = [
    HeadingLevel.HEADING_1,
    HeadingLevel.HEADING_2,
    HeadingLevel.HEADING_3,
    HeadingLevel.HEADING_4,
    HeadingLevel.HEADING_5,
    HeadingLevel.HEADING_6,
  ][Math.min(Math.max(token.depth, 1), 6) - 1]
  return new Paragraph({
    heading,
    children: await inlineTokensToRuns(token.tokens, {
      bold: true,
      color: token.depth === 1 ? docxTheme.heading : token.depth === 2 ? docxTheme.accent : docxTheme.accentDark,
    }),
    spacing: {
      before: token.depth === 1 ? 240 : 320,
      after: token.depth === 1 ? 220 : 180,
    },
    indent: paragraphIndent(context),
  })
}

async function paragraphToDocx(tokens: Token[], context: DocxBlockContext): Promise<Paragraph> {
  return new Paragraph({
    children: await inlineTokensToRuns(tokens, { color: context.quote ? docxTheme.muted : docxTheme.text }),
    spacing: paragraphSpacing(),
    indent: paragraphIndent(context),
    shading: context.quote ? { type: ShadingType.CLEAR, fill: docxTheme.quoteBg } : undefined,
    border: context.quote
      ? {
          left: {
            style: BorderStyle.SINGLE,
            color: docxTheme.accent,
            size: 16,
            space: 8,
          },
        }
      : undefined,
  })
}

async function blockquoteToDocx(token: Tokens.Blockquote, context: DocxBlockContext): Promise<DocxBlock[]> {
  const blocks: DocxBlock[] = []
  const nextContext = { ...context, indent: context.indent + 240, quote: true }
  for (const childToken of token.tokens) {
    blocks.push(...await blockTokenToDocx(childToken, nextContext))
  }
  return blocks
}

async function listToDocx(token: Tokens.List, context: DocxBlockContext): Promise<DocxBlock[]> {
  const blocks: DocxBlock[] = []
  for (const item of token.items) {
    const firstToken = item.tokens.find((child) => child.type !== 'space')
    const firstTokens = firstToken && firstToken.type === 'paragraph'
      ? firstToken.tokens
      : [{ type: 'text', raw: item.text, text: item.text } satisfies Tokens.Text]
    const prefix = item.task ? `${item.checked ? '☑' : '☐'} ` : ''
    blocks.push(new Paragraph({
      children: [
        ...(prefix ? [styledTextRun(prefix, context, { color: docxTheme.accentDark })] : []),
        ...await inlineTokensToRuns(firstTokens, { color: docxTheme.text }),
      ],
      numbering: {
        reference: token.ordered ? docxOrderedListReference : docxBulletListReference,
        level: Math.min(context.listLevel, 2),
      },
      spacing: { before: 0, after: 120, line: 330 },
    }))

    const restTokens = firstToken && firstToken.type === 'paragraph'
      ? item.tokens.filter((child) => child !== firstToken)
      : item.tokens
    for (const childToken of restTokens) {
      blocks.push(...await blockTokenToDocx(childToken, {
        ...context,
        indent: context.indent + 360,
        listLevel: context.listLevel + 1,
      }))
    }
  }
  return blocks
}

function codeBlockToDocx(token: Tokens.Code, context: DocxBlockContext): Paragraph {
  const lines = token.text.split('\n')
  const children = lines.flatMap((line, index) => [
    new TextRun({
      text: line || ' ',
      break: index === 0 ? undefined : 1,
      font: 'Consolas',
      size: 21,
      color: docxTheme.codeText,
    }),
  ])
  return new Paragraph({
    children,
    shading: { type: ShadingType.CLEAR, fill: docxTheme.codeBg },
    spacing: { before: 160, after: 220, line: 300 },
    indent: paragraphIndent(context),
    border: {
      top: { style: BorderStyle.SINGLE, color: docxTheme.codeBg, size: 8, space: 8 },
      bottom: { style: BorderStyle.SINGLE, color: docxTheme.codeBg, size: 8, space: 8 },
      left: { style: BorderStyle.SINGLE, color: docxTheme.codeBg, size: 8, space: 8 },
      right: { style: BorderStyle.SINGLE, color: docxTheme.codeBg, size: 8, space: 8 },
    },
  })
}

function horizontalRuleToDocx(context: DocxBlockContext): Paragraph {
  return new Paragraph({
    children: [styledTextRun('────────────', context, { color: docxTheme.accent })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 220, after: 220 },
  })
}

async function tableToDocx(token: Tokens.Table): Promise<Table> {
  const rows = [
    new TableRow({
      children: await Promise.all(token.header.map((cell) => tableCellToDocx(cell, true))),
    }),
    ...await Promise.all(token.rows.map(async (row, rowIndex) => new TableRow({
      children: await Promise.all(row.map((cell) => tableCellToDocx(cell, false, rowIndex % 2 === 1))),
    }))),
  ]
  return new Table({
    rows,
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: tableBorder(),
      bottom: tableBorder(),
      left: tableBorder(),
      right: tableBorder(),
      insideHorizontal: tableBorder(),
      insideVertical: tableBorder(),
    },
  })
}

async function tableCellToDocx(cell: Tokens.TableCell, header: boolean, striped = false): Promise<TableCell> {
  return new TableCell({
    shading: header
      ? { type: ShadingType.CLEAR, fill: docxTheme.tableHeaderBg }
      : striped ? { type: ShadingType.CLEAR, fill: docxTheme.tableStripeBg } : undefined,
    margins: { top: 120, bottom: 120, left: 140, right: 140 },
    children: [
      new Paragraph({
        children: await inlineTokensToRuns(cell.tokens, {
          bold: header,
          color: header ? docxTheme.accentDark : docxTheme.text,
        }),
        alignment: cell.align === 'center'
          ? AlignmentType.CENTER
          : cell.align === 'right' ? AlignmentType.RIGHT : AlignmentType.LEFT,
        spacing: { before: 0, after: 0, line: 300 },
      }),
    ],
  })
}

async function htmlTokenToDocx(token: Tokens.HTML | Tokens.Tag, context: DocxBlockContext): Promise<DocxBlock[]> {
  const imageTokens = extractHtmlImages(token.raw)
  if (imageTokens.length > 0) {
    const paragraphs: Paragraph[] = []
    for (const imageToken of imageTokens) {
      paragraphs.push(await imageToParagraph(imageToken, context))
    }
    return paragraphs
  }
  const text = stripHtml(token.raw).trim()
  return text ? [new Paragraph({ children: [styledTextRun(text, context)], spacing: paragraphSpacing() })] : []
}

async function inlineTokensToRuns(tokens: Token[] = [], style: InlineStyle = {}): Promise<ParagraphChild[]> {
  const runs: ParagraphChild[] = []
  for (const token of tokens) {
    switch (token.type) {
      case 'text':
      case 'escape':
        if ('tokens' in token && token.tokens) {
          runs.push(...await inlineTokensToRuns(token.tokens, style))
        } else if ('text' in token && token.text) {
          runs.push(new TextRun({ text: token.text, ...textRunStyle(style) }))
        }
        break
      case 'strong':
        runs.push(...await inlineTokensToRuns((token as Tokens.Strong).tokens, { ...style, bold: true }))
        break
      case 'em':
        runs.push(...await inlineTokensToRuns((token as Tokens.Em).tokens, { ...style, italics: true }))
        break
      case 'del':
        runs.push(...await inlineTokensToRuns((token as Tokens.Del).tokens, { ...style, strike: true }))
        break
      case 'codespan': {
        const codeToken = token as Tokens.Codespan
        runs.push(new TextRun({
          text: codeToken.text,
          font: 'Consolas',
          size: 21,
          color: docxTheme.text,
          shading: { type: ShadingType.CLEAR, fill: docxTheme.inlineCodeBg },
        }))
        break
      }
      case 'br':
        runs.push(new TextRun({ text: '', break: 1 }))
        break
      case 'link': {
        const linkToken = token as Tokens.Link
        runs.push(new ExternalHyperlink({
          link: linkToken.href,
          children: await inlineTokensToRuns(linkToken.tokens, { ...style, color: 'B8874A' }),
        }))
        break
      }
      case 'image':
        runs.push(...await imageToRuns(token as Tokens.Image))
        break
      case 'html':
        runs.push(...htmlInlineToRuns(token.raw, style))
        break
      default:
        if (token.raw) {
          runs.push(new TextRun({ text: stripHtml(token.raw), ...textRunStyle(style) }))
        }
        break
    }
  }
  return runs.length > 0 ? runs : [new TextRun('')]
}

async function imageToParagraph(token: Tokens.Image, context: DocxBlockContext): Promise<Paragraph> {
  return new Paragraph({
    children: await imageToRuns(token),
    alignment: AlignmentType.CENTER,
    spacing: { before: 160, after: token.text ? 80 : 220 },
    indent: paragraphIndent(context),
  })
}

async function imageToRuns(token: Tokens.Image): Promise<ParagraphChild[]> {
  const image = await fetchImageForDocx(token.href)
  if (!image) {
    return [new TextRun({ text: `[图片无法下载：${token.text || token.href}]`, color: 'BE123C' })]
  }
  const type = resolveImageType(image.contentType, token.href)
  if (!type) {
    return [new TextRun({ text: `[暂不支持的图片格式：${token.text || token.href}]`, color: 'BE123C' })]
  }
  return [
    new ImageRun({
      data: image.data,
      transformation: scaleImage(image.width, image.height),
      type,
      altText: {
        title: token.text || '文章图片',
        description: token.text || token.href,
        name: token.text || 'article-image',
      },
    }),
  ]
}

function styledTextRun(text: string, context: DocxBlockContext, style: InlineStyle = {}): TextRun {
  return new TextRun({
    text,
    ...textRunStyle({ color: context.quote ? docxTheme.muted : docxTheme.text, ...style }),
  })
}

function textRunStyle(style: InlineStyle): IRunOptions {
  return {
    bold: style.bold,
    italics: style.italics,
    strike: style.strike,
    color: style.color,
    font: {
      ascii: 'Aptos',
      eastAsia: 'Microsoft YaHei',
      hAnsi: 'Aptos',
    },
  }
}

function paragraphSpacing() {
  return { before: 0, after: 180, line: 360 }
}

function paragraphIndent(context: DocxBlockContext) {
  return context.indent > 0 ? { left: context.indent } : undefined
}

function tableBorder() {
  return { style: BorderStyle.SINGLE, color: docxTheme.tableBorder, size: 4 }
}

function buildNumberingLevels(format: typeof LevelFormat.DECIMAL | typeof LevelFormat.BULLET, text: string) {
  return [0, 1, 2].map((level) => ({
    level,
    format,
    text,
    alignment: AlignmentType.LEFT,
    style: {
      paragraph: {
        indent: {
          left: 720 + level * 360,
          hanging: 360,
        },
      },
    },
  }))
}

function extractHtmlImages(html: string): Tokens.Image[] {
  return [...html.matchAll(/<img\b[^>]*\bsrc=["']([^"']+)["'][^>]*>/gi)].map((match) => ({
    type: 'image',
    raw: match[0],
    href: decodeHtmlAttribute(match[1]),
    title: null,
    text: decodeHtmlAttribute(extractHtmlAttribute(match[0], 'alt') ?? ''),
    tokens: [],
  }))
}

function extractMarkdownImages(markdown: string): Tokens.Image[] {
  const tokens = marked.lexer(markdown, { gfm: true })
  const images: Tokens.Image[] = []
  collectImagesFromTokens(tokens, images)
  return images
}

function collectImagesFromTokens(tokens: Token[] = [], images: Tokens.Image[]): void {
  for (const token of tokens) {
    if (token.type === 'image') {
      images.push(token as Tokens.Image)
      continue
    }
    if (token.type === 'html') {
      images.push(...extractHtmlImages(token.raw))
      continue
    }
    if ('tokens' in token && Array.isArray(token.tokens)) {
      collectImagesFromTokens(token.tokens, images)
    }
    if (token.type === 'list') {
      for (const item of (token as Tokens.List).items) {
        collectImagesFromTokens(item.tokens, images)
      }
    }
  }
}

function uniqueImageFilename(
  image: Tokens.Image,
  index: number,
  contentType: string | null,
  usedNames: Set<string>,
): string {
  const sourceName = image.href.startsWith('data:') ? '' : image.href
  const urlName = sourceName ? imageFilenameFromUrl(sourceName) : ''
  const fallbackName = sanitizeFilename(image.text || `image-${index}`)
  const extension = imageExtension(contentType, image.href)
  const rawName = sanitizeFilename(urlName || fallbackName || `image-${index}`)
  const dotIndex = rawName.lastIndexOf('.')
  const base = dotIndex > 0 ? rawName.slice(0, dotIndex) : rawName
  const existingExtension = dotIndex > 0 ? rawName.slice(dotIndex + 1).toLowerCase() : ''
  const normalizedExtension = existingExtension || extension
  let candidate = `${base || `image-${index}`}.${normalizedExtension}`
  let suffix = 2

  while (usedNames.has(candidate)) {
    candidate = `${base || `image-${index}`}-${suffix}.${normalizedExtension}`
    suffix += 1
  }
  usedNames.add(candidate)
  return candidate
}

function imageFilenameFromUrl(url: string): string {
  try {
    const parsed = new URL(resolveImageUrl(url))
    return decodeURIComponent(parsed.pathname.split('/').filter(Boolean).at(-1) ?? '')
  } catch {
    return ''
  }
}

function imageExtension(contentType: string | null, url: string): string {
  const normalizedContentType = contentType?.toLowerCase() ?? ''
  const normalizedUrl = url.toLowerCase()
  if (normalizedContentType.includes('png') || normalizedUrl.endsWith('.png')) return 'png'
  if (normalizedContentType.includes('gif') || normalizedUrl.endsWith('.gif')) return 'gif'
  if (normalizedContentType.includes('bmp') || normalizedUrl.endsWith('.bmp')) return 'bmp'
  if (normalizedContentType.includes('webp') || normalizedUrl.endsWith('.webp')) return 'webp'
  if (normalizedContentType.includes('svg') || normalizedUrl.endsWith('.svg')) return 'svg'
  if (normalizedContentType.includes('jpeg') || normalizedContentType.includes('jpg') || /\.jpe?g$/i.test(url)) return 'jpg'
  return 'png'
}

function htmlInlineToRuns(html: string, style: InlineStyle): ParagraphChild[] {
  const images = extractHtmlImages(html)
  if (images.length > 0) return []
  const text = stripHtml(html)
  return text ? [new TextRun({ text, ...textRunStyle(style) })] : []
}

function extractHtmlAttribute(html: string, name: string): string | null {
  const match = new RegExp(`\\b${name}=["']([^"']*)["']`, 'i').exec(html)
  return match ? match[1] : null
}

function stripHtml(value: string): string {
  const host = typeof document !== 'undefined' ? document.createElement('div') : null
  if (host) {
    host.innerHTML = value
    return host.textContent || ''
  }
  return value.replace(/<[^>]+>/g, '')
}

function decodeHtmlAttribute(value: string): string {
  const host = typeof document !== 'undefined' ? document.createElement('textarea') : null
  if (!host) return value
  host.innerHTML = value
  return host.value
}

async function fetchImageForDocx(url: string): Promise<DocxImage | null> {
  if (url.startsWith('data:')) {
    const parsed = parseDataUrl(url)
    if (!parsed) return null
    return prepareDocxImage(parsed.data, parsed.contentType, url)
  }

  const resolvedUrl = resolveImageUrl(url)
  try {
    const response = await fetchImageDirectly(resolvedUrl)
    if (response.ok) {
      const data = await response.arrayBuffer()
      const contentType = response.headers.get('content-type')
      return prepareDocxImage(data, contentType, resolvedUrl)
    }
  } catch {
    // Cross-origin images often fail here because the image host does not allow CORS.
  }

  if (!/^https?:\/\//i.test(resolvedUrl)) {
    return null
  }

  if (!shouldProxyImageUrl(resolvedUrl)) {
    return null
  }

  try {
    const response = await api.get<ArrayBuffer>('/article-distribution/image-proxy', {
      params: { url: resolvedUrl },
      responseType: 'arraybuffer',
    })
    const data = response.data
    const contentType = String(response.headers['content-type'] ?? '')
    return prepareDocxImage(data, contentType, resolvedUrl)
  } catch {
    return null
  }
}

async function fetchImageForPackage(
  url: string,
  onProgress?: (progress: ImageFetchProgress) => void,
): Promise<ArticlePackageImage | null> {
  if (url.startsWith('data:')) {
    const parsed = parseDataUrl(url)
    if (parsed) {
      onProgress?.({ loadedBytes: parsed.data.byteLength, totalBytes: parsed.data.byteLength })
    }
    return parsed
  }

  const resolvedUrl = resolveImageUrl(url)
  try {
    const response = await fetchImageDirectly(resolvedUrl)
    if (response.ok) {
      const data = await readResponseArrayBuffer(response, onProgress)
      return {
        data,
        contentType: response.headers.get('content-type'),
      }
    }
  } catch {
    // Cross-origin images often fail here because the image host does not allow CORS.
  }

  if (!/^https?:\/\//i.test(resolvedUrl) || !shouldProxyImageUrl(resolvedUrl)) {
    return null
  }

  try {
    const response = await api.get<ArrayBuffer>('/article-distribution/image-proxy', {
      params: { url: resolvedUrl },
      responseType: 'arraybuffer',
      onDownloadProgress: (event) => {
        onProgress?.({
          loadedBytes: event.loaded,
          totalBytes: event.total && event.total > 0 ? event.total : undefined,
        })
      },
    })
    onProgress?.({ loadedBytes: response.data.byteLength, totalBytes: response.data.byteLength })
    return {
      data: response.data,
      contentType: String(response.headers['content-type'] ?? ''),
    }
  } catch {
    return null
  }
}

async function readResponseArrayBuffer(
  response: Response,
  onProgress?: (progress: ImageFetchProgress) => void,
): Promise<ArrayBuffer> {
  const totalBytes = parseContentLength(response.headers.get('content-length'))
  if (!response.body) {
    const data = await response.arrayBuffer()
    onProgress?.({ loadedBytes: data.byteLength, totalBytes: totalBytes ?? data.byteLength })
    return data
  }

  const reader = response.body.getReader()
  const chunks: Uint8Array[] = []
  let loadedBytes = 0

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    if (!value) continue

    chunks.push(value)
    loadedBytes += value.byteLength
    onProgress?.({ loadedBytes, totalBytes })
  }

  const data = new Uint8Array(loadedBytes)
  let offset = 0
  for (const chunk of chunks) {
    data.set(chunk, offset)
    offset += chunk.byteLength
  }
  return data.buffer as ArrayBuffer
}

function parseContentLength(value: string | null): number | undefined {
  if (!value) return undefined
  const parsed = Number.parseInt(value, 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined
}

async function fetchImageDirectly(url: string): Promise<Response> {
  const headers = new Headers()
  if (shouldAttachAppAuth(url)) {
    const accessToken = getAccessToken()
    if (accessToken) {
      headers.set('Authorization', `Bearer ${accessToken}`)
    }
  }

  return fetch(url, {
    credentials: shouldAttachAppAuth(url) ? 'include' : 'omit',
    headers,
  })
}

function shouldAttachAppAuth(url: string): boolean {
  if (typeof window === 'undefined') return false
  try {
    const parsed = new URL(url)
    const current = new URL(window.location.href)
    return parsed.origin === current.origin || isLocalOrPrivateHostname(parsed.hostname)
  } catch {
    return false
  }
}

function shouldProxyImageUrl(url: string): boolean {
  try {
    const parsed = new URL(url)
    if (!['http:', 'https:'].includes(parsed.protocol)) return false
    if (typeof window !== 'undefined' && parsed.origin === window.location.origin) {
      return false
    }
    return !isLocalOrPrivateHostname(parsed.hostname)
  } catch {
    return false
  }
}

async function prepareDocxImage(
  data: ArrayBuffer,
  contentType: string | null,
  sourceUrl: string,
): Promise<DocxImage> {
  const dimensions = await resolveImageDimensions(data, contentType)
  if (resolveImageType(contentType, sourceUrl)) {
    return { data, contentType, ...dimensions }
  }

  const rasterized = await rasterizeImageToPng(data, contentType, dimensions)
  if (rasterized) {
    return rasterized
  }
  return { data, contentType, ...dimensions }
}

function parseDataUrl(url: string): { data: ArrayBuffer; contentType: string | null } | null {
  const match = /^data:([^;,]+)?(;base64)?,(.*)$/i.exec(url)
  if (!match) return null
  const contentType = match[1] || null
  const isBase64 = Boolean(match[2])
  const raw = isBase64 ? atob(match[3]) : decodeURIComponent(match[3])
  const bytes = new Uint8Array(raw.length)
  for (let index = 0; index < raw.length; index += 1) {
    bytes[index] = raw.charCodeAt(index)
  }
  return { data: bytes.buffer, contentType }
}

function resolveImageType(contentType: string | null, url: string): 'jpg' | 'png' | 'gif' | 'bmp' | null {
  const normalizedContentType = contentType?.toLowerCase() ?? ''
  const normalizedUrl = url.toLowerCase()
  if (normalizedContentType.includes('png') || normalizedUrl.endsWith('.png')) return 'png'
  if (
    normalizedContentType.includes('jpeg') ||
    normalizedContentType.includes('jpg') ||
    normalizedUrl.endsWith('.jpg') ||
    normalizedUrl.endsWith('.jpeg')
  ) return 'jpg'
  if (normalizedContentType.includes('gif') || normalizedUrl.endsWith('.gif')) return 'gif'
  if (normalizedContentType.includes('bmp') || normalizedUrl.endsWith('.bmp')) return 'bmp'
  return null
}

function resolveImageUrl(url: string): string {
  if (/^https?:\/\//i.test(url) || url.startsWith('data:')) return url
  if (typeof window === 'undefined') return url
  return new URL(url, window.location.origin).toString()
}

function isLocalOrPrivateHostname(hostname: string): boolean {
  const normalized = hostname.toLowerCase().replace(/^\[|\]$/g, '')
  if (
    normalized === 'localhost' ||
    normalized.endsWith('.localhost') ||
    normalized.endsWith('.local')
  ) {
    return true
  }

  if (normalized === '::1' || normalized.startsWith('fe80:') || normalized.startsWith('fc') || normalized.startsWith('fd')) {
    return true
  }

  const parts = normalized.split('.').map((part) => Number.parseInt(part, 10))
  if (parts.length !== 4 || parts.some((part) => Number.isNaN(part))) {
    return false
  }

  const [first, second] = parts
  return (
    first === 10 ||
    first === 127 ||
    (first === 169 && second === 254) ||
    (first === 172 && second >= 16 && second <= 31) ||
    (first === 192 && second === 168)
  )
}

async function resolveImageDimensions(
  data: ArrayBuffer,
  contentType: string | null,
): Promise<{ width: number; height: number }> {
  if (typeof Image === 'undefined' || typeof URL === 'undefined') {
    return { width: 520, height: 292 }
  }
  const objectUrl = URL.createObjectURL(new Blob([data], { type: contentType || 'image/jpeg' }))
  try {
    return await new Promise((resolve) => {
      const image = new Image()
      image.onload = () => resolve({
        width: image.naturalWidth || 520,
        height: image.naturalHeight || 292,
      })
      image.onerror = () => resolve({ width: 520, height: 292 })
      image.src = objectUrl
    })
  } finally {
    URL.revokeObjectURL(objectUrl)
  }
}

async function rasterizeImageToPng(
  data: ArrayBuffer,
  contentType: string | null,
  fallbackDimensions: { width: number; height: number },
): Promise<DocxImage | null> {
  if (
    typeof Image === 'undefined' ||
    typeof URL === 'undefined' ||
    typeof document === 'undefined'
  ) {
    return null
  }

  const objectUrl = URL.createObjectURL(new Blob([data], { type: contentType || 'image/*' }))
  try {
    const image = await new Promise<HTMLImageElement | null>((resolve) => {
      const element = new Image()
      element.onload = () => resolve(element)
      element.onerror = () => resolve(null)
      element.src = objectUrl
    })
    if (!image) return null

    const width = image.naturalWidth || fallbackDimensions.width
    const height = image.naturalHeight || fallbackDimensions.height
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const context = canvas.getContext('2d')
    if (!context) return null
    context.drawImage(image, 0, 0, width, height)

    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(resolve, 'image/png')
    })
    if (!blob) return null
    return {
      data: await blob.arrayBuffer(),
      contentType: 'image/png',
      width,
      height,
    }
  } catch {
    return null
  } finally {
    URL.revokeObjectURL(objectUrl)
  }
}

function scaleImage(width: number, height: number): { width: number; height: number } {
  const maxWidth = 520
  const maxHeight = 360
  const ratio = Math.min(maxWidth / width, maxHeight / height, 1)
  return {
    width: Math.max(1, Math.round(width * ratio)),
    height: Math.max(1, Math.round(height * ratio)),
  }
}

function sanitizeFilename(filename: string): string {
  return filename.replace(/[\\/:*?"<>|]+/g, '_').slice(0, 80)
}
