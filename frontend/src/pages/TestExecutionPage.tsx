import { Card, CardContent } from '@/components/ui/card'
import { Play } from 'lucide-react'

export default function TestExecutionPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">测试执行</h1>
        <p className="text-gray-600 mt-2">启动和监控测试执行</p>
      </div>

      <Card>
        <CardContent className="text-center py-12">
          <Play className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500">测试执行功能开发中...</p>
        </CardContent>
      </Card>
    </div>
  )
}

