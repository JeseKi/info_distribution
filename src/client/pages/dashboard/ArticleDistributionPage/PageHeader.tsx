import { Button, Flex, Space, Typography } from 'antd'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons'

export function PageHeader({
  loading,
  onCreateAccount,
  onRefresh,
}: {
  loading: boolean
  onCreateAccount: () => void
  onRefresh: () => void
}) {
  return (
    <Flex align="center" justify="space-between" gap={16} wrap="wrap">
      <div>
        <Typography.Title level={2} style={{ margin: 0 }}>
          文章分发
        </Typography.Title>
        <Typography.Text type="secondary">
          按账号、日期和发布状态管理待分发内容。
        </Typography.Text>
      </div>
      <Space wrap>
        <Button icon={<ReloadOutlined />} loading={loading} onClick={onRefresh}>
          刷新
        </Button>
        <Button type="primary" icon={<PlusOutlined />} onClick={onCreateAccount}>
          新建账号
        </Button>
      </Space>
    </Flex>
  )
}
