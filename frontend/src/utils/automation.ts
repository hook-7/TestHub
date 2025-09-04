
// 自动化模块安全初始化
export const safeInitAutomation = async () => {
  try {
    const { useAutomationStore } = await import('@/stores/automation')
    const store = useAutomationStore()
    
    // 确保store已初始化
    if (store.templates.length === 0) {
      await store.loadTemplates()
    }
    
    return store
  } catch (error) {
    console.error('自动化模块初始化失败:', error)
    return null
  }
}

// 安全的组件使用
export const useAutomationSafely = () => {
  const store = useAutomationStore()
  
  // 安全的计算属性
  const safeTemplates = computed(() => store.templates || [])
  const safePendingCommands = computed(() => store.pendingCommands || [])
  const safeExecutingCommands = computed(() => store.executingCommands || [])
  
  return {
    ...store,
    templates: safeTemplates,
    pendingCommands: safePendingCommands,
    executingCommands: safeExecutingCommands
  }
}
