import type { Tag } from '@/app/components/base/tag-management/constant'

export const MAX_TAG_STRING_LENGTH = 500

export type SystemTagCategory = 'app' | 'kb'

export type CategorizedTag = Tag & {
  category: SystemTagCategory
  groupLabel: string
  displayName: string
}

export type GroupedTagSection = {
  groupLabel: string
  tags: CategorizedTag[]
}

const DEFAULT_GROUP_LABEL = '默认分组'
const SSO_TAG_SPLIT_PATTERN = /[，、；;|,]+/
const DEFAULT_FALLBACK_TAGS: Tag[] = [
  { id: 'fallback-agent-default', name: 'Agent:通用 Agent/默认协作', type: 'app', binding_count: 0 },
  { id: 'fallback-workflow-default', name: 'Workflow:通用 Workflow/默认流程', type: 'app', binding_count: 0 },
  { id: 'fallback-kb-default', name: '知识库/默认知识库', type: 'knowledge', binding_count: 0 },
]
const CATEGORY_PREFIX_PATTERNS: Array<{ category: SystemTagCategory, pattern: RegExp }> = [
  { category: 'app', pattern: /^(workflow|工作流)[/:：|｜-]\s*/i },
  { category: 'kb', pattern: /^(knowledge|kb|知识库)[/:：|｜-]\s*/i },
  { category: 'app', pattern: /^(agent|智能体)[/:：|｜-]\s*/i },
]
const GROUP_SEPARATOR_PATTERNS = ['::', '：', ':', '/', '／', '|', '｜', ' - ']

const normalizeMatchToken = (value: string) => value.trim().toLowerCase()

const detectCategory = (name: string, fallbackType: Tag['type']): { category: SystemTagCategory, normalizedName: string } => {
  if (fallbackType === 'knowledge')
    return { category: 'kb', normalizedName: name.trim() }

  for (const { category, pattern } of CATEGORY_PREFIX_PATTERNS) {
    if (pattern.test(name))
      return { category, normalizedName: name.replace(pattern, '').trim() }
  }

  return {
    category: 'app',
    normalizedName: name.trim(),
  }
}

const splitGroupAndDisplayName = (name: string) => {
  const normalizedName = name.trim()
  for (const separator of GROUP_SEPARATOR_PATTERNS) {
    const separatorIndex = normalizedName.indexOf(separator)
    if (separatorIndex <= 0)
      continue

    const groupLabel = normalizedName.slice(0, separatorIndex).trim()
    const displayName = normalizedName.slice(separatorIndex + separator.length).trim()
    if (groupLabel && displayName) {
      return {
        groupLabel,
        displayName,
      }
    }
  }

  return {
    groupLabel: DEFAULT_GROUP_LABEL,
    displayName: normalizedName,
  }
}

export const getCategorizedTagMatchKey = (tag: Pick<CategorizedTag, 'category' | 'groupLabel' | 'displayName'>) => {
  return [
    tag.category,
    normalizeMatchToken(tag.groupLabel),
    normalizeMatchToken(tag.displayName),
  ].join('::')
}

export const createCategorizedTagPreview = (name: string, fallbackType: Tag['type'] = 'app') => {
  const { category, normalizedName } = detectCategory(name, fallbackType)
  const { groupLabel, displayName } = splitGroupAndDisplayName(normalizedName)

  return {
    category,
    groupLabel,
    displayName,
  }
}

export const categorizeSystemTags = (tags: Tag[]) => {
  const categorizedTags: CategorizedTag[] = []
  const seenKeys = new Set<string>()

  tags.forEach((tag) => {
    const { category, normalizedName } = detectCategory(tag.name, tag.type)
    const { groupLabel, displayName } = splitGroupAndDisplayName(normalizedName)
    const categorizedTag = {
      ...tag,
      category,
      groupLabel,
      displayName,
    } satisfies CategorizedTag
    const matchKey = getCategorizedTagMatchKey(categorizedTag)

    if (seenKeys.has(matchKey))
      return

    seenKeys.add(matchKey)
    categorizedTags.push(categorizedTag)
  })

  return categorizedTags
}

export const buildGroupedTagSections = (tags: CategorizedTag[], category: SystemTagCategory) => {
  const groupedSections = new Map<string, CategorizedTag[]>()

  tags
    .filter(tag => tag.category === category)
    .forEach((tag) => {
      const currentTags = groupedSections.get(tag.groupLabel) || []
      currentTags.push(tag)
      groupedSections.set(tag.groupLabel, currentTags)
    })

  return Array.from(groupedSections.entries()).map(([groupLabel, groupedTags]) => ({
    groupLabel,
    tags: groupedTags,
  })) satisfies GroupedTagSection[]
}

export const stringifySelectedTagNames = (tagNames: string[]) => {
  if (!tagNames.length)
    return ''

  const separator = tagNames.some(tagName => tagName.includes(',')) ? '|' : ','
  return tagNames.join(separator)
}

export const exceedsTagStringLimit = (tagString: string) => tagString.length > MAX_TAG_STRING_LENGTH

export const parseUserTagNames = (rawValue: unknown) => {
  let values: string[] = []

  if (typeof rawValue === 'string')
    values = rawValue.split(SSO_TAG_SPLIT_PATTERN)
  else if (Array.isArray(rawValue))
    values = rawValue.flatMap(item => typeof item === 'string' ? item.split(SSO_TAG_SPLIT_PATTERN) : [])
  else
    return []

  const normalizedNames: string[] = []
  const seenNames = new Set<string>()

  values.forEach((value) => {
    const normalizedValue = value.trim()
    if (!normalizedValue || seenNames.has(normalizedValue))
      return

    normalizedNames.push(normalizedValue)
    seenNames.add(normalizedValue)
  })

  return normalizedNames
}

const buildVirtualTagId = (name: string) => {
  const normalized = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4E00-\u9FA5]+/g, '-')
    .replace(/^-+|-+$/g, '')

  return `virtual-tag-${normalized || 'unknown'}`
}

export const createVirtualTag = (name: string, id = buildVirtualTagId(name)) => {
  const { category } = detectCategory(name, 'app')

  return {
    id,
    name,
    type: category === 'kb' ? 'knowledge' : 'app',
    binding_count: 0,
  } satisfies Tag
}

export const resolveCategorizedTagsByNames = (availableTags: CategorizedTag[], tagNames: string[]) => {
  const availableTagNameMap = new Map(availableTags.map(tag => [normalizeMatchToken(tag.name), tag]))
  const availableTagMatchKeyMap = new Map(availableTags.map(tag => [getCategorizedTagMatchKey(tag), tag]))
  const resolvedTags: CategorizedTag[] = []
  const seenIds = new Set<string>()

  tagNames.forEach((tagName) => {
    const normalizedTagName = normalizeMatchToken(tagName)
    const exactTag = availableTagNameMap.get(normalizedTagName)
    const matchedTag = exactTag || availableTagMatchKeyMap.get(getCategorizedTagMatchKey({
      ...createCategorizedTagPreview(tagName),
    }))

    if (!matchedTag || seenIds.has(matchedTag.id))
      return

    seenIds.add(matchedTag.id)
    resolvedTags.push(matchedTag)
  })

  return resolvedTags
}

export const ensureNonEmptySystemTags = (tags: Tag[]) => {
  if (tags.length)
    return tags

  return DEFAULT_FALLBACK_TAGS.map(tag => ({ ...tag }))
}
