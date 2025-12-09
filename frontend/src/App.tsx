import { Routes, Route } from 'react-router-dom'
import Layout from '@/components/Layout'
import HomePage from '@/pages/HomePage'
import ProjectsPage from '@/pages/ProjectsPage'
import ProjectDetailPage from '@/pages/ProjectDetailPage'
import TestCasesPage from '@/pages/TestCasesPage'
import TestExecutionPage from '@/pages/TestExecutionPage'
import ResultsPage from '@/pages/ResultsPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/:id" element={<ProjectDetailPage />} />
        <Route path="test-cases" element={<TestCasesPage />} />
        <Route path="execution" element={<TestExecutionPage />} />
        <Route path="results" element={<ResultsPage />} />
      </Route>
    </Routes>
  )
}

export default App
