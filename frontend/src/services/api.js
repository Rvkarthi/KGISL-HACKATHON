import axios from 'axios'

const BASE_URL = 'http://localhost:8000'

const api = axios.create({
    baseURL: BASE_URL,
    timeout: 300000,
})

/**
 * Parse a resume PDF (without job description matching).
 * @param {File} file - PDF file object
 * @param {boolean} biassFree - enable bias-free parsing
 * @returns {Promise<ParsedResume>}
 */
export async function parseResume(file, biasFree = false) {
    const form = new FormData()
    form.append('file', file)
    form.append('bias_free', biasFree)

    const { data } = await api.post('/api/resume/parse', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
}

/**
 * Screen a resume against a job description.
 * @param {File} file - PDF resume
 * @param {string} jobDescription - raw JD text
 * @param {boolean} biasFree - enable bias-free evaluation
 * @returns {Promise<MatchResult>}
 */
export async function screenResume(file, jobDescription, biasFree = false) {
    const form = new FormData()
    form.append('file', file)
    form.append('job_description', jobDescription)
    form.append('bias_free', biasFree)

    const { data } = await api.post('/api/resume/screen', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
}

/**
 * Screen multiple resumes against a job description.
 * @param {File[]} files - array of PDF resumes
 * @param {string} jobDescription - raw JD text
 * @param {boolean} biasFree - enable bias-free evaluation
 * @returns {Promise<BulkScreenResponse>}
 */
export async function bulkScreenResumes(files, jobDescription, biasFree = false) {
    const form = new FormData()
    files.forEach(file => {
        form.append('files', file)
    })
    form.append('job_description', jobDescription)
    form.append('bias_free', biasFree)

    const { data } = await api.post('/api/resume/bulk-screen', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
}

/**
 * Fetch screening history records.
 * @returns {Promise<ScreeningRecord[]>}
 */
export async function fetchHistory() {
    const { data } = await api.get('/api/history/')
    return data
}

/**
 * Delete a specific screening record.
 * @param {number} id
 */
export async function deleteRecord(id) {
    await api.delete(`/api/history/${id}`)
}

/**
 * Clear all screening records.
 */
export async function clearAllRecords() {
    await api.delete('/api/history/')
}

/**
 * Fetch a specific screening record's full details.
 * @param {number} id
 * @returns {Promise<MatchResult>}
 */
export async function fetchRecordDetail(id) {
    const { data } = await api.get(`/api/history/${id}`)
    return data
}

/**
 * Fetch all JD templates.
 * @returns {Promise<JDTemplate[]>}
 */
export async function fetchTemplates() {
    const { data } = await api.get('/api/templates/')
    return data
}

/**
 * Save a new JD template.
 * @param {string} title
 * @param {string} description
 * @returns {Promise<JDTemplate>}
 */
export async function createTemplate(title, description) {
    const { data } = await api.post('/api/templates/', { title, description })
    return data
}

/**
 * Delete a JD template.
 * @param {number} id
 */
export async function deleteTemplate(id) {
    await api.delete(`/api/templates/${id}`)
}

export default api
