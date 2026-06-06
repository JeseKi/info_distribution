import { Button, Dropdown, Segmented, Space } from 'antd'
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
  loading,
  view,
  visibleKeys,
  visibleSummaryKeys,
  onExport,
  onRefresh,
  onVisibleKeysChange,
  onVisibleSummaryKeysChange,
  onViewChange,
}: {
  canViewTopics: boolean
  exporting: boolean
  loading: boolean
  view: ArticleDistributionOverviewView
  visibleKeys: string[]
  visibleSummaryKeys: string[]
  onExport: (format: ArticleDistributionReportExportFormat) => void
  onRefresh: () => void
  onVisibleKeysChange: (keys: string[]) => void
  onVisibleSummaryKeysChange: (keys: string[]) => void
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
        visibleSummaryKeys={visibleSummaryKeys}
        onChange={onVisibleKeysChange}
        onSummaryChange={onVisibleSummaryKeysChange}
      />
      <Dropdown
        menu={{
          items: [
            { key: 'xlsx', label: '导出为 Excel' },
            { key: 'csv', label: '导出为 CSV' },
          ],
          onClick: ({ key }) => onExport(key as ArticleDistributionReportExportFormat),
        }}
        trigger={['click']}
        disabled={exporting}
      >
        <Button icon={<DownloadOutlined />} loading={exporting}>
          导出
        </Button>
      </Dropdown>
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
