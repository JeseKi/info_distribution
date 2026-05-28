import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  App,
  Button,
  Card,
  DatePicker,
  Flex,
  Form,
  Input,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { TableColumnsType } from 'antd'
import { DownloadOutlined, KeyOutlined, PlusOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { listUsers } from '../../lib/admin'
import * as articleApi from '../../lib/articleDistribution'
import type {
  AdminUser,
  ArticleDistributionAccount,
  ArticleDistributionAccountStatusFilter,
  ArticleDistributionApiKey,
  ArticleDistributionArticleBatchPayload,
  ArticleDistributionPublicityRecordExportParams,
  ArticlePublicationType,
} from '../../lib/types'

function inactiveAccountTag(isActive?: boolean) {
  return isActive === false ? <Tag color="red">已停用</Tag> : null
}

const publicationTypeOptions = [
  { label: '视频', value: 'video' },
  { label: '文章', value: 'article' },
  { label: '图文', value: 'image_text' },
]

const accountStatusOptions = [
  { label: '全部', value: 'all' },
  { label: '启用', value: 'active' },
  { label: '停用', value: 'inactive' },
]

interface UploadFormValues {
  user_id: number
  account_id: number
  articles: Array<{
    title: string
    scheduled_date: dayjs.Dayjs
    markdown_content: string
  }>
}

interface CsvExportFormValues {
  scheduled_from?: dayjs.Dayjs
  scheduled_to?: dayjs.Dayjs
  platform?: string
  publication_type?: ArticlePublicationType
  account_status?: ArticleDistributionAccountStatusFilter
}

export default function ArticleDistributionAdminPage() {
  const { message, modal } = App.useApp()
  const [users, setUsers] = useState<AdminUser[]>([])
  const [accounts, setAccounts] = useState<ArticleDistributionAccount[]>([])
  const [apiKeys, setApiKeys] = useState<ArticleDistributionApiKey[]>([])
  const [loading, setLoading] = useState(false)
  const [exportingCsv, setExportingCsv] = useState(false)
  const [selectedUserId, setSelectedUserId] = useState<number | undefined>()
  const [uploadForm] = Form.useForm<UploadFormValues>()
  const [keyForm] = Form.useForm<{ name: string }>()
  const [csvExportForm] = Form.useForm<CsvExportFormValues>()

  const userOptions = useMemo(
    () => users.map((user) => ({ label: `${user.username} (${user.id})`, value: user.id })),
    [users],
  )

  const accountOptions = useMemo(
    () => accounts.map((account) => ({
      label: (
        <Space size={4}>
          <span>{account.platform} / {account.account_name} / {account.publication_type}</span>
          {inactiveAccountTag(account.is_active)}
        </Space>
      ),
      value: account.id,
      disabled: !account.is_active,
    })),
    [accounts],
  )

  const loadInitialData = useCallback(async () => {
    setLoading(true)
    try {
      const [nextUsers, nextKeys] = await Promise.all([
        listUsers(),
        articleApi.listArticleApiKeys(),
      ])
      setUsers(nextUsers)
      setApiKeys(nextKeys)
    } catch (error) {
      message.error(resolveErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }, [message])

  const loadAccounts = useCallback(async (userId: number) => {
    try {
      setAccounts(await articleApi.listArticleAccounts({ user_id: userId }))
    } catch (error) {
      message.error(resolveErrorMessage(error))
    }
  }, [message])

  useEffect(() => {
    void loadInitialData()
  }, [loadInitialData])

  const handleCreateApiKey = async ({ name }: { name: string }) => {
    try {
      const created = await articleApi.createArticleApiKey({ name })
      await loadInitialData()
      keyForm.resetFields()
      modal.info({
        title: 'API Key 已创建',
        content: (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Alert type="warning" showIcon message="明文 Key 只会显示一次。" />
            <Typography.Text copyable={{ text: created.api_key }} code style={{ wordBreak: 'break-all' }}>
              {created.api_key}
            </Typography.Text>
          </Space>
        ),
      })
    } catch (error) {
      message.error(resolveErrorMessage(error))
    }
  }

  const handleRevokeApiKey = async (apiKeyId: number) => {
    try {
      await articleApi.revokeArticleApiKey(apiKeyId)
      message.success('API Key 已吊销')
      await loadInitialData()
    } catch (error) {
      message.error(resolveErrorMessage(error))
    }
  }

  const handleUploadArticles = async (values: UploadFormValues) => {
    const payload: ArticleDistributionArticleBatchPayload = {
      account_id: values.account_id,
      articles: values.articles.map((article) => ({
        title: article.title,
        markdown_content: article.markdown_content,
        scheduled_date: article.scheduled_date.format('YYYY-MM-DD'),
      })),
    }
    try {
      const created = await articleApi.createAdminArticles(payload)
      message.success(`已上传 ${created.length} 篇文章`)
      uploadForm.resetFields()
    } catch (error) {
      message.error(resolveErrorMessage(error))
    }
  }

  const handleExportCsv = async () => {
    const values = csvExportForm.getFieldsValue()
    if (values.scheduled_from && values.scheduled_to && values.scheduled_from.isAfter(values.scheduled_to, 'day')) {
      message.error('起始日期不能晚于截止日期')
      return
    }
    const params: ArticleDistributionPublicityRecordExportParams = {
      scheduled_from: values.scheduled_from?.format('YYYY-MM-DD'),
      scheduled_to: (values.scheduled_to ?? dayjs()).format('YYYY-MM-DD'),
      platform: values.platform?.trim() || undefined,
      publication_type: values.publication_type,
      account_status: values.account_status ?? 'all',
    }
    setExportingCsv(true)
    try {
      await articleApi.downloadPublicityRecordsCsv(params)
      message.success('CSV 已开始下载')
    } catch (error) {
      message.error(resolveErrorMessage(error))
    } finally {
      setExportingCsv(false)
    }
  }

  const apiKeyColumns: TableColumnsType<ArticleDistributionApiKey> = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    {
      title: '前缀',
      dataIndex: 'key_prefix',
      key: 'key_prefix',
      render: (value: string) => <Typography.Text code>{value}</Typography.Text>,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (value: boolean) => value ? <Tag color="green">可用</Tag> : <Tag>已吊销</Tag>,
    },
    { title: '最近使用', dataIndex: 'last_used_at', key: 'last_used_at', render: (value: string | null) => value ?? '-' },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => record.is_active ? (
        <Popconfirm title="吊销这个 API Key？" onConfirm={() => void handleRevokeApiKey(record.id)}>
          <Button danger>吊销</Button>
        </Popconfirm>
      ) : null,
    },
  ]

  return (
    <Flex vertical gap={20}>
      <Card title="对外宣发记录">
        <Form
          form={csvExportForm}
          layout="vertical"
          initialValues={{ scheduled_to: dayjs(), account_status: 'all' }}
        >
          <Flex gap={16} wrap="wrap" align="end">
            <Form.Item label="起始日期" name="scheduled_from" style={{ minWidth: 180 }}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item label="截止日期" name="scheduled_to" style={{ minWidth: 180 }}>
              <DatePicker allowClear={false} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item label="平台" name="platform" style={{ minWidth: 180 }}>
              <Input allowClear placeholder="wechat、zhihu..." />
            </Form.Item>
            <Form.Item label="发布类型" name="publication_type" style={{ minWidth: 160 }}>
              <Select allowClear options={publicationTypeOptions} placeholder="全部类型" />
            </Form.Item>
            <Form.Item label="账号状态" name="account_status" style={{ minWidth: 140 }}>
              <Select options={accountStatusOptions} />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  loading={exportingCsv}
                  onClick={() => void handleExportCsv()}
                >
                  导出 CSV
                </Button>
                <Button
                  onClick={() => {
                    csvExportForm.resetFields()
                  }}
                >
                  重置
                </Button>
              </Space>
            </Form.Item>
          </Flex>
        </Form>
      </Card>

      <Card title="上传文章">
        <Form
          form={uploadForm}
          layout="vertical"
          initialValues={{ articles: [{ title: '', markdown_content: '' }] }}
          onFinish={(values) => void handleUploadArticles(values)}
        >
          <Flex gap={16} wrap="wrap">
            <Form.Item label="用户" name="user_id" rules={[{ required: true, message: '请选择用户' }]} style={{ minWidth: 240 }}>
              <Select
                showSearch
                options={userOptions}
                optionFilterProp="label"
                onChange={(userId: number) => {
                  setSelectedUserId(userId)
                  uploadForm.setFieldValue('account_id', undefined)
                  void loadAccounts(userId)
                }}
              />
            </Form.Item>
            <Form.Item label="账号" name="account_id" rules={[{ required: true, message: '请选择账号' }]} style={{ minWidth: 320 }}>
              <Select disabled={!selectedUserId} options={accountOptions} />
            </Form.Item>
          </Flex>

          <Form.List name="articles">
            {(fields, { add, remove }) => (
              <Flex vertical gap={16}>
                {fields.map((field, index) => (
                  <Card
                    key={field.key}
                    size="small"
                    title={`文章 ${index + 1}`}
                    extra={fields.length > 1 ? <Button danger onClick={() => remove(field.name)}>移除</Button> : null}
                  >
                    <Form.Item name={[field.name, 'title']} label="标题" rules={[{ required: true, message: '请输入标题' }]}>
                      <Input />
                    </Form.Item>
                    <Form.Item name={[field.name, 'scheduled_date']} label="发布日期" rules={[{ required: true, message: '请选择发布日期' }]}>
                      <DatePicker />
                    </Form.Item>
                    <Form.Item name={[field.name, 'markdown_content']} label="Markdown" rules={[{ required: true, message: '请输入 Markdown' }]}>
                      <Input.TextArea rows={8} />
                    </Form.Item>
                  </Card>
                ))}
                <Button icon={<PlusOutlined />} onClick={() => add({ title: '', markdown_content: '' })}>
                  添加文章
                </Button>
              </Flex>
            )}
          </Form.List>

          <Form.Item style={{ marginTop: 16 }}>
            <Button type="primary" htmlType="submit">上传</Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="API Key">
        <Form form={keyForm} layout="inline" onFinish={(values) => void handleCreateApiKey(values)} style={{ marginBottom: 16 }}>
          <Form.Item name="name" rules={[{ required: true, message: '请输入名称' }]}>
            <Input prefix={<KeyOutlined />} placeholder="名称" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" icon={<PlusOutlined />} htmlType="submit">创建</Button>
          </Form.Item>
        </Form>
        <Table rowKey="id" loading={loading} columns={apiKeyColumns} dataSource={apiKeys} />
      </Card>
    </Flex>
  )
}

function resolveErrorMessage(error: unknown): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: unknown } } }).response
    const detail = response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return '操作失败'
}
