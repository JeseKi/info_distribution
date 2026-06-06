import { useCallback, useEffect, useMemo, useState } from 'react'
import { Alert, App, Empty, Flex, Form, Table, Typography } from 'antd'
import dayjs from 'dayjs'
import * as articleApi from '../../../lib/articleDistribution'
import { useAuth } from '../../../hooks/useAuth'
import type {
  ArticleDistributionOverview,
  ArticleDistributionOverviewArticle,
  ArticleDistributionOverviewParams,
  ArticleDistributionOverviewView,
  ArticleDistributionReportExportFormat,
} from '../../../lib/types'
import { resolveApiErrorMessage } from '../../../lib/error'
import { ArticleDetailModal } from './ArticleDetailModal'
import { buildArticleColumns } from './articleColumns'
import { buildPlatformColumns, buildTopicColumns, buildUserColumns } from './columns'
import { defaultOverview, metadataScope } from './constants'
import { filterColumns, readVisibleColumns, writeVisibleColumns } from './columnVisibility'
import { isArticleItem, isTopicItem, isUserItem } from './itemGuards'
import { ReportToolbar } from './ReportToolbar'
import { SummaryFilterCard } from './SummaryFilterCard'
import { tableScroll } from './tableUtils'
import type { FilterValues } from './types'

