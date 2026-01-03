import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { AlertCircle, XCircle, ExternalLink, RefreshCw } from 'lucide-react'
import { useToolStatus } from '@/hooks/useToolStatus'
import type { ToolStatus } from '@/lib/api'

interface ToolErrorDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  missingTools: Array<{ name: string; status: ToolStatus }>
  onRetry?: () => void
}

export function ToolErrorDialog({ open, onOpenChange, missingTools, onRetry }: ToolErrorDialogProps) {
  const { refresh } = useToolStatus()

  const handleRetry = async () => {
    await refresh()
    if (onRetry) {
      onRetry()
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-red-600">
            <XCircle className="h-5 w-5" />
            工具不可用
          </DialogTitle>
          <DialogDescription>
            以下工具未找到或不可执行，请安装后重试
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {missingTools.map((tool, index) => (
            <div
              key={index}
              className="p-4 border border-red-200 rounded-lg bg-red-50"
            >
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <h4 className="font-semibold text-red-900 mb-1">
                    {tool.name}
                  </h4>
                  <p className="text-sm text-red-700 mb-2">
                    {tool.status.message}
                  </p>
                  {tool.status.path && (
                    <p className="text-xs text-red-600 font-mono mb-2">
                      路径: {tool.status.path}
                    </p>
                  )}
                  {tool.status.install_hint && (
                    <div className="mt-2 p-2 bg-white rounded border border-red-200">
                      <p className="text-xs font-medium text-gray-700 mb-1">安装提示:</p>
                      <pre className="text-xs text-gray-600 whitespace-pre-wrap font-sans">
                        {tool.status.install_hint}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            onClick={handleRetry}
            className="w-full sm:w-auto"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            重新检查
          </Button>
          <Button
            onClick={() => onOpenChange(false)}
            className="w-full sm:w-auto"
          >
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}



