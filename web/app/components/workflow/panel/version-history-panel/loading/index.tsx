import Item from './item'

const itemConfig = Array.from({ length: 8 }).map((_, index) => {
  return {
    key: `loading-${index === 0 ? 'first' : 'middle'}-${index === 7 ? 'last' : 'normal'}-${(index + 1) % 2 === 0 ? 'even' : 'odd'}`,
    isFirst: index === 0,
    isLast: index === 7,
    titleWidth: (index + 1) % 2 === 0 ? 'w-1/3' : 'w-2/5',
    releaseNotesWidth: (index + 1) % 2 === 0 ? 'w-3/4' : 'w-4/6',
  }
})

const Loading = () => {
  return (
    <div className="relative w-full overflow-y-hidden">
      <div className="absolute left-0 top-0 z-10 h-full w-full bg-dataset-chunk-list-mask-bg" />
      {itemConfig.map(({ key, ...config }) => <Item key={key} {...config} />)}
    </div>
  )
}

export default Loading
