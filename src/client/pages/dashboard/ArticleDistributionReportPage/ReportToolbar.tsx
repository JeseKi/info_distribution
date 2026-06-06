import { Button, Select, Segmented, Space } from 'antd'
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import type {
  ArticleDistributionOverviewView,
  ArticleDistributionReportExportFormat,
} from '../../../lib/types'
import { viewOptions } from './constants'
import { ColumnSelector } from './ColumnSelector'

export function ReportToolbar({
  canViewTopics,
  exporting,
  exportFormat,
  loading,
  view,
  visibleKeys,
  onExport,
  onFormatChange,
  onRefresh,
  onVisibleKeysChange,
  onViewChange,
}: {
  canViewTopics: boolean
  exporting: boolean
  exportFormat: ArticleDistributionReportExportFormat
  loading: boolean
  view: ArticleDistributionOverviewView
  visibleKeys: string[]
  onExport: () => void
  onFormatChange: (format: ArticleDistributionReportExportFormat) => void
  onRefresh: () => void
  onVisibleKeysChange: (keys: string[]) => void
  onViewChange: (view: ArticleDistributionOverviewView) => void
}) {
  return (
    <Space wrap>
      <Segmented
        value={view}
        options={viewOptions.map((option) => ({
          ...option,
          disabled: option.value === 'topics' && !canViewTopics,
        }))}
        onChange={(value) => onViewChange(value as ArticleDistributionOverviewView)}
      />
      <ColumnSelector
        view={view}
        visibleKeys={visibleKeys}
        onChange={onVisibleKeysChange}
      />
      <Select<ArticleDistributionReportExportFormat>
        value={exportFormat}
        options={[
          { label: 'Excel', value: 'xlsx' },
          { label: 'CSV', value: 'csv' },
        ]}
        style={{ width: 96 }}
        onChange={onFormatChange}
      />
      <Button
        icon={<DownloadOutlined />}
        loading={exporting}
        onClick={onExport}
      >
        导出
      </Button>
      <Button
        icon={<ReloadOutlined />}
        loading={loading}
        onClick={onRefresh}
      >
        刷新
      </Button>
    </Space>
  )
}
