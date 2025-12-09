import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus, TestTube } from 'lucide-react'

export default function TestCasesPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">测试用例</h1>
          <p className="text-gray-600 mt-2">管理和编辑测试用例（Test IR格式）</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          创建用例
        </Button>
      </div>

      <Card>
        <CardContent className="text-center py-12">
          <TestTube className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500">测试用例功能开发中...</p>
        </CardContent>
      </Card>
    </div>
  )
}

