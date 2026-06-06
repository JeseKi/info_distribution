import { Form, Input, Modal, Select, Switch } from 'antd'
import type { FormInstance } from 'antd'
import type { ArticleDistributionAccount } from '../../../lib/types'
import { publicationTypeOptions } from './constants'
import type { AccountFormValues } from './types'

export function AccountModal({
  editingAccount,
  form,
  isAdmin,
  open,
  onCancel,
  onSubmit,
}: {
  editingAccount: ArticleDistributionAccount | null
  form: FormInstance<AccountFormValues>
  isAdmin: boolean
  open: boolean
  onCancel: () => void
  onSubmit: (values: AccountFormValues) => void
}) {
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
            <Input type="number" placeholder="留空则使用当前管理员" />
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
        <Form.Item label="状态" name="is_active" valuePropName="checked">
          <Switch checkedChildren="启用" unCheckedChildren="停用" />
        </Form.Item>
      </Form>
    </Modal>
  )
}
