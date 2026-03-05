import { useState, useCallback } from 'react'
import { screenResume, bulkScreenResumes } from '../services/api'

/**
 * Custom hook that manages the full screening flow:
 * file selection → submission → loading → result/error state
 */
export function useScreening() {
    const [files, setFiles] = useState([])
    const [jobDescription, setJobDescription] = useState('')
    const [biasFree, setBiasFree] = useState(false)
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)
    const [bulkResult, setBulkResult] = useState(null)
    const [error, setError] = useState(null)

    const reset = useCallback(() => {
        setFiles([])
        setJobDescription('')
        setBiasFree(false)
        setResult(null)
        setBulkResult(null)
        setError(null)
        setLoading(false)
    }, [])

    const submit = useCallback(async () => {
        setError(null)

        if (files.length === 0) {
            setError('Please upload at least one PDF resume.')
            return
        }
        if (!jobDescription.trim()) {
            setError('Please enter a job description.')
            return
        }

        setLoading(true)
        try {
            if (files.length > 1) {
                const data = await bulkScreenResumes(files, jobDescription, biasFree)
                setBulkResult(data)
            } else {
                const data = await screenResume(files[0], jobDescription, biasFree)
                setResult(data)
            }
        } catch (err) {
            const detail =
                err?.response?.data?.detail ||
                err?.message ||
                'An unexpected error occurred. Please check the backend is running.'
            setError(detail)
        } finally {
            setLoading(false)
        }
    }, [files, jobDescription, biasFree])

    return {
        files, setFiles,
        jobDescription, setJobDescription,
        biasFree, setBiasFree,
        loading,
        result, setResult,
        bulkResult, setBulkResult,
        error, setError,
        submit,
        reset,
    }
}
