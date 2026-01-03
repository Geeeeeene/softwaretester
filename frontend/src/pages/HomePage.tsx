import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  FolderOpen, 
  TestTube, 
  Play, 
  BarChart3,
  Upload,
  Code,
  Zap
} from 'lucide-react'

export default function HomePage() {
  const features = [
    {
      title: '项目管理',
      description: '创建和管理测试项目，支持多种语言和框架',
      icon: FolderOpen,
      href: '/projects',
      color: 'text-blue-600',
    },
  ]

  const highlights = [
    {
      title: '统一Test IR',
      description: 'JSON/YAML格式的测试中间表示，支持多种测试类型',
      icon: Code,
    },
    {
      title: '智能执行',
      description: '基于队列的异步执行，支持并行和优先级调度',
      icon: Zap,
    },
    {
      title: '快速上手',
      description: 'Docker一键部署，完善的API文档和示例',
      icon: Upload,
    },
  ]

  return (
    <div className="space-y-8">
      {/* Hero区域 */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-gray-900">
          欢迎使用 HomemadeTester
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          基于Test IR的统一测试平台，支持系统测试、单元测试、集成测试和静态分析
        </p>
        <div className="flex justify-center gap-4 pt-4">
          <Link to="/projects">
            <Button size="lg">
              <FolderOpen className="mr-2 h-5 w-5" />
              开始测试
            </Button>
          </Link>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button size="lg" variant="outline">
              <Code className="mr-2 h-5 w-5" />
              API文档
            </Button>
          </a>
        </div>
      </div>

      {/* 核心功能 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {features.map((feature) => (
          <Link key={feature.title} to={feature.href}>
            <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <feature.icon className={`h-10 w-10 ${feature.color} mb-2`} />
                <CardTitle className="text-xl">{feature.title}</CardTitle>
                <CardDescription>{feature.description}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>

      {/* 特性亮点 */}
      <div className="bg-white rounded-lg border p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          平台特性
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {highlights.map((highlight) => (
            <div key={highlight.title} className="text-center space-y-2">
              <highlight.icon className="h-12 w-12 mx-auto text-primary" />
              <h3 className="font-semibold text-lg">{highlight.title}</h3>
              <p className="text-sm text-gray-600">{highlight.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 快速开始 */}
      <Card>
        <CardHeader>
          <CardTitle>快速开始</CardTitle>
          <CardDescription>通过以下步骤开始使用测试平台</CardDescription>
        </CardHeader>
        <CardContent>
          <ol className="list-decimal list-inside space-y-2 text-gray-700">
            <li>创建一个新项目，上传源代码或二进制文件</li>
            <li>编写测试用例，使用Test IR格式（JSON/YAML）</li>
            <li>选择执行器（Robot Framework、UTBot、Static Analyzer）</li>
            <li>运行测试并查看实时进度</li>
            <li>分析测试结果、覆盖率和趋势</li>
          </ol>
          <div className="mt-6">
            <Link to="/projects">
              <Button>
                创建第一个项目
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

