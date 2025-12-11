import { useState } from 'react'
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react'
import { useToolStatus } from '@/hooks/useToolStatus'
import { ToolErrorDialog } from './ToolErrorDialog'

export function ToolStatusIndicator() {
  const { checkUnitTestTools, isLoading } = useToolStatus()
  const [dialogOpen, setDialogOpen] = useState(false)
  const toolCheck = checkUnitTestTools()

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <AlertCircle className="h-4 w-4 animate-pulse" />
        <span>检查工具中...</span>
      </div>
    )
  }

  const allAvailable = toolCheck.allAvailable
  const missingCount = toolCheck.missing.length

  return (
    <>
      <div
        className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
        onClick={() => {
          if (!allAvailable) {
            setDialogOpen(true)
          }
        }}
      >
        {allAvailable ? (
          <>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            <span className="text-sm text-green-600">所有工具可用</span>
          </>
        ) : (
          <>
            <XCircle className="h-4 w-4 text-red-500" />
            <span className="text-sm text-red-600">
              {missingCount} 个工具缺失
            </span>
          </>
        )}
      </div>

      <ToolErrorDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        missingTools={toolCheck.missing}
      />
    </>
  )
}



