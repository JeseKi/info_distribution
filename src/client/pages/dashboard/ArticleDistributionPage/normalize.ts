import type { ArticleDistributionAccountPayload } from '../../../lib/types'

export function normalizeAccountPayload(
  values: ArticleDistributionAccountPayload,
): ArticleDistributionAccountPayload {
  return {
    ...values,
    user_id: values.user_id ? Number(values.user_id) : undefined,
  }
}
