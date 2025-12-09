import { Card, CardContent } from '@/components/ui/card'
import { BarChart3 } from 'lucide-react'

export default function ResultsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">结果分析</h1>
        <p className="text-gray-600 mt-2">查看测试结果、覆盖率和趋势</p>
      </div>

      <Card>
        <CardContent className="text-center py-12">
          <BarChart3 className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500">结果分析功能开发中...</p>
        </CardContent>
      </Card>
    </div>
  )
}

