import { useState } from 'react'
import { Button, Checkbox, Divider, Modal, Space, Typography } from 'antd'
import { SettingOutlined } from '@ant-design/icons'
import type { ArticleDistributionOverviewView } from '../../../lib/types'
import { columnLabels, summaryMetricLabels } from './constants'

export function ColumnSelector({
  view,
  visibleKeys,
  visibleSummaryKeys,
  onChange,
  onSummaryChange,
}: {
  view: ArticleDistributionOverviewView
  visibleKeys: string[]
  visibleSummaryKeys: string[]
  onChange: (keys: string[]) => void
  onSummaryChange: (keys: string[]) => void
}) {
  const [open, setOpen] = useState(false)
  const labels = columnLabels[view]
  return (
    <>
      <Button icon={<SettingOutlined />} onClick={() => setOpen(true)}>
        显示设置
      </Button>
      <Modal
        title="显示设置"
        open={open}
        width={620}
        footer={null}
        onCancel={() => setOpen(false)}
      >
        <Space direction="vertical" size={12} style={{ width: '100%' }}>
          <Typography.Title level={5} style={{ margin: 0 }}>
            统计数据
          </Typography.Title>
          <Checkbox.Group
            value={visibleSummaryKeys}
            options={Object.entries(summaryMetricLabels).map(([value, label]) => ({ value, label }))}
            onChange={(values) => onSummaryChange(values.map(String))}
            style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(120px, 1fr))', gap: 8 }}
          />
        </Space>
        <Divider />
        <Space direction="vertical" size={12} style={{ width: '100%' }}>
          <Typography.Title level={5} style={{ margin: 0 }}>
            表格字段
          </Typography.Title>
          <Checkbox.Group
            value={visibleKeys}
            options={Object.entries(labels).map(([value, label]) => ({ value, label }))}
            onChange={(values) => onChange(values.map(String))}
            style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(110px, 1fr))', gap: 8 }}
          />
        </Space>
      </Modal>
    </>
  )
}
