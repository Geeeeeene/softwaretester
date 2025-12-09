import { Outlet, Link, useLocation } from 'react-router-dom'
import { 
  Home, 
  FolderOpen, 
  TestTube, 
  Play, 
  BarChart3,
  Menu
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: '首页', href: '/', icon: Home },
  { name: '项目管理', href: '/projects', icon: FolderOpen },
  { name: '测试用例', href: '/test-cases', icon: TestTube },
  { name: '测试执行', href: '/execution', icon: Play },
  { name: '结果分析', href: '/results', icon: BarChart3 },
]

export default function Layout() {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <TestTube className="h-8 w-8 text-primary" />
              <span className="ml-2 text-xl font-bold text-gray-900">
                HomemadeTester
              </span>
            </div>
            
            <nav className="hidden md:flex space-x-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={cn(
                      "flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary text-white"
                        : "text-gray-700 hover:bg-gray-100"
                    )}
                  >
                    <item.icon className="h-4 w-4 mr-2" />
                    {item.name}
                  </Link>
                )
              })}
            </nav>

            <button className="md:hidden p-2">
              <Menu className="h-6 w-6" />
            </button>
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* 页脚 */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            © 2024 HomemadeTester. 基于Test IR的统一测试平台
          </p>
        </div>
      </footer>
    </div>
  )
}

