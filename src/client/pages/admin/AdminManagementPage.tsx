import { ApiOutlined, AppstoreOutlined, FileTextOutlined, KeyOutlined, LockOutlined, TeamOutlined } from '@ant-design/icons'
import { Tabs } from 'antd'
import UserManagementPage from './UserManagementPage'
import PermissionManagementPage from './PermissionManagementPage'
import ScopeManagementPage from './ScopeManagementPage'
import OAuthClientManagementPage from './OAuthClientManagementPage'
import ArticleDistributionAdminPage from './ArticleDistributionAdminPage'
import ProjectThemeManagementPage from './ProjectThemeManagementPage'

const tabItems = [
  {
    key: 'users',
    label: (
      <span>
        <TeamOutlined />
        用户管理
      </span>
    ),
    children: <UserManagementPage />,
  },
  {
    key: 'projects-themes',
    label: (
      <span>
        <AppstoreOutlined />
        项目主题
      </span>
    ),
    children: <ProjectThemeManagementPage />,
  },
  {
    key: 'scopes',
    label: (
      <span>
        <LockOutlined />
        Scope 管理
      </span>
    ),
    children: <ScopeManagementPage />,
  },
  {
    key: 'permissions',
    label: (
      <span>
        <KeyOutlined />
        权限管理
      </span>
    ),
    children: <PermissionManagementPage />,
  },
  {
    key: 'oauth-clients',
    label: (
      <span>
        <ApiOutlined />
        OAuth Clients
      </span>
    ),
    children: <OAuthClientManagementPage />,
  },
  {
    key: 'article-distribution',
    label: (
      <span>
        <FileTextOutlined />
        文章分发
      </span>
    ),
    children: <ArticleDistributionAdminPage />,
  },
]

export default function AdminManagementPage() {
  return (
    <div style={{ overflowX: 'auto' }}>
      <Tabs defaultActiveKey="users" items={tabItems} style={{ minWidth: 500 }} />
    </div>
  )
}
