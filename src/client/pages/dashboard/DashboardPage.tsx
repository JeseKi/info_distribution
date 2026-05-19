import { Button, Card, Flex, Space, Statistic, Typography } from 'antd'
import { CalendarOutlined, FileTextOutlined, SendOutlined } from '@ant-design/icons'
import { Link } from 'react-router-dom'

export default function DashboardPage() {
  return (
    <Flex vertical gap={20}>
      <Flex align="center" justify="space-between" gap={16} wrap="wrap">
        <div>
          <Typography.Title level={2} style={{ margin: 0 }}>
            内容分发工作台
          </Typography.Title>
          <Typography.Text type="secondary">
            管理账号、查看每日待发布文章，并完成发布状态回填。
          </Typography.Text>
        </div>
        <Link to="/article-distribution">
          <Button type="primary" icon={<FileTextOutlined />}>进入文章分发</Button>
        </Link>
      </Flex>

      <Flex gap={16} wrap="wrap">
        <Card style={{ flex: '1 1 220px' }}>
          <Statistic title="核心流程" value="账号 → 日期 → 文章" prefix={<SendOutlined />} />
        </Card>
        <Card style={{ flex: '1 1 220px' }}>
          <Statistic title="默认视图" value="阅读预览" prefix={<FileTextOutlined />} />
        </Card>
        <Card style={{ flex: '1 1 220px' }}>
          <Statistic title="发布节奏" value="每日多篇" prefix={<CalendarOutlined />} />
        </Card>
      </Flex>

      <Card>
        <Space direction="vertical" size={8}>
          <Typography.Title level={4} style={{ margin: 0 }}>
            当前可用能力
          </Typography.Title>
          <Typography.Text>
            普通用户可以维护自己的平台账号、按日期查看分配到账号的文章、阅读预览 Markdown 内容，并切换已发布/未发布状态。
          </Typography.Text>
          <Typography.Text type="secondary">
            管理员可以在后台上传文章、生成 API Key，并通过 v1 API 批量写入指定账号的文章队列。
          </Typography.Text>
        </Space>
      </Card>
    </Flex>
  )
}
