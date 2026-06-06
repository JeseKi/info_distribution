import { Button, Card, Checkbox, DatePicker, Flex, Form, Input, Select, Space, Statistic } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import type { FormInstance } from 'antd'
import type { ArticleDistributionOverviewSummary } from '../../../lib/types'
import { accountStatusOptions, publicationTypeOptions, publishStatusOptions } from './constants'
import type { FilterValues } from './types'

export function SummaryFilterCard({
  form,
  missingTrafficOnly,
  summary,
  onApplyFilters,
  onResetFilters,
}: {
  form: FormInstance<FilterValues>
  missingTrafficOnly: boolean | undefined
  summary: ArticleDistributionOverviewSummary
  onApplyFilters: () => void
  onResetFilters: () => void
}) {
  return (
    <Card>
      <Flex gap={24} wrap="wrap">
        <Statistic title="用户数" value={summary.total_users} />
        <Statistic title="文章数" value={summary.total_articles} />
        <Statistic title="已发布" value={summary.published_articles} />
        <Statistic title="未发布" value={summary.unpublished_articles} />
        <Statistic title="未填流量" value={summary.missing_articles} />
        <Statistic title="选题数" value={summary.topic_count} />
        <Statistic title="素材数" value={summary.material_count} />
        <Statistic title="阅读量" value={summary.read_count} />
        <Statistic title="点赞量" value={summary.like_count} />
        <Statistic title="收藏量" value={summary.favorite_count} />
        <Statistic title="转发量" value={summary.share_count} />
      </Flex>

      <Form
        form={form}
        layout="vertical"
        initialValues={{
          account_status: 'active',
          missing_traffic_only: false,
          traffic_date: dayjs(),
        }}
        style={{ marginTop: 18 }}
      >
        <Flex gap={16} wrap="wrap" align="end">
          <Form.Item label="搜索" name="keyword" style={{ minWidth: 240 }}>
            <Input prefix={<SearchOutlined />} allowClear placeholder="用户、文章、账号或链接" />
          </Form.Item>
          <Form.Item label="平台" name="platform" style={{ minWidth: 180 }}>
            <Input allowClear placeholder="wechat、zhihu..." />
          </Form.Item>
          <Form.Item label="发布类型" name="publication_type" style={{ minWidth: 150 }}>
            <Select allowClear options={publicationTypeOptions} placeholder="全部类型" />
          </Form.Item>
          <Form.Item label="发布状态" name="publish_status" style={{ minWidth: 150 }}>
            <Select allowClear options={publishStatusOptions} placeholder="全部状态" />
          </Form.Item>
          <Form.Item label="账号状态" name="account_status" style={{ minWidth: 130 }}>
            <Select options={accountStatusOptions} />
          </Form.Item>
          <Form.Item label="计划日期" name="date_range" style={{ minWidth: 260 }}>
            <DatePicker.RangePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="missing_traffic_only" valuePropName="checked">
            <Checkbox>只看未填流量</Checkbox>
          </Form.Item>
          {missingTrafficOnly && (
            <Form.Item label="流量日期" name="traffic_date" style={{ minWidth: 180 }}>
              <DatePicker allowClear={false} style={{ width: '100%' }} />
            </Form.Item>
          )}
          <Form.Item>
            <Space>
              <Button type="primary" onClick={onApplyFilters}>
                筛选
              </Button>
              <Button onClick={onResetFilters}>
                重置
              </Button>
            </Space>
          </Form.Item>
        </Flex>
      </Form>
    </Card>
  )
}
