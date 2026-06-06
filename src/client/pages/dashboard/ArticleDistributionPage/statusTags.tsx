import { Tag } from 'antd'
import type { ArticlePublishStatus } from '../../../lib/types'

export function publishStatusTag(status: ArticlePublishStatus) {
  if (status === 'published') return <Tag color="green">已发布</Tag>
  if (status === 'invalid') return <Tag color="red">文档失效</Tag>
  return <Tag>未发布</Tag>
}

export function inactiveAccountTag(isActive?: boolean) {
  return isActive === false ? <Tag color="red">已停用</Tag> : null
}
