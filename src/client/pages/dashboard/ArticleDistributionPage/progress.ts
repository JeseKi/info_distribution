import type { ImagePackageDownloadProgress } from '../../../lib/articleDistributionExport'
import type { ImagePackageProgressState } from './types'

export function buildImagePackageProgressState(
  progress: ImagePackageDownloadProgress,
): ImagePackageProgressState {
  if (progress.phase === 'compressing') {
    const zipPercent = Math.round(progress.zipPercent ?? 0)
    return {
      percent: clampPercent(90 + zipPercent / 10),
      title: '正在压缩图片包',
      detail: `已保存 ${progress.savedImages} 张图片，ZIP 生成 ${zipPercent}%`,
    }
  }

  const currentIndex = progress.currentImageIndex ?? Math.min(progress.processedImages + 1, progress.totalImages)
  const percent = calculateImageDownloadPercent(progress)
  return {
    percent,
    title: `正在下载图片 ${currentIndex}/${progress.totalImages}`,
    detail: buildImageDownloadProgressDetail(progress),
  }
}

function calculateImageDownloadPercent(progress: ImagePackageDownloadProgress): number {
  if (progress.totalImages <= 0) return 0
  if (progress.currentImageIndex && progress.currentTotalBytes && progress.currentTotalBytes > 0) {
    const currentRatio = Math.min(progress.currentLoadedBytes / progress.currentTotalBytes, 1)
    return clampPercent(((progress.processedImages + currentRatio) / progress.totalImages) * 90)
  }
  return clampPercent((progress.processedImages / progress.totalImages) * 90)
}

function buildImageDownloadProgressDetail(progress: ImagePackageDownloadProgress): string {
  const savedText = `已保存 ${progress.savedImages} 张图片`
  if (progress.currentTotalBytes && progress.currentTotalBytes > 0) {
    return `当前 ${formatBytes(progress.currentLoadedBytes)} / ${formatBytes(progress.currentTotalBytes)}，累计 ${formatBytes(progress.loadedBytes)}，${savedText}`
  }
  if (progress.currentLoadedBytes > 0) {
    return `当前已接收 ${formatBytes(progress.currentLoadedBytes)}，累计 ${formatBytes(progress.loadedBytes)}，${savedText}`
  }
  return `已处理 ${progress.processedImages}/${progress.totalImages} 张图片，${savedText}`
}

function clampPercent(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)))
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
