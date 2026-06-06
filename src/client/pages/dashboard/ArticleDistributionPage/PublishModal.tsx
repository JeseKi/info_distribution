import { Form, Input, Modal } from 'antd'
import type { FormInstance } from 'antd'

export function PublishModal({
  form,
  open,
  onCancel,
  onSubmit,
}: {
  form: FormInstance<{ published_url: string }>
  open: boolean
  onCancel: () => void
  onSubmit: (values: { published_url: string }) => void
}) {
  return (
    <Modal
      title="填写发布地址"
      open={open}
      onCancel={onCancel}
      onOk={() => form.submit()}
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={onSubmit}>
        <Form.Item
          label="发布地址"
          name="published_url"
          rules={[
            { required: true, message: '请输入发布地址' },
            { type: 'url', message: '请输入有效 URL' },
          ]}
        >
          <Input placeholder="https://..." />
        </Form.Item>
      </Form>
    </Modal>
  )
}
