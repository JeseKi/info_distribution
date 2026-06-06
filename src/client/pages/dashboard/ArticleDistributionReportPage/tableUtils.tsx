import { Space, Tag, Typography } from 'antd'
import type { TableColumnsType } from 'antd'
import type { ReactNode } from 'react'
import type {
  ArticleDistributionOverviewSortBy,
  ArticleDistributionOverviewSortOrder,
  ArticlePublishStatus,
} from '../../../lib/types'

export interface ReportSortState {
  sort_by?: ArticleDistributionOverviewSortBy
  sort_order?: ArticleDistributionOverviewSortOrder
}

export function columnTitle(title: string, icon: ReactNode) {
  return (
    <Space size={6}>
      {icon}
      <span>{title}</span>
    </Space>
  )
}

export function publishStatusTag(status: ArticlePublishStatus) {
  if (status === 'published') return <Tag color="green">已发布</Tag>
  if (status === 'invalid') return <Tag color="red">文档失效</Tag>
  return <Tag>未发布</Tag>
}

export function renderTrafficValue(value: number | undefined) {
  return typeof value === 'number' ? value : '-'
}

export function tableScroll<T extends object>(columns: TableColumnsType<T>) {
  const width = columns.reduce((total, column) => (
    total + (typeof column.width === 'number' ? column.width : 0)
  ), 0)
  return width > 0 ? { x: width } : undefined
}

export function trafficColumn<T extends object, K extends keyof T & string>(
  title: string,
  dataIndex: K,
  icon?: ReactNode,
  sortState?: ReportSortState,
): TableColumnsType<T>[number] {
  return {
    title: icon ? columnTitle(title, icon) : title,
    dataIndex,
    key: dataIndex,
    width: 110,
    sorter: true,
    sortOrder: sortState?.sort_by === dataIndex
      ? (sortState.sort_order === 'asc' ? 'ascend' : 'descend')
      : null,
    render: (value: T[K]) => renderTrafficValue(Number(value)),
  }
}

export function remoteSortOrder(key: ArticleDistributionOverviewSortBy, sortState?: ReportSortState) {
  if (sortState?.sort_by !== key) return null
  return sortState.sort_order === 'asc' ? 'ascend' : 'descend'
}

export function renderMaterials(materials: string[]) {
  if (!materials.length) return '-'
  const visible = materials.slice(0, 2)
  return (
    <Space direction="vertical" size={2}>
      {visible.map((material) => (
        <Typography.Text key={material} ellipsis style={{ maxWidth: 280 }}>
          {material}
        </Typography.Text>
      ))}
      {materials.length > visible.length && (
        <Typography.Text type="secondary">另 {materials.length - visible.length} 条</Typography.Text>
      )}
    </Space>
  )
}
