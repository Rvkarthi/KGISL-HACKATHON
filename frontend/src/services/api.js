import axios from 'axios'

const BASE_URL = 'http://localhost:8000'

const api = axios.create({
    baseURL: BASE_URL,
    timeout: 300000,
})

// Add a request interceptor to include the JWT token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
}, (error) => {
    return Promise.reject(error)
})

// Helper to transform backend score string "85.50%" to number 85.5
const parseBackendScore = (scoreStr) => {
    if (!scoreStr || typeof scoreStr !== 'string') return 0
    return parseFloat(scoreStr.replace('%', '')) || 0
}

/**
 * Auth API calls
 */
export async function login(email, password) {
    const { data } = await api.post('/api/auth/login', { email, password })
    return data
}

export async function registerNormal(formData) {
    const { data } = await api.post('/api/auth/register/normal', formData)
    return data
}

export async function registerHR(formData) {
    const { data } = await api.post('/api/auth/register/hr', formData)
    return data
}

export async function getMe() {
    const { data } = await api.get('/api/auth/me')
    return data
}

/**
 * ATS API calls
 */

/**
 * Parse a resume PDF.
 * @param {File} file - PDF file object
 * @returns {Promise<any>}
 */
export async function parseResume(file) {
    const form = new FormData()
    form.append('pdf_file', file)

    const { data } = await api.post('/api/ats/parser', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
}

/**
 * Screen a resume.
 * @param {File} file - PDF resume
 * @param {string} jobDescription - JD text (backend JD is currently hardcoded)
 * @param {boolean} biasFree - Bias free mode
 * @returns {Promise<any>}
 */
export async function screenResume(file, jobDescription, biasFree) {
    const form = new FormData()
    form.append('pdf_file', file)
    // Note: Backend currently has JD hardcoded in engine, but we pass these for future-proofing
    if (jobDescription) form.append('job_description', jobDescription)
    form.append('bias_free', biasFree)

    const { data } = await api.post('/api/ats/screening', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
    })

    // Map backend response to frontend expected format
    return {
        filename: file.name,
        candidate_name: data.info?.name || 'Anonymous',
        email: data.info?.email || '',
        phone: data.info?.phone || '',
        final_score: parseBackendScore(data.overall),
        skill_score: parseBackendScore(data.fields?.skills || data.fields?.skill),
        experience_score: parseBackendScore(data.fields?.experience),
        domain_score: parseBackendScore(data.fields?.about),
        matched_skills: data.skills || [],
        missing_skills: data.skipped || [],
        experience_gap: 0,
        domain_match: true,
        candidate_domain: data.info?.role || 'N/A',
        job_domain: 'Target Role',
        candidate_experience: 0,
        required_experience: 0,
        learning_roadmap: [],
        recommended_domains: [],
        top_skills_to_gain: data.skipped || [],
    }
}

/**
 * Screen multiple resumes.
 * @param {File[]} files - array of PDF resumes
 * @param {string} jobDescription - JD text
 * @param {boolean} biasFree - Bias free mode
 * @returns {Promise<any>}
 */
export async function bulkScreenResumes(files, jobDescription, biasFree) {
    const form = new FormData()
    files.forEach(file => {
        form.append('pdf_files', file)
    })
    if (jobDescription) form.append('job_description', jobDescription)
    form.append('bias_free', biasFree)

    const { data } = await api.post('/api/ats/screening/bulk', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
    })

    // Map bulk results
    const mappedResults = data.results.map(res => {
        if (res.status !== 'success') {
            return {
                filename: res.filename,
                candidate_name: 'Error',
                final_score: 0,
                error: res.error
            }
        }
        const r = res.result
        return {
            filename: res.filename,
            candidate_name: r.info?.name || 'Anonymous',
            email: r.info?.email || '',
            phone: r.info?.phone || '',
            final_score: parseBackendScore(r.overall),
            candidate_experience: 0,
            candidate_domain: r.info?.role || 'N/A',
        }
    })

    return {
        results: mappedResults,
        total: data.total,
        succeeded: data.succeeded,
        failed: data.failed
    }
}

/**
 * Fetch history (Mocked for now as backend doesn't have it)
 */
export async function fetchHistory() {
    // Return empty for now as backend lacks this endpoint
    return []
}

export async function deleteRecord(id) {
    return true
}

export async function clearAllRecords() {
    return true
}

export async function fetchRecordDetail(id) {
    return null
}

/**
 * Fetch templates (Mocked for now)
 */
export async function fetchTemplates() {
    return []
}

export async function createTemplate(title, description) {
    return { id: Math.random(), title, description }
}

export async function deleteTemplate(id) {
    return true
}

export default api
