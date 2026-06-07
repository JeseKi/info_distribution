import { Form, Input, InputNumber, Modal, Select, Switch } from 'antd'
import type { FormInstance } from 'antd'
import { useEffect } from 'react'
import type { AccountOptions, ArticleDistributionAccount } from '../../../lib/types'
import { publicationTypeOptions } from './constants'
import type { AccountFormValues } from './types'

export function AccountModal({
  editingAccount,
  form,
  isAdmin,
  accountOptions,
  accountOptionsLoading,
  open,
  onTargetUserChange,
  onCancel,
  onSubmit,
}: {
  editingAccount: ArticleDistributionAccount | null
  form: FormInstance<AccountFormValues>
  isAdmin: boolean
  accountOptions: AccountOptions
  accountOptionsLoading: boolean
  open: boolean
  onTargetUserChange: (userId?: number) => void
  onCancel: () => void
  onSubmit: (values: AccountFormValues) => void
}) {
  const watchedUserId = Form.useWatch('user_id', form)

  useEffect(() => {
    if (!open || !isAdmin) {
      return
    }
    const numericUserId = watchedUserId ? Number(watchedUserId) : undefined
    onTargetUserChange(Number.isFinite(numericUserId) ? numericUserId : undefined)
  }, [isAdmin, onTargetUserChange, open, watchedUserId])

  return (
    <Modal
      title={editingAccount ? '编辑账号' : '新建账号'}
      open={open}
      onCancel={onCancel}
      onOk={() => form.submit()}
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={onSubmit}>
        {isAdmin && (
          <Form.Item label="用户 ID" name="user_id">
            <InputNumber min={1} precision={0} placeholder="留空则使用当前管理员" style={{ width: '100%' }} />
          </Form.Item>
        )}
        <Form.Item label="平台" name="platform" rules={[{ required: true, message: '请输入平台' }]}>
          <Input placeholder="知乎、公众号、小红书等" />
        </Form.Item>
        <Form.Item label="账号名称" name="account_name" rules={[{ required: true, message: '请输入账号名称' }]}>
          <Input />
        </Form.Item>
        <Form.Item label="发布类型" name="publication_type" rules={[{ required: true, message: '请选择发布类型' }]}>
          <Select options={publicationTypeOptions} />
        </Form.Item>
        <Form.Item label="主题" name="theme_id" rules={[{ required: true, message: '请选择主题' }]}>
          <Select
            loading={accountOptionsLoading}
            options={accountOptions.themes.map((theme) => ({
              label: theme.is_active ? theme.name : `${theme.name}（停用）`,
              value: theme.id,
            }))}
            optionFilterProp="label"
            placeholder="请选择主题"
          />
        </Form.Item>
        <Form.Item label="状态" name="is_active" valuePropName="checked">
          <Switch checkedChildren="启用" unCheckedChildren="停用" />
        </Form.Item>
      </Form>
    </Modal>
  )
}
