import { Button, Checkbox, Popover } from 'antd'
import { SettingOutlined } from '@ant-design/icons'
import type { ArticleDistributionOverviewView } from '../../../lib/types'
import { columnLabels } from './constants'

export function ColumnSelector({
  view,
  visibleKeys,
  onChange,
}: {
  view: ArticleDistributionOverviewView
  visibleKeys: string[]
  onChange: (keys: string[]) => void
}) {
  const labels = columnLabels[view]
  return (
    <Popover
      trigger="click"
      placement="bottomRight"
      content={(
        <Checkbox.Group
          value={visibleKeys}
          options={Object.entries(labels).map(([value, label]) => ({ value, label }))}
          onChange={(values) => onChange(values.map(String))}
          style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(110px, 1fr))', gap: 8 }}
        />
      )}
    >
      <Button icon={<SettingOutlined />}>显示字段</Button>
    </Popover>
  )
}
