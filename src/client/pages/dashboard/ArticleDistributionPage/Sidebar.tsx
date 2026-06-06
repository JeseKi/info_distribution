import { Button, DatePicker, Flex, Form, Popconfirm, Select, Space, Statistic, Typography } from 'antd'
import { DeleteOutlined, EditOutlined } from '@ant-design/icons'
import type { FormInstance } from 'antd'
import type { ArticleDistributionAccount } from '../../../lib/types'
import { publicationTypeOptions, publicationTypeText, publishStatusOptions } from './constants'
import { inactiveAccountTag } from './statusTags'
import type { AccountSelectOption, ArticleFilterFormValues } from './types'

export function Sidebar({
  accounts,
  accountOptions,
  articlePageSize,
  filterForm,
  invalidCount,
  isAdmin,
  publishedCount,
  unreadCount,
  onApplyFilters,
  onDeleteAccount,
  onEditAccount,
  onResetFilters,
  onToggleAccountActive,
}: {
  accounts: ArticleDistributionAccount[]
  accountOptions: AccountSelectOption[]
  articlePageSize: number
  filterForm: FormInstance<ArticleFilterFormValues>
  invalidCount: number
  isAdmin: boolean
  publishedCount: number
  unreadCount: number
  onApplyFilters: (page: number, pageSize: number) => void
  onDeleteAccount: (accountId: number) => void
  onEditAccount: (account: ArticleDistributionAccount) => void
  onResetFilters: (page: number, pageSize: number) => void
  onToggleAccountActive: (account: ArticleDistributionAccount) => void
}) {
  return (
    <aside className="article-side">
      <Flex vertical gap={18}>
        <Flex gap={12}>
          <Statistic title="待发布" value={unreadCount} />
          <Statistic title="已发布" value={publishedCount} />
          <Statistic title="文档失效" value={invalidCount} />
        </Flex>

        <Form form={filterForm} layout="vertical">
          <Form.Item label="账号" name="account_id">
            <Select allowClear placeholder="全部账号" options={accountOptions} />
          </Form.Item>
          <Form.Item label="发布类型" name="publication_type">
            <Select allowClear placeholder="全部类型" options={publicationTypeOptions} />
          </Form.Item>
          <Form.Item label="发布状态" name="publish_status">
            <Select allowClear placeholder="全部状态" options={publishStatusOptions} />
          </Form.Item>
          <Form.Item label="日期" name="date_range">
            <DatePicker.RangePicker style={{ width: '100%' }} />
          </Form.Item>
          <Space>
            <Button type="primary" onClick={() => onApplyFilters(1, articlePageSize)}>筛选</Button>
            <Button onClick={() => onResetFilters(1, articlePageSize)}>重置</Button>
          </Space>
        </Form>

        <div>
          <Typography.Text strong>账号</Typography.Text>
          <Flex vertical gap={8} style={{ marginTop: 10 }}>
            {accounts.map((account) => (
              <div key={account.id} className="article-list-item">
                <Flex justify="space-between" gap={8} align="start">
                  <div>
                    <Typography.Text strong>{account.account_name}</Typography.Text>
                    <div>
                      <Typography.Text type="secondary">
                        {account.platform} · {publicationTypeText[account.publication_type]}
                      </Typography.Text>
                      {inactiveAccountTag(account.is_active)}
                    </div>
                    {isAdmin && <Typography.Text type="secondary">用户 {account.user_id}</Typography.Text>}
                  </div>
                  <Space size={4}>
                    <Button size="small" onClick={() => onToggleAccountActive(account)}>
                      {account.is_active ? '停用' : '启用'}
                    </Button>
                    <Button size="small" icon={<EditOutlined />} onClick={() => onEditAccount(account)} />
                    <Popconfirm title="删除这个账号？已有文章的账号请停用。" onConfirm={() => onDeleteAccount(account.id)}>
                      <Button size="small" danger icon={<DeleteOutlined />} />
                    </Popconfirm>
                  </Space>
                </Flex>
              </div>
            ))}
          </Flex>
        </div>
      </Flex>
    </aside>
  )
}
