import { useQuery, useQueryClient } from '@tanstack/react-query'
import { toolsApi, type ToolsStatusResponse, type ToolStatus } from '@/lib/api'
import type { AxiosResponse } from 'axios'

/**
 * Hook for checking tool availability status
 */
export function useToolStatus() {
  const queryClient = useQueryClient()

  // Query all tools status
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['tools', 'status'],
    queryFn: async () => {
      const response = await toolsApi.getStatus()
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 5 * 60 * 1000, // Auto-refresh every 5 minutes
  })

  /**
   * Check if a specific tool is available
   */
  const isToolAvailable = (toolName: keyof ToolsStatusResponse): boolean => {
    if (!data) return false
    const tool = data[toolName]
    return tool?.available ?? false
  }

  /**
   * Get status of a specific tool
   */
  const getToolStatus = (toolName: keyof ToolsStatusResponse): ToolStatus | null => {
    if (!data) return null
    const tool = data[toolName]
    return tool || null
  }

  /**
   * Check if all required tools for unit testing are available
   */
  const checkUnitTestTools = (): {
    allAvailable: boolean
    missing: Array<{ name: string; status: ToolStatus }>
  } => {
    if (!data) {
      return { allAvailable: false, missing: [] }
    }

    const requiredTools: Array<{ name: keyof ToolsStatusResponse; displayName: string }> = [
      { name: 'gcov', displayName: 'gcov' },
      { name: 'lcov', displayName: 'lcov' },
      { name: 'drmemory', displayName: 'Dr. Memory' },
    ]

    const missing: Array<{ name: string; status: ToolStatus }> = []

    requiredTools.forEach(({ name, displayName }) => {
      const tool = data[name]
      if (!tool || !tool.available) {
        missing.push({ name: displayName, status: tool || { available: false, message: '未找到' } })
      }
    })

    return {
      allAvailable: missing.length === 0,
      missing,
    }
  }

  /**
   * Manually refresh tool status
   */
  const refresh = async () => {
    await refetch()
  }

  return {
    toolsStatus: data,
    isLoading,
    error,
    isToolAvailable,
    getToolStatus,
    checkUnitTestTools,
    refresh,
  }
}



