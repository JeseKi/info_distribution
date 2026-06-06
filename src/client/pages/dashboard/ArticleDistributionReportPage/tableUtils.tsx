import { Space, Tag, Typography } from 'antd'
import type { TableColumnsType } from 'antd'
import type { ArticlePublishStatus } from '../../../lib/types'

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
): TableColumnsType<T>[number] {
  const valueOf = (record: T) => Number(record[dataIndex] ?? 0)
  return {
    title,
    dataIndex,
    key: dataIndex,
    width: 110,
    sorter: (a: T, b: T) => valueOf(a) - valueOf(b),
    render: (value: T[K]) => renderTrafficValue(Number(value)),
  }
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
