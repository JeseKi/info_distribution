import { useCallback, useEffect, useState } from 'react'
import {
  App,
  Button,
  Card,
  Empty,
  Flex,
  Form,
  Input,
  InputNumber,
  Pagination,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { TableColumnsType } from 'antd'
import { DeleteOutlined, EditOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useAuth } from '../../hooks/useAuth'
import * as articleApi from '../../lib/articleDistribution'
import { resolveApiErrorMessage } from '../../lib/error'
import type {
  ArticleDistributionAccount,
  ArticleDistributionAccountPageParams,
  ArticlePublicationType,
} from '../../lib/types'
import { AccountModal } from './ArticleDistributionPage/AccountModal'
import { publicationTypeOptions, publicationTypeText } from './ArticleDistributionPage/constants'
import { normalizeAccountPayload } from './ArticleDistributionPage/normalize'
import type { AccountFormValues } from './ArticleDistributionPage/types'

const defaultPageSize = 10

const accountStatusOptions = [
  { label: '启用', value: true },
  { label: '停用', value: false },
]

interface FilterValues {
  keyword?: string
  user_id?: number
  platform?: string
  publication_type?: ArticlePublicationType
  is_active?: boolean
}

export default function ArticleDistributionAccountsPage() {
  const { message } = App.useApp()
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const [filterForm] = Form.useForm<FilterValues>()
  const [accountForm] = Form.useForm<AccountFormValues>()
  const [items, setItems] = useState<ArticleDistributionAccount[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(defaultPageSize)
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingAccount, setEditingAccount] = useState<ArticleDistributionAccount | null>(null)

  const buildParams = useCallback((): ArticleDistributionAccountPageParams => {
    const values = filterForm.getFieldsValue()
    return {
      keyword: normalizeOptional(values.keyword),
      user_id: isAdmin ? values.user_id : undefined,
      platform: normalizeOptional(values.platform),
      publication_type: values.publication_type,
      is_active: values.is_active,
    }
  }, [filterForm, isAdmin])

  const loadData = useCallback(async (
    filters?: ArticleDistributionAccountPageParams,
    pagination: { page: number; pageSize: number } = { page: 1, pageSize: defaultPageSize },
  ) => {
    setLoading(true)
    try {
      const nextPage = await articleApi.listArticleAccountsPage({
        ...filters,
        page: pagination.page,
        page_size: pagination.pageSize,
      })
      setItems(nextPage.items)
      setTotal(nextPage.total)
      setPage(nextPage.page)
      setPageSize(nextPage.page_size)
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '账户列表加载失败'))
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    void loadData(undefined, { page: 1, pageSize: defaultPageSize })
  }, [loadData])

  const reloadCurrentPage = () => loadData(buildParams(), { page, pageSize })

  const openCreateModal = () => {
    setEditingAccount(null)
    accountForm.resetFields()
    accountForm.setFieldsValue({ is_active: true })
    setModalOpen(true)
  }

  const openEditModal = (account: ArticleDistributionAccount) => {
    setEditingAccount(account)
    accountForm.setFieldsValue(account)
    setModalOpen(true)
  }

  const handleAccountSubmit = async (values: AccountFormValues) => {
    try {
      if (editingAccount) {
        await articleApi.updateArticleAccount(editingAccount.id, normalizeAccountPayload(values))
        message.success('账号已更新')
        await reloadCurrentPage()
      } else {
        await articleApi.createArticleAccount(normalizeAccountPayload(values))
        message.success('账号已创建')
        await loadData(buildParams(), { page: 1, pageSize })
      }
      setModalOpen(false)
      setEditingAccount(null)
      accountForm.resetFields()
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '账号保存失败'))
    }
  }

  const handleToggleAccountActive = async (account: ArticleDistributionAccount) => {
    try {
      await articleApi.updateArticleAccount(account.id, { is_active: !account.is_active })
      message.success(account.is_active ? '账号已停用' : '账号已启用')
      await reloadCurrentPage()
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '账号状态更新失败'))
    }
  }

  const handleDeleteAccount = async (account: ArticleDistributionAccount) => {
    try {
      await articleApi.deleteArticleAccount(account.id)
      message.success('账号已删除')
      await loadData(buildParams(), {
        page: items.length === 1 && page > 1 ? page - 1 : page,
        pageSize,
      })
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '账号删除失败'))
    }
  }

  const columns: TableColumnsType<ArticleDistributionAccount> = [
    {
      title: '账号名称',
      dataIndex: 'account_name',
      key: 'account_name',
      width: 220,
      render: (value: string) => <Typography.Text strong>{value}</Typography.Text>,
    },
    {
      title: '平台',
      dataIndex: 'platform',
      key: 'platform',
      width: 160,
    },
    {
      title: '发布类型',
      dataIndex: 'publication_type',
      key: 'publication_type',
      width: 120,
      render: (value: ArticlePublicationType) => publicationTypeText[value],
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (value: boolean) => value ? <Tag color="green">启用</Tag> : <Tag color="red">停用</Tag>,
    },
    {
      title: '归属用户',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 120,
      render: (value: number) => `用户 ${value}`,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (value: string) => dayjs(value).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 180,
      render: (value: string) => dayjs(value).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right',
      width: 220,
      render: (_, record) => (
        <Space size={4}>
          <Button size="small" onClick={() => void handleToggleAccountActive(record)}>
            {record.is_active ? '停用' : '启用'}
          </Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEditModal(record)}>
            编辑
          </Button>
          <Popconfirm
            title="删除这个账号？"
            description="已有文章的账号请停用。"
            onConfirm={() => void handleDeleteAccount(record)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <Flex vertical gap={18}>
      <Flex align="center" justify="space-between" gap={16} wrap="wrap">
        <div>
          <Typography.Title level={2} style={{ margin: 0 }}>
            分发账户
          </Typography.Title>
          <Typography.Text type="secondary">
            管理文章分发使用的平台账号和发布类型。
          </Typography.Text>
        </div>
        <Space wrap>
          <Button icon={<ReloadOutlined />} loading={loading} onClick={() => void reloadCurrentPage()}>
            刷新
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
            新建账号
          </Button>
        </Space>
      </Flex>

      <Card>
        <Form form={filterForm} layout="inline" style={{ marginBottom: 16 }}>
          <Form.Item label="关键词" name="keyword">
            <Input allowClear placeholder="账号或平台" style={{ width: 180 }} />
          </Form.Item>
          {isAdmin && (
            <Form.Item label="用户 ID" name="user_id">
              <InputNumber min={1} precision={0} placeholder="全部用户" style={{ width: 140 }} />
            </Form.Item>
          )}
          <Form.Item label="平台" name="platform">
            <Input allowClear placeholder="全部平台" style={{ width: 160 }} />
          </Form.Item>
          <Form.Item label="发布类型" name="publication_type">
            <Select allowClear placeholder="全部类型" options={publicationTypeOptions} style={{ width: 140 }} />
          </Form.Item>
          <Form.Item label="状态" name="is_active">
            <Select allowClear placeholder="全部状态" options={accountStatusOptions} style={{ width: 130 }} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" onClick={() => void loadData(buildParams(), { page: 1, pageSize })}>
                筛选
              </Button>
              <Button onClick={() => {
                filterForm.resetFields()
                void loadData(undefined, { page: 1, pageSize })
              }}>
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>

        <Table
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={items}
          pagination={false}
          scroll={{ x: 1280 }}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无账号" /> }}
        />
        {total > 0 && (
          <Pagination
            current={page}
            pageSize={pageSize}
            total={total}
            showSizeChanger
            pageSizeOptions={[10, 20, 50]}
            style={{ marginTop: 16, textAlign: 'right' }}
            onChange={(nextPage, nextPageSize) => void loadData(buildParams(), {
              page: nextPage,
              pageSize: nextPageSize,
            })}
          />
        )}
      </Card>

      <AccountModal
        editingAccount={editingAccount}
        form={accountForm}
        isAdmin={isAdmin}
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false)
          setEditingAccount(null)
        }}
        onSubmit={(values) => void handleAccountSubmit(values)}
      />
    </Flex>
  )
}

function normalizeOptional(value: string | undefined): string | undefined {
  const normalized = value?.trim()
  return normalized || undefined
}
