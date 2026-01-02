import React, { Component, ErrorInfo, ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { AlertTriangle } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary 捕获到错误:', error, errorInfo)
    this.setState({
      error,
      errorInfo,
    })
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
    // 刷新页面以确保状态完全重置
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="h-8 w-8 text-red-500" />
              <h1 className="text-2xl font-bold text-gray-900">页面出现错误</h1>
            </div>
            
            <p className="text-gray-600 mb-4">
              抱歉，页面在渲染时遇到了错误。这可能是由于数据格式问题或代码错误导致的。
            </p>

            {this.state.error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <h2 className="text-sm font-semibold text-red-800 mb-2">错误信息：</h2>
                <p className="text-sm text-red-700 font-mono break-all">
                  {this.state.error.message || '未知错误'}
                </p>
              </div>
            )}

            {this.state.errorInfo && process.env.NODE_ENV === 'development' && (
              <details className="mb-4">
                <summary className="text-sm font-semibold text-gray-700 cursor-pointer mb-2">
                  详细错误信息（开发模式）
                </summary>
                <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto max-h-64">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}

            <div className="flex gap-3">
              <Button onClick={this.handleReset} className="flex-1">
                刷新页面
              </Button>
              <Button
                variant="outline"
                onClick={() => window.history.back()}
                className="flex-1"
              >
                返回上一页
              </Button>
            </div>

            <p className="text-xs text-gray-500 mt-4">
              提示：如果问题持续存在，请检查浏览器控制台的详细错误信息。
            </p>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}



















