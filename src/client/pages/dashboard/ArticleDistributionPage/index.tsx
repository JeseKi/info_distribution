import { Flex } from 'antd'
import { AccountModal } from './AccountModal'
import { ArticleEditModal } from './ArticleEditModal'
import { ArticleListPanel } from './ArticleListPanel'
import { ArticlePreviewPanel } from './ArticlePreviewPanel'
import { PageHeader } from './PageHeader'
import { PublishModal } from './PublishModal'
import { Sidebar } from './Sidebar'
import { useArticleDistributionController } from './useArticleDistributionController'

export default function ArticleDistributionPage() {
  const state = useArticleDistributionController()

  return (
    <Flex vertical gap={18} className="article-workspace">
      <PageHeader
        loading={state.loading}
        onCreateAccount={state.handleCreateAccount}
        onRefresh={() => void state.reloadCurrentPage()}
      />

      <div className="article-shell">
        <Sidebar
          accounts={state.accounts}
          accountOptions={state.accountOptions}
          articlePageSize={state.articlePageSize}
          filterForm={state.filterForm}
          invalidCount={state.articleStatusCounts.invalid}
          isAdmin={state.isAdmin}
          publishedCount={state.articleStatusCounts.published}
          unreadCount={state.articleStatusCounts.unpublished}
          onApplyFilters={(page, pageSize) => void state.loadData(state.buildFilters(), { page, pageSize })}
          onDeleteAccount={(accountId) => void state.handleDeleteAccount(accountId)}
          onEditAccount={state.handleEditAccount}
          onResetFilters={state.handleResetFilters}
          onToggleAccountActive={(account) => void state.handleToggleAccountActive(account)}
        />
        <ArticleListPanel
          articles={state.articles}
          articlePage={state.articlePage}
          articlePageSize={state.articlePageSize}
          articleTotal={state.articleTotal}
          selectedArticle={state.selectedArticle}
          onPageChange={(page, pageSize) => void state.loadData(state.buildFilters(), { page, pageSize })}
          onSelectArticle={state.setSelectedArticleId}
        />
        <ArticlePreviewPanel
          copyMenuOpen={state.copyMenuOpen}
          downloadingImages={state.downloadingImages}
          imagePackageProgress={state.imagePackageProgress}
          isAdmin={state.isAdmin}
          selectedArticle={state.selectedArticle}
          onCopyAction={(type) => void state.copyAction(type)}
          onCopyMenuOpenChange={state.setCopyMenuOpen}
          onDeleteArticle={(article) => void state.handleDeleteArticle(article)}
          onDownloadImagePackage={(mode) => void state.handleDownloadImagePackage(mode)}
          onEditArticle={state.openArticleEditModal}
          onOpenPublishModal={state.openPublishModal}
          onStatusChange={(article, status) => void state.handleDirectStatusChange(article, status)}
        />
      </div>

      <AccountModal
        editingAccount={state.editingAccount}
        form={state.accountForm}
        isAdmin={state.isAdmin}
        accountOptions={state.accountSetupOptions}
        accountOptionsLoading={state.accountSetupOptionsLoading}
        open={state.accountModalOpen}
        onTargetUserChange={state.loadAccountSetupOptions}
        onCancel={() => state.setAccountModalOpen(false)}
        onSubmit={(values) => void state.handleAccountSubmit(values)}
      />
      <PublishModal
        form={state.publishForm}
        open={state.publishModalOpen}
        onCancel={() => state.setPublishModalOpen(false)}
        onSubmit={(values) => void state.handlePublishSubmit(values)}
      />
      <ArticleEditModal
        accountOptions={state.accountOptions}
        form={state.articleEditForm}
        open={state.articleEditModalOpen}
        onCancel={() => state.setArticleEditModalOpen(false)}
        onSubmit={(values) => void state.handleArticleEditSubmit(values)}
      />
    </Flex>
  )
}
