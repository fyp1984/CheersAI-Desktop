import { createStore, useStore } from 'zustand'

type MemberTagSelectionState = {
  selectedTagIds: string[]
}

type MemberTagSelectionActions = {
  resetSelectedTagIds: (selectedTagIds?: string[]) => void
  setSelectedTagIds: (selectedTagIds: string[]) => void
  toggleSelectedTagId: (tagId: string) => void
  selectGroup: (tagIds: string[]) => void
  invertGroup: (tagIds: string[]) => void
}

export type MemberTagSelectionStore = ReturnType<typeof createMemberTagSelectionStore>

export const createMemberTagSelectionStore = (initialSelectedTagIds: string[] = []) => createStore<
  MemberTagSelectionState & MemberTagSelectionActions
>(set => ({
  selectedTagIds: initialSelectedTagIds,
  resetSelectedTagIds: selectedTagIds => set({ selectedTagIds: selectedTagIds || [] }),
  setSelectedTagIds: selectedTagIds => set({ selectedTagIds }),
  toggleSelectedTagId: tagId => set((state) => {
    if (state.selectedTagIds.includes(tagId))
      return { selectedTagIds: state.selectedTagIds.filter(id => id !== tagId) }

    return { selectedTagIds: [...state.selectedTagIds, tagId] }
  }),
  selectGroup: tagIds => set((state) => ({
    selectedTagIds: [...new Set([...state.selectedTagIds, ...tagIds])],
  })),
  invertGroup: tagIds => set((state) => {
    const selectedTagIdSet = new Set(state.selectedTagIds)
    const nextSelectedTagIds = state.selectedTagIds.filter(id => !tagIds.includes(id))

    tagIds.forEach((tagId) => {
      if (!selectedTagIdSet.has(tagId))
        nextSelectedTagIds.push(tagId)
    })

    return { selectedTagIds: nextSelectedTagIds }
  }),
}))

export const useMemberTagSelectionStore = <T>(
  store: MemberTagSelectionStore,
  selector: (state: MemberTagSelectionState & MemberTagSelectionActions) => T,
) => useStore(store, selector)
