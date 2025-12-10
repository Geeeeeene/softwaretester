import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 如果是FormData，移除Content-Type让浏览器自动设置（包含boundary）
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    
    // 可以在这里添加认证token
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 统一错误处理
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      console.error('网络错误：无法连接到后端服务器，请确保后端正在运行')
      console.error('后端地址:', API_BASE_URL)
    } else if (error.response?.status === 401) {
      // 处理未授权
      console.error('未授权，请登录')
    } else if (error.response?.status === 404) {
      console.error('资源不存在')
    } else if (error.response?.status >= 500) {
      console.error('服务器错误')
    }
    return Promise.reject(error)
  }
)

// ============ 项目API ============

export interface Project {
  id: number
  name: string
  description?: string
  project_type: string
  language?: string
  framework?: string
  source_path?: string
  build_path?: string
  binary_path?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  name: string
  description?: string
  project_type: string
  language?: string
  framework?: string
  source_path?: string
  build_path?: string
  binary_path?: string
}

export const projectsApi = {
  list: (params?: { skip?: number; limit?: number; project_type?: string }) =>
    api.get<{ total: number; items: Project[] }>('/api/v1/projects', { params }),
  
  get: (id: number) =>
    api.get<Project>(`/api/v1/projects/${id}`),
  
  create: (data: ProjectCreate) =>
    api.post<Project>('/api/v1/projects', data),
  
  // 创建项目（支持文件上传）
  createWithFile: (formData: FormData) =>
    api.post<Project>('/api/v1/projects', formData, {
      // 不要手动设置Content-Type，让axios自动处理FormData的boundary
    }),
  
  update: (id: number, data: Partial<ProjectCreate>) =>
    api.put<Project>(`/api/v1/projects/${id}`, data),
  
  delete: (id: number) =>
    api.delete(`/api/v1/projects/${id}`),
}

// ============ 文件上传API ============

export const uploadApi = {
  // 上传项目源代码
  uploadProjectSource: (projectId: number, file: File, extract: boolean = true) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('extract', extract.toString())
    return api.post<{
      message: string
      filename: string
      path?: string
      extracted_path?: string
      size: number
      extracted: boolean
    }>(`/api/v1/upload/project/${projectId}/source`, formData)
  },
}

// ============ 测试用例API ============

export interface TestCase {
  id: number
  project_id: number
  name: string
  description?: string
  test_type: string
  test_ir: Record<string, any>
  priority: string
  tags: string[]
  created_at: string
  updated_at: string
}

export interface TestCaseCreate {
  project_id: number
  name: string
  description?: string
  test_type: string
  test_ir: Record<string, any>
  priority?: string
  tags?: string[]
}

export const testCasesApi = {
  list: (params?: { 
    project_id?: number
    test_type?: string
    priority?: string
    skip?: number
    limit?: number
  }) =>
    api.get<{ total: number; items: TestCase[] }>('/api/v1/test-cases', { params }),
  
  get: (id: number) =>
    api.get<TestCase>(`/api/v1/test-cases/${id}`),
  
  create: (data: TestCaseCreate) =>
    api.post<TestCase>('/api/v1/test-cases', data),
  
  update: (id: number, data: Partial<TestCaseCreate>) =>
    api.put<TestCase>(`/api/v1/test-cases/${id}`, data),
  
  delete: (id: number) =>
    api.delete(`/api/v1/test-cases/${id}`),
}

// ============ 测试执行API ============

export interface TestExecution {
  id: number
  project_id: number
  executor_type: string
  status: string
  total_tests: number
  passed_tests: number
  failed_tests: number
  skipped_tests: number
  duration_seconds?: number
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
  // 新增字段
  coverage_data?: {
    percentage?: number
    lines_covered?: number
    lines_total?: number
    branches_covered?: number
    branches_total?: number
    functions_covered?: number
    functions_total?: number
  }
  result?: {
    issues?: Array<{
      id: string
      type: string
      severity: string
      message: string
      stack_trace?: Array<{
        frame: number
        function: string
        file: string
        line?: number
      }>
    }>
    total_issues?: number
    error_count?: number
    warning_count?: number
  }
  logs?: string
  artifacts?: Array<{
    type: string
    path: string
  }>
}

export interface ExecutionCreate {
  project_id: number
  executor_type: string
  test_case_ids: number[]
}

export const executionsApi = {
  list: (params?: { 
    project_id?: number
    status?: string
    skip?: number
    limit?: number
  }) =>
    api.get<TestExecution[]>('/api/v1/executions', { params }),
  
  get: (id: number) =>
    api.get<TestExecution>(`/api/v1/executions/${id}`),
  
  create: (data: ExecutionCreate) =>
    api.post<TestExecution>('/api/v1/executions', data),
  
  // 执行单元测试（UTBot + gcov + lcov + Dr.Memory）
  runUnitTest: (projectId: number) =>
    api.post<{
      message: string
      execution_id: number
      status: string
      project_id: number
    }>(`/api/v1/projects/${projectId}/test/utbot`),
  
  // 执行本地项目的单元测试（支持localStorage项目）
  runLocalUnitTest: (projectData: {
    id: string
    name: string
    source_file?: {
      name: string
      size: number
      type: string
      data: string
    }
  }) =>
    api.post<{
      message: string
      execution_id: number
      status: string
      temp_path?: string
    }>('/api/v1/projects/local/test/utbot', projectData),
}
