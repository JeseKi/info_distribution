import type dayjs from 'dayjs'
import type {
  ArticleDistributionAccountStatusFilter,
  ArticlePublicationType,
  ArticlePublishStatus,
} from '../../../lib/types'

export interface FilterValues {
  keyword?: string
  project_id?: number
  theme_id?: number
  platform?: string
  publication_type?: ArticlePublicationType
  publish_status?: ArticlePublishStatus
  account_status?: ArticleDistributionAccountStatusFilter
  date_range?: [dayjs.Dayjs, dayjs.Dayjs]
  missing_traffic_only?: boolean
  traffic_date?: dayjs.Dayjs
}
