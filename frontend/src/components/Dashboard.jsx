import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, FileSearch, RotateCcw, Save, Trash2, Plus, Bookmark } from 'lucide-react'
import FileDropzone from '../components/FileDropzone'
import BiasFreeToggle from '../components/BiasFreeToggle'
import ErrorBanner from '../components/ErrorBanner'
import { useScreening } from '../hooks/useScreening'
import { fetchTemplates, createTemplate, deleteTemplate } from '../services/api'

export default function Dashboard() {
    const navigate = useNavigate()
    const {
        files, setFiles,
        jobDescription, setJobDescription,
        biasFree, setBiasFree,
        loading, result, bulkResult, error,
        submit, reset,
    } = useScreening()

    const [templates, setTemplates] = useState([])
    const [isSavingTemplate, setIsSavingTemplate] = useState(false)
    const [newTemplateTitle, setNewTemplateTitle] = useState('')

    const loadUserTemplates = async () => {
        try {
            const data = await fetchTemplates()
            setTemplates(data)
        } catch (err) {
            console.error('Failed to load templates')
        }
    }

    useEffect(() => {
        loadUserTemplates()
    }, [])

    const handleSubmit = async (e) => {
        e.preventDefault()
        await submit()
    }

    const handleSaveTemplate = async () => {
        if (!newTemplateTitle.trim() || !jobDescription.trim()) {
            alert('Please provide both a title and a job description.')
            return
        }

        try {
            await createTemplate(newTemplateTitle, jobDescription)
            setNewTemplateTitle('')
            setIsSavingTemplate(false)
            loadUserTemplates()
        } catch (err) {
            alert('Failed to save template.')
        }
    }

    const handleDeleteTemplate = async (id) => {
        if (!window.confirm('Delete this template?')) return
        try {
            await deleteTemplate(id)
            loadUserTemplates()
        } catch (err) {
            alert('Failed to delete template.')
        }
    }

    // If we got a result, navigate to results page
    if (result) {
        navigate('/results', { state: { result } })
    }

    // If we got bulk results, navigate to bulk results page
    if (bulkResult) {
        navigate('/bulk-results', { state: { results: bulkResult.results } })
    }

    return (
        <div className="max-w-5xl mx-auto px-4 py-10 animate-slide-up">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-extrabold text-white leading-tight">Resume Screening Dashboard</h1>
                <p className="text-gray-400 mt-1">Upload one or more resumes (100+) and paste a job description to get ranked results.</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid lg:grid-cols-2 gap-6">
                    {/* Left: Upload + Evaluation Mode */}
                    <div className="space-y-5">
                        {/* Resume Upload */}
                        <div className="card p-5">
                            <h2 className="section-title text-base mb-1">
                                <span className="text-brand-400 font-mono text-xs mr-2">01</span>
                                Upload Resumes (PDF)
                            </h2>
                            <p className="section-sub mb-4">Max 10 MB per file · Multiple upload supported</p>
                            <FileDropzone files={files} onFilesChange={setFiles} multiple={true} />
                        </div>

                        {/* Bias-Free Toggle */}
                        <div className="card p-5">
                            <h2 className="section-title text-base mb-3">
                                <span className="text-brand-400 font-mono text-xs mr-2">03</span>
                                Evaluation Mode
                            </h2>
                            <BiasFreeToggle enabled={biasFree} onChange={setBiasFree} />
                        </div>

                        {/* Templates List */}
                        <div className="card p-5">
                            <div className="flex items-center justify-between mb-3">
                                <h2 className="section-title text-base mb-0">
                                    <span className="text-brand-400 font-mono text-xs mr-2">04</span>
                                    JD Templates
                                </h2>
                                <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">SAVED TEMPLATES</span>
                            </div>

                            {templates.length === 0 ? (
                                <div className="text-center py-6 border-2 border-dashed border-surface-600 rounded-xl">
                                    <Bookmark className="w-5 h-5 text-surface-600 mx-auto mb-2" />
                                    <p className="text-[10px] text-gray-500">No custom templates yet.</p>
                                </div>
                            ) : (
                                <div className="space-y-2 max-h-40 overflow-y-auto pr-1 custom-scrollbar">
                                    {templates.map((tpl) => (
                                        <div key={tpl.id} className="flex items-center justify-between p-2 rounded-lg bg-surface-700/50 border border-surface-600 group transition-all hover:border-brand-500/30">
                                            <button
                                                type="button"
                                                onClick={() => setJobDescription(tpl.description)}
                                                className="flex-1 text-left text-xs font-semibold text-gray-300 group-hover:text-white transition-colors truncate pr-2"
                                            >
                                                {tpl.title}
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => handleDeleteTemplate(tpl.id)}
                                                className="p-1 text-gray-600 hover:text-danger-400 transition-colors"
                                            >
                                                <Trash2 className="w-3.5 h-3.5" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Right: Job Description */}
                    <div className="card p-5 flex flex-col">
                        <div className="flex items-center justify-between mb-1">
                            <h2 className="section-title text-base">
                                <span className="text-brand-400 font-mono text-xs mr-2">02</span>
                                Job Description
                            </h2>
                            <div className="flex items-center gap-3">
                                {!isSavingTemplate ? (
                                    <button
                                        type="button"
                                        onClick={() => setIsSavingTemplate(true)}
                                        className="inline-flex items-center gap-1.5 text-[10px] font-bold text-brand-400 hover:text-brand-300 transition-colors uppercase tracking-wider"
                                    >
                                        <Plus className="w-3 h-3" />
                                        Save as Template
                                    </button>
                                ) : (
                                    <div className="flex items-center gap-2 animate-fade-in">
                                        <input
                                            type="text"
                                            value={newTemplateTitle}
                                            onChange={(e) => setNewTemplateTitle(e.target.value)}
                                            placeholder="Template Title..."
                                            className="bg-surface-800 border-surface-600 text-[10px] px-2 py-1 rounded outline-none focus:border-brand-500 w-32 border"
                                            autoFocus
                                        />
                                        <button
                                            type="button"
                                            onClick={handleSaveTemplate}
                                            className="text-success-400 hover:text-success-300"
                                            title="Confirm Save"
                                        >
                                            <Save className="w-3.5 h-3.5" />
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setIsSavingTemplate(false)}
                                            className="text-danger-400 hover:text-danger-300"
                                            title="Cancel"
                                        >
                                            <RotateCcw className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                )}
                                <span className="text-xs text-gray-500 tabular-nums">{jobDescription.length} chars</span>
                            </div>
                        </div>
                        <p className="section-sub mb-3">Target skills, experience, and domain</p>

                        <textarea
                            id="job-description-input"
                            value={jobDescription}
                            onChange={(e) => setJobDescription(e.target.value)}
                            placeholder="Paste the full job description here, including required skills, years of experience, and domain..."
                            className="input-field flex-1 min-h-[350px] resize-none font-mono text-xs leading-relaxed"
                            rows={18}
                        />
                    </div>
                </div>

                {/* Error */}
                <ErrorBanner message={error} />

                {/* Actions */}
                <div className="flex items-center gap-4">
                    <button
                        type="submit"
                        id="screen-submit-btn"
                        disabled={loading}
                        className="btn-primary px-8 py-3 text-base"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Analyzing Resume...
                            </>
                        ) : (
                            <>
                                <FileSearch className="w-5 h-5" />
                                Screen Resume
                            </>
                        )}
                    </button>

                    <button
                        type="button"
                        id="reset-btn"
                        onClick={reset}
                        className="btn-secondary"
                        disabled={loading}
                    >
                        <RotateCcw className="w-4 h-4" />
                        Reset
                    </button>

                    {loading && (
                        <span className="text-xs text-gray-500 animate-pulse font-medium">
                            Step: Computing scores and ranking candidates...
                        </span>
                    )}
                </div>
            </form>
        </div>
    )
}
