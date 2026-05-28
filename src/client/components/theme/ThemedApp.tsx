import { App as AntdApp, ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from '../../App'
import { useThemeMode } from '../../hooks/useThemeMode'

export default function ThemedApp() {
  const { resolvedTheme } = useThemeMode()
  const isDark = resolvedTheme === 'dark'

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: isDark ? '#5aa7ff' : '#2f6fed',
          colorInfo: isDark ? '#5aa7ff' : '#2f6fed',
          borderRadius: 8,
          colorBgBase: isDark ? '#101419' : '#f7f9fb',
          colorBgLayout: isDark ? '#0d1117' : '#eef1f4',
          colorBgContainer: isDark ? '#151b22' : '#f8fafc',
          colorBgElevated: isDark ? '#171e26' : '#ffffff',
          colorBorder: isDark ? '#2b3540' : '#d7dde4',
          colorBorderSecondary: isDark ? '#232c36' : '#e3e8ee',
          colorFillAlter: isDark ? 'rgba(91, 113, 137, 0.14)' : 'rgba(84, 101, 120, 0.08)',
          colorTextBase: isDark ? '#dce5ef' : '#1d2630',
          colorTextSecondary: isDark ? '#98a6b5' : '#647282',
          fontFamily:
            "'Inter', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', system-ui, -apple-system, sans-serif",
        },
        components: {
          Button: {
            controlHeight: 40,
            fontWeight: 600,
            paddingInline: 16,
          },
          Layout: {
            headerBg: isDark ? '#121820' : '#f4f7fa',
            bodyBg: 'transparent',
            siderBg: isDark ? '#141a21' : '#f8fafc',
          },
          Card: {
            borderRadiusLG: 8,
            boxShadowTertiary: isDark
              ? '0 18px 48px rgba(0, 0, 0, 0.34)'
              : '0 16px 42px rgba(38, 50, 64, 0.1)',
          },
          Menu: {
            itemBg: 'transparent',
            itemSelectedBg: isDark ? 'rgba(90, 167, 255, 0.14)' : 'rgba(47, 111, 237, 0.1)',
            itemSelectedColor: isDark ? '#9cccff' : '#1f5ed8',
          },
          Table: {
            headerBg: isDark ? '#181f27' : '#f1f5f8',
            borderColor: isDark ? '#29333e' : '#dce2e8',
          },
        },
      }}
    >
      <AntdApp>
        <App />
      </AntdApp>
    </ConfigProvider>
  )
}
