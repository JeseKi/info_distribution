import type { TableColumnsType } from 'antd'
import type { ArticleDistributionOverviewView } from '../../../lib/types'
import {
  columnLabels,
  defaultVisibleColumns,
  defaultVisibleSummaryMetrics,
  summaryMetricLabels,
} from './constants'

function localStorageKey(view: ArticleDistributionOverviewView) {
  return `article-distribution-report-columns:${view}`
}

const summaryMetricStorageKey = 'article-distribution-report-summary-metrics'

export function readVisibleColumns(view: ArticleDistributionOverviewView) {
  try {
    const raw = window.localStorage.getItem(localStorageKey(view))
    if (!raw) return defaultVisibleColumns[view]
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return defaultVisibleColumns[view]
    const allowed = new Set(Object.keys(columnLabels[view]))
    const selected = parsed.filter((value): value is string => (
      typeof value === 'string' && allowed.has(value)
    ))
    return selected.length ? selected : defaultVisibleColumns[view]
  } catch {
    return defaultVisibleColumns[view]
  }
}

export function writeVisibleColumns(view: ArticleDistributionOverviewView, keys: string[]) {
  window.localStorage.setItem(localStorageKey(view), JSON.stringify(keys))
}

export function readVisibleSummaryMetrics() {
  try {
    const raw = window.localStorage.getItem(summaryMetricStorageKey)
    if (!raw) return defaultVisibleSummaryMetrics
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return defaultVisibleSummaryMetrics
    const allowed = new Set(Object.keys(summaryMetricLabels))
    const selected = parsed.filter((value): value is string => (
      typeof value === 'string' && allowed.has(value)
    ))
    return selected.length ? selected : defaultVisibleSummaryMetrics
  } catch {
    return defaultVisibleSummaryMetrics
  }
}

export function writeVisibleSummaryMetrics(keys: string[]) {
  window.localStorage.setItem(summaryMetricStorageKey, JSON.stringify(keys))
}

export function filterColumns<T extends object>(
  columns: TableColumnsType<T>,
  visibleKeys: string[],
): TableColumnsType<T> {
  return columns.filter((column) => {
    const key = typeof column.key === 'string' ? column.key : undefined
    return !key || visibleKeys.includes(key)
  })
}
