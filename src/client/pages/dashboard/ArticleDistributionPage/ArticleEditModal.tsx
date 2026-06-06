import { DatePicker, Form, Input, Modal, Select } from 'antd'
import type { FormInstance } from 'antd'
import type { AccountSelectOption, ArticleEditFormValues } from './types'

export function ArticleEditModal({
  accountOptions,
  form,
  open,
  onCancel,
  onSubmit,
}: {
  accountOptions: AccountSelectOption[]
  form: FormInstance<ArticleEditFormValues>
  open: boolean
  onCancel: () => void
  onSubmit: (values: ArticleEditFormValues) => void
}) {
  return (
    <Modal
      title="编辑文章"
      open={open}
      onCancel={onCancel}
      onOk={() => form.submit()}
      width={820}
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={onSubmit}>
        <Form.Item label="账号" name="account_id" rules={[{ required: true, message: '请选择账号' }]}>
          <Select options={accountOptions} />
        </Form.Item>
        <Form.Item label="标题" name="title" rules={[{ required: true, message: '请输入标题' }]}>
          <Input />
        </Form.Item>
        <Form.Item label="发布日期" name="scheduled_date" rules={[{ required: true, message: '请选择发布日期' }]}>
          <DatePicker />
        </Form.Item>
        <Form.Item label="Markdown" name="markdown_content" rules={[{ required: true, message: '请输入 Markdown' }]}>
          <Input.TextArea rows={14} />
        </Form.Item>
      </Form>
    </Modal>
  )
}
