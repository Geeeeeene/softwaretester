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
    if (error.response?.status === 401) {
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
  binary_path?: string
}

export const projectsApi = {
  list: (params?: { skip?: number; limit?: number; project_type?: string }) =>
    api.get<{ total: number; items: Project[] }>('/api/v1/projects', { params }),
  
  get: (id: number) =>
    api.get<Project>(`/api/v1/projects/${id}`),
  
  create: (data: ProjectCreate) =>
    api.post<Project>('/api/v1/projects', data),
  
  update: (id: number, data: Partial<ProjectCreate>) =>
    api.put<Project>(`/api/v1/projects/${id}`, data),
  
  delete: (id: number) =>
    api.delete(`/api/v1/projects/${id}`),
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
}