export default function ArticleDistributionReportPage() {
  const { message } = App.useApp()
  const { user } = useAuth()
  const [form] = Form.useForm<FilterValues>()
  const [view, setView] = useState<ArticleDistributionOverviewView>('users')
  const [loading, setLoading] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [exportFormat, setExportFormat] = useState<ArticleDistributionReportExportFormat>('xlsx')
  const [overview, setOverview] = useState<ArticleDistributionOverview>(defaultOverview)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [selectedArticle, setSelectedArticle] = useState<ArticleDistributionOverviewArticle | null>(null)
  const [visibleColumns, setVisibleColumns] = useState<Record<ArticleDistributionOverviewView, string[]>>(() => ({
    users: readVisibleColumns('users'),
    articles: readVisibleColumns('articles'),
    topics: readVisibleColumns('topics'),
  }))

  const canViewTopics = Boolean(user?.effective_scopes.includes(metadataScope))
  const missingTrafficOnly = Form.useWatch('missing_traffic_only', form)

  const buildParams = useCallback((
    nextPage: number,
    nextPageSize: number,
  ): ArticleDistributionOverviewParams => {
    const values = form.getFieldsValue()
    const scheduledRange = values.date_range
    const params: ArticleDistributionOverviewParams = {
      view,
      page: nextPage,
      page_size: nextPageSize,
      keyword: values.keyword?.trim() || undefined,
      platform: values.platform?.trim() || undefined,
      publication_type: values.publication_type,
      publish_status: values.publish_status,
      account_status: values.account_status ?? 'active',
      scheduled_from: scheduledRange?.[0]?.format('YYYY-MM-DD'),
      scheduled_to: scheduledRange?.[1]?.format('YYYY-MM-DD'),
      missing_traffic_only: Boolean(values.missing_traffic_only),
    }
    if (values.missing_traffic_only) {
      const trafficDate = values.traffic_date ?? dayjs()
      params.recorded_from = trafficDate.startOf('day').toISOString()
      params.recorded_to = trafficDate.add(1, 'day').startOf('day').toISOString()
    }
    return params
  }, [form, view])

  const loadOverview = useCallback(async (nextPage = page, nextPageSize = pageSize) => {
    if (view === 'topics' && !canViewTopics) {
      setOverview({ ...defaultOverview, view: 'topics' })
      return
    }
    setLoading(true)
    try {
      const report = await articleApi.listReportOverview(buildParams(nextPage, nextPageSize))
      setOverview(report)
      setPage(report.page)
      setPageSize(report.page_size)
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '统一报表加载失败'))
    } finally {
      setLoading(false)
    }
  }, [buildParams, canViewTopics, message, page, pageSize, view])

  useEffect(() => {
    void loadOverview(page, pageSize)
  }, [loadOverview, page, pageSize])

  const setVisibleKeys = useCallback((keys: string[]) => {
    setVisibleColumns((current) => {
      const next = { ...current, [view]: keys }
      writeVisibleColumns(view, keys)
      return next
    })
  }, [view])

  const handleApplyFilters = () => {
    setPage(1)
    void loadOverview(1, pageSize)
  }

  const handleResetFilters = () => {
    form.resetFields()
    setPage(1)
    void loadOverview(1, pageSize)
  }

  const handleViewChange = (nextView: ArticleDistributionOverviewView) => {
    setView(nextView)
    setPage(1)
  }

  const handleExport = async () => {
    if (view === 'topics' && !canViewTopics) {
      message.error('缺少选题汇总导出权限')
      return
    }
    setExporting(true)
    try {
      await articleApi.downloadReportOverviewExport(buildParams(1, pageSize), exportFormat)
      message.success('文件已开始下载')
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '统一报表导出失败'))
    } finally {
      setExporting(false)
    }
  }

  const summary = overview.summary
  const users = useMemo(() => overview.items.filter(isUserItem), [overview.items])
  const articles = useMemo(() => overview.items.filter(isArticleItem), [overview.items])
  const topics = useMemo(() => overview.items.filter(isTopicItem), [overview.items])

  const userColumns = buildUserColumns()
  const articleColumns = buildArticleColumns({
    includeUser: true,
    includeActions: true,
    onSelectArticle: setSelectedArticle,
  })
  const topicColumns = buildTopicColumns()
  const visibleUserColumns = filterColumns(userColumns, visibleColumns.users)
  const visibleArticleColumns = filterColumns(articleColumns, visibleColumns.articles)
  const visibleTopicColumns = filterColumns(topicColumns, visibleColumns.topics)
  const expandedUserArticleColumns = buildArticleColumns({
    includeUser: false,
    includeActions: true,
    onSelectArticle: setSelectedArticle,
  })
  const expandedTopicArticleColumns = buildArticleColumns({
    includeUser: true,
    includeActions: true,
    onSelectArticle: setSelectedArticle,
  })
  const pagination = {
    current: page,
    pageSize,
    total: overview.total,
    showSizeChanger: true,
    pageSizeOptions: [10, 20, 50, 100],
    showTotal: (_: number, range: [number, number]) => `第 ${range[0]}-${range[1]} 条，共 ${overview.total} 条`,
    onChange: (nextPage: number, nextPageSize: number) => {
      setPage(nextPage)
      setPageSize(nextPageSize)
    },
  }

  return (
    <Flex vertical gap={18}>
      <Flex align="center" justify="space-between" gap={16} wrap="wrap">
        <div>
          <Typography.Title level={2} style={{ margin: 0 }}>
            分发后台
          </Typography.Title>
          <Typography.Text type="secondary">
            用统一筛选查看用户进度、文章明细、未填流量和选题汇总。
          </Typography.Text>
        </div>
        <ReportToolbar
          canViewTopics={canViewTopics}
          exporting={exporting}
          exportFormat={exportFormat}
          loading={loading}
          view={view}
          visibleKeys={visibleColumns[view]}
          onExport={() => void handleExport()}
          onFormatChange={setExportFormat}
          onRefresh={() => void loadOverview(page, pageSize)}
          onVisibleKeysChange={setVisibleKeys}
          onViewChange={handleViewChange}
        />
      </Flex>

      {!canViewTopics && (
        <Alert
          type="info"
          showIcon
          message="选题汇总需要额外权限"
          description={`需要 ${metadataScope} scope。`}
        />
      )}

      <SummaryFilterCard
        form={form}
        missingTrafficOnly={missingTrafficOnly}
        summary={summary}
        onApplyFilters={handleApplyFilters}
        onResetFilters={handleResetFilters}
      />

      {view === 'users' && (
        <Table
          rowKey="user_id"
          loading={loading}
          columns={visibleUserColumns}
          dataSource={users}
          expandable={{
            expandedRowRender: (record) => {
              const platformColumns = buildPlatformColumns(record)
              return (
                <Flex vertical gap={12} style={{ minWidth: 0, width: '100%', overflow: 'hidden' }}>
                  <Table
                    rowKey="account_id"
                    columns={platformColumns}
                    dataSource={record.platform_summaries}
                    pagination={false}
                    size="small"
                    tableLayout="fixed"
                    scroll={tableScroll(platformColumns)}
                  />
                  <Table
                    rowKey="id"
                    columns={expandedUserArticleColumns}
                    dataSource={record.articles}
                    pagination={false}
                    size="small"
                    tableLayout="fixed"
                    scroll={tableScroll(expandedUserArticleColumns)}
                  />
                </Flex>
              )
            },
          }}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无用户数据" /> }}
          pagination={pagination}
          tableLayout="fixed"
          scroll={tableScroll(visibleUserColumns)}
        />
      )}

      {view === 'articles' && (
        <Table
          rowKey="id"
          loading={loading}
          columns={visibleArticleColumns}
          dataSource={articles}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无文章数据" /> }}
          pagination={pagination}
          tableLayout="fixed"
          scroll={tableScroll(visibleArticleColumns)}
        />
      )}

      {view === 'topics' && (
        <Table
          rowKey="key"
          loading={loading}
          columns={visibleTopicColumns}
          dataSource={topics}
          expandable={{
            expandedRowRender: (record) => (
              <Table
                rowKey="id"
                size="small"
                columns={expandedTopicArticleColumns}
                dataSource={record.articles}
                pagination={false}
                tableLayout="fixed"
                scroll={tableScroll(expandedTopicArticleColumns)}
              />
            ),
          }}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无选题数据" /> }}
          pagination={pagination}
          tableLayout="fixed"
          scroll={tableScroll(visibleTopicColumns)}
        />
      )}
      <ArticleDetailModal
        article={selectedArticle}
        onClose={() => setSelectedArticle(null)}
      />
    </Flex>
  )
}
