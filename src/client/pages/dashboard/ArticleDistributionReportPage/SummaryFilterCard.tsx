import { useMemo, useState } from 'react'
import { Button, Card, Checkbox, DatePicker, Form, Input, Modal, Select, Space, Statistic } from 'antd'
import {
  BarChartOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CommentOutlined,
  FileTextOutlined,
  FilterOutlined,
  LikeOutlined,
  ProfileOutlined,
  ReadOutlined,
  SearchOutlined,
  ShareAltOutlined,
  StarOutlined,
  TagsOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type { FormInstance } from 'antd'
import type { ReactNode } from 'react'
import type { ArticleDistributionOverviewSummary, Project, Theme } from '../../../lib/types'
import {
  accountStatusOptions,
  publicationTypeOptions,
  publishStatusOptions,
  summaryMetricLabels,
} from './constants'
import type { FilterValues } from './types'

const summaryMetricConfig: {
  key: keyof ArticleDistributionOverviewSummary
  icon: ReactNode
}[] = [
  { key: 'total_users', icon: <TeamOutlined /> },
  { key: 'total_articles', icon: <FileTextOutlined /> },
  { key: 'published_articles', icon: <CheckCircleOutlined /> },
  { key: 'unpublished_articles', icon: <ClockCircleOutlined /> },
  { key: 'invalid_articles', icon: <FileTextOutlined /> },
  { key: 'inactive_account_articles', icon: <TeamOutlined /> },
  { key: 'missing_articles', icon: <BarChartOutlined /> },
  { key: 'topic_count', icon: <TagsOutlined /> },
  { key: 'material_count', icon: <ProfileOutlined /> },
  { key: 'read_count', icon: <ReadOutlined /> },
  { key: 'like_count', icon: <LikeOutlined /> },
  { key: 'favorite_count', icon: <StarOutlined /> },
  { key: 'share_count', icon: <ShareAltOutlined /> },
  { key: 'comment_count', icon: <CommentOutlined /> },
]

export function SummaryFilterCard({
  form,
  missingTrafficOnly,
  projects,
  summary,
  themes,
  visibleSummaryKeys,
  onApplyFilters,
  onResetFilters,
}: {
  form: FormInstance<FilterValues>
  missingTrafficOnly: boolean | undefined
  projects: Project[]
  summary: ArticleDistributionOverviewSummary
  themes: Theme[]
  visibleSummaryKeys: string[]
  onApplyFilters: () => void
  onResetFilters: () => void
}) {
  const [filterModalOpen, setFilterModalOpen] = useState(false)
  const selectedProjectId = Form.useWatch('project_id', form)
  const visibleSummaryMetrics = useMemo(() => {
    const visible = new Set(visibleSummaryKeys)
    return summaryMetricConfig.filter((metric) => visible.has(metric.key))
  }, [visibleSummaryKeys])
  const projectOptions = useMemo(
    () => projects.map((project) => ({
      label: project.is_active ? project.name : `${project.name}（停用）`,
      value: project.id,
    })),
    [projects],
  )
  const themeOptions = useMemo(() => {
    const selectedProject = projects.find((project) => project.id === selectedProjectId)
    const availableThemes = selectedProject
      ? themes.filter((theme) => selectedProject.theme_ids.includes(theme.id))
      : themes
    return availableThemes.map((theme) => ({
      label: theme.is_active ? theme.name : `${theme.name}（停用）`,
      value: theme.id,
    }))
  }, [projects, selectedProjectId, themes])

  const handleApplyFilters = () => {
    onApplyFilters()
    setFilterModalOpen(false)
  }

  const handleResetFilters = () => {
    onResetFilters()
    setFilterModalOpen(false)
  }

  return (
    <Card>
      <Space direction="vertical" size={18} style={{ width: '100%' }}>
        <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space wrap>
            {visibleSummaryMetrics.map((metric) => (
              <Statistic
                key={metric.key}
                title={summaryMetricLabels[metric.key]}
                value={summary[metric.key]}
                prefix={metric.icon}
                style={{ minWidth: 116 }}
              />
            ))}
          </Space>
          <Button icon={<FilterOutlined />} onClick={() => setFilterModalOpen(true)}>
            高级筛选
          </Button>
        </Space>

        <Form
          form={form}
          layout="vertical"
          initialValues={{
            account_status: 'active',
            missing_traffic_only: false,
            traffic_date: dayjs(),
          }}
        >
          <Modal
            title="高级筛选"
            open={filterModalOpen}
            width={860}
            onCancel={() => setFilterModalOpen(false)}
            footer={[
              <Button key="reset" onClick={handleResetFilters}>
                重置
              </Button>,
              <Button key="cancel" onClick={() => setFilterModalOpen(false)}>
                取消
              </Button>,
              <Button key="apply" type="primary" onClick={handleApplyFilters}>
                应用筛选
              </Button>,
            ]}
          >
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '0 16px',
              }}
            >
              <Form.Item label="搜索" name="keyword">
                <Input prefix={<SearchOutlined />} allowClear placeholder="用户、文章、账号或链接" />
              </Form.Item>
              <Form.Item label="项目" name="project_id">
                <Select
                  allowClear
                  options={projectOptions}
                  placeholder="全部项目"
                  onChange={() => form.setFieldValue('theme_id', undefined)}
                />
              </Form.Item>
              <Form.Item label="主题" name="theme_id">
                <Select allowClear options={themeOptions} placeholder="全部主题" />
              </Form.Item>
              <Form.Item label="平台" name="platform">
                <Input allowClear placeholder="wechat、zhihu..." />
              </Form.Item>
              <Form.Item label="发布类型" name="publication_type">
                <Select allowClear options={publicationTypeOptions} placeholder="全部类型" />
              </Form.Item>
              <Form.Item label="发布状态" name="publish_status">
                <Select allowClear options={publishStatusOptions} placeholder="全部状态" />
              </Form.Item>
              <Form.Item label="账号状态" name="account_status">
                <Select options={accountStatusOptions} />
              </Form.Item>
              <Form.Item label="计划日期" name="date_range">
                <DatePicker.RangePicker style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="missing_traffic_only" valuePropName="checked">
                <Checkbox>只看未填流量</Checkbox>
              </Form.Item>
              {missingTrafficOnly && (
                <Form.Item label="流量日期" name="traffic_date">
                  <DatePicker allowClear={false} style={{ width: '100%' }} />
                </Form.Item>
              )}
            </div>
          </Modal>
        </Form>
      </Space>
    </Card>
  )
}
