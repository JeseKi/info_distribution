import { App, Button, Card, Flex, Form, Input, Modal, Select, Space, Switch, Table, Tag, Typography } from 'antd'
import type { TableColumnsType } from 'antd'
import { EditOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  createProject,
  createTheme,
  listProjects,
  listThemes,
  updateProject,
  updateTheme,
} from '../../lib/admin'
import type { Project, ProjectPayload, Theme, ThemePayload } from '../../lib/types'
import { useAuth } from '../../hooks/useAuth'
import DangerousActionTwoFactorModal from '../../components/auth/DangerousActionTwoFactorModal'
import { resolveApiErrorMessage } from '../../lib/error'

type ProjectFormValues = {
  name: string
  code?: string
  is_active: boolean
  theme_ids: number[]
}

type ThemeFormValues = {
  name: string
  is_active: boolean
  project_ids: number[]
}

type PendingTwoFactor = {
  title: string
  description: string
  action: (code?: string) => Promise<void>
}

export default function ProjectThemeManagementPage() {
  const { message } = App.useApp()
  const { user } = useAuth()
  const [projectForm] = Form.useForm<ProjectFormValues>()
  const [themeForm] = Form.useForm<ThemeFormValues>()
  const [projects, setProjects] = useState<Project[]>([])
  const [themes, setThemes] = useState<Theme[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [editingTheme, setEditingTheme] = useState<Theme | null>(null)
  const [projectModalOpen, setProjectModalOpen] = useState(false)
  const [themeModalOpen, setThemeModalOpen] = useState(false)
  const [pendingTwoFactor, setPendingTwoFactor] = useState<PendingTwoFactor | null>(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [projectData, themeData] = await Promise.all([listProjects(), listThemes()])
      setProjects(projectData)
      setThemes(themeData)
    } catch (error) {
      message.error(resolveApiErrorMessage(error, '项目主题加载失败'))
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const themeOptions = useMemo(
    () => themes.map((theme) => ({
      label: theme.is_active ? theme.name : `${theme.name}（停用）`,
      value: theme.id,
    })),
    [themes],
  )

  const projectOptions = useMemo(
    () => projects.map((project) => ({
      label: project.is_active ? project.name : `${project.name}（停用）`,
      value: project.id,
    })),
    [projects],
  )

  const runWrite = async (title: string, description: string, action: (code?: string) => Promise<void>) => {
    if (user?.two_factor_enabled) {
      setPendingTwoFactor({ title, description, action })
      return
    }
    await action()
  }

  const openCreateProject = () => {
    setEditingProject(null)
    projectForm.setFieldsValue({ name: '', code: '', is_active: true, theme_ids: [] })
    setProjectModalOpen(true)
  }

  const openEditProject = (project: Project) => {
    setEditingProject(project)
    projectForm.setFieldsValue({
      name: project.name,
      code: project.code,
      is_active: project.is_active,
      theme_ids: project.theme_ids,
    })
    setProjectModalOpen(true)
  }

  const openCreateTheme = () => {
    setEditingTheme(null)
    themeForm.setFieldsValue({ name: '', is_active: true, project_ids: [] })
    setThemeModalOpen(true)
  }

  const openEditTheme = (theme: Theme) => {
    setEditingTheme(theme)
    themeForm.setFieldsValue({
      name: theme.name,
      is_active: theme.is_active,
      project_ids: theme.project_ids,
    })
    setThemeModalOpen(true)
  }

  const submitProject = async () => {
    const values = await projectForm.validateFields()
    const payload: ProjectPayload = {
      name: values.name.trim(),
      code: values.code?.trim() ? values.code.trim().toUpperCase() : null,
      is_active: values.is_active,
      theme_ids: values.theme_ids ?? [],
    }
    await runWrite(
      editingProject ? '二步验证后保存项目' : '二步验证后创建项目',
      '管理员项目写操作需要二步验证。',
      async (twoFactorCode?: string) => {
        setSaving(true)
        try {
          if (editingProject) {
            await updateProject(editingProject.id, payload, twoFactorCode)
            message.success('项目已更新')
          } else {
            await createProject(payload, twoFactorCode)
            message.success('项目已创建')
          }
          setProjectModalOpen(false)
          setPendingTwoFactor(null)
          await loadData()
        } catch (error) {
          message.error(resolveApiErrorMessage(error, '项目保存失败'))
        } finally {
          setSaving(false)
        }
      },
    )
  }

  const submitTheme = async () => {
    const values = await themeForm.validateFields()
    const payload: ThemePayload = {
      name: values.name.trim(),
      is_active: values.is_active,
      project_ids: values.project_ids ?? [],
    }
    await runWrite(
      editingTheme ? '二步验证后保存主题' : '二步验证后创建主题',
      '管理员主题写操作需要二步验证。',
      async (twoFactorCode?: string) => {
        setSaving(true)
        try {
          if (editingTheme) {
            await updateTheme(editingTheme.id, payload, twoFactorCode)
            message.success('主题已更新')
          } else {
            await createTheme(payload, twoFactorCode)
            message.success('主题已创建')
          }
          setThemeModalOpen(false)
          setPendingTwoFactor(null)
          await loadData()
        } catch (error) {
          message.error(resolveApiErrorMessage(error, '主题保存失败'))
        } finally {
          setSaving(false)
        }
      },
    )
  }

  const projectColumns: TableColumnsType<Project> = [
    { title: '项目', dataIndex: 'name', key: 'name', render: (value) => <Typography.Text strong>{value}</Typography.Text> },
    { title: '项目码', dataIndex: 'code', key: 'code', render: (value) => <Tag color="blue">{value}</Tag> },
    {
      title: '主题',
      dataIndex: 'themes',
      key: 'themes',
      render: (_, record) => (
        <Space wrap size={4}>
          {record.themes.length ? record.themes.map((theme) => <Tag key={theme.id}>{theme.name}</Tag>) : '-'}
        </Space>
      ),
    },
    { title: '状态', dataIndex: 'is_active', key: 'is_active', render: (value) => value ? <Tag color="green">启用</Tag> : <Tag>停用</Tag> },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => <Button size="small" icon={<EditOutlined />} onClick={() => openEditProject(record)}>编辑</Button>,
    },
  ]

  const themeColumns: TableColumnsType<Theme> = [
    { title: '主题', dataIndex: 'name', key: 'name', render: (value) => <Typography.Text strong>{value}</Typography.Text> },
    {
      title: '项目',
      dataIndex: 'project_ids',
      key: 'project_ids',
      render: (_, record) => (
        <Space wrap size={4}>
          {record.project_ids.length
            ? record.project_ids.map((projectId) => {
                const project = projects.find((item) => item.id === projectId)
                return <Tag key={projectId}>{project?.name ?? `#${projectId}`}</Tag>
              })
            : '-'}
        </Space>
      ),
    },
    { title: '状态', dataIndex: 'is_active', key: 'is_active', render: (value) => value ? <Tag color="green">启用</Tag> : <Tag>停用</Tag> },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => <Button size="small" icon={<EditOutlined />} onClick={() => openEditTheme(record)}>编辑</Button>,
    },
  ]

  return (
    <Flex vertical gap={24}>
      <Card>
        <Flex justify="space-between" align="center" wrap="wrap" gap={12}>
          <div>
            <Typography.Title level={4} style={{ margin: 0 }}>项目主题</Typography.Title>
            <Typography.Text type="secondary">管理注册项目码、项目可用主题，以及启停状态。</Typography.Text>
          </div>
          <Button icon={<ReloadOutlined />} loading={loading} onClick={() => void loadData()}>刷新</Button>
        </Flex>
      </Card>

      <Card
        title="项目"
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreateProject}>新建项目</Button>}
      >
        <Table rowKey="id" loading={loading} columns={projectColumns} dataSource={projects} pagination={false} scroll={{ x: 'max-content' }} />
      </Card>

      <Card
        title="主题"
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreateTheme}>新建主题</Button>}
      >
        <Table rowKey="id" loading={loading} columns={themeColumns} dataSource={themes} pagination={false} scroll={{ x: 'max-content' }} />
      </Card>

      <Modal
        title={editingProject ? '编辑项目' : '新建项目'}
        open={projectModalOpen}
        onCancel={() => setProjectModalOpen(false)}
        onOk={() => void submitProject()}
        confirmLoading={saving}
        destroyOnClose
      >
        <Form form={projectForm} layout="vertical" requiredMark={false}>
          <Form.Item label="项目名称" name="name" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="例如 AIFC" />
          </Form.Item>
          <Form.Item
            label="项目码"
            name="code"
            normalize={(value: string | undefined) => value?.toUpperCase()}
            rules={[
              { len: 8, message: '项目码必须是 8 位大写字母' },
              { pattern: /^[A-Z]{8}$/, message: '项目码只能包含大写字母' },
            ]}
          >
            <Input maxLength={8} placeholder="留空自动生成" />
          </Form.Item>
          <Form.Item label="关联主题" name="theme_ids">
            <Select mode="multiple" options={themeOptions} optionFilterProp="label" placeholder="请选择主题" />
          </Form.Item>
          <Form.Item label="状态" name="is_active" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="停用" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={editingTheme ? '编辑主题' : '新建主题'}
        open={themeModalOpen}
        onCancel={() => setThemeModalOpen(false)}
        onOk={() => void submitTheme()}
        confirmLoading={saving}
        destroyOnClose
      >
        <Form form={themeForm} layout="vertical" requiredMark={false}>
          <Form.Item label="主题名称" name="name" rules={[{ required: true, message: '请输入主题名称' }]}>
            <Input placeholder="例如 AI" />
          </Form.Item>
          <Form.Item label="关联项目" name="project_ids">
            <Select mode="multiple" options={projectOptions} optionFilterProp="label" placeholder="请选择项目" />
          </Form.Item>
          <Form.Item label="状态" name="is_active" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="停用" />
          </Form.Item>
        </Form>
      </Modal>

      <DangerousActionTwoFactorModal
        open={Boolean(pendingTwoFactor)}
        title={pendingTwoFactor?.title ?? '二步验证'}
        description={pendingTwoFactor?.description ?? ''}
        loading={saving}
        onCancel={() => setPendingTwoFactor(null)}
        onConfirm={async (code) => {
          await pendingTwoFactor?.action(code)
        }}
      />
    </Flex>
  )
}
