import type { ReactNode } from 'react'
import type dayjs from 'dayjs'
import type {
  ArticleDistributionAccountPayload,
  ArticlePublicationType,
  ArticlePublishStatus,
} from '../../../lib/types'

export interface ArticleEditFormValues {
  account_id: number
  title: string
  scheduled_date: dayjs.Dayjs
  markdown_content: string
}

export interface ArticleFilterFormValues {
  account_id?: number
  publish_status?: ArticlePublishStatus
  publication_type?: ArticlePublicationType
  date_range?: [dayjs.Dayjs, dayjs.Dayjs]
}

export interface ImagePackageProgressState {
  percent: number
  title: string
  detail: string
}

export type AccountFormValues = ArticleDistributionAccountPayload

export type AccountSelectOption = {
  label: ReactNode
  value: number
}
