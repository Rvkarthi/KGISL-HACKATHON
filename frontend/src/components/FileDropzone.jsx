import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, CheckCircle2, AlertCircle } from 'lucide-react'

export default function FileDropzone({ files, onFilesChange, multiple = false }) {
    const [dragError, setDragError] = useState(null)

    const onDrop = useCallback((accepted, rejected) => {
        setDragError(null)
        if (rejected.length > 0) {
            const reason = rejected[0]?.errors?.[0]?.message || 'Invalid file.'
            setDragError(reason)
            return
        }

        if (accepted.length > 0) {
            const validFiles = accepted.filter(f => f.size <= 10 * 1024 * 1024)
            if (validFiles.length < accepted.length) {
                setDragError('Some files were over 10 MB and skipped.')
            }

            if (multiple) {
                // Combine with existing files, distinct by name/size
                onFilesChange(prev => {
                    const existingNames = new Set(prev.map(f => `${f.name}-${f.size}`))
                    const newFiles = validFiles.filter(f => !existingNames.has(`${f.name}-${f.size}`))
                    return [...prev, ...newFiles]
                })
            } else {
                onFilesChange([validFiles[0]])
            }
        }
    }, [multiple, onFilesChange])

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'application/pdf': ['.pdf'] },
        maxFiles: multiple ? 150 : 1,
        multiple: multiple,
    })

    const removeFile = (index) => (e) => {
        e.stopPropagation()
        onFilesChange(prev => prev.filter((_, i) => i !== index))
    }

    const formatSize = (bytes) => {
        if (bytes < 1024) return `${bytes} B`
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    }

    const hasFiles = files && files.length > 0

    return (
        <div>
            <div
                {...getRootProps()}
                id="resume-dropzone"
                className={`
          relative flex flex-col items-center justify-center gap-3
          rounded-xl border-2 border-dashed px-6 py-10 cursor-pointer
          transition-all duration-200
          ${isDragActive
                        ? 'border-brand-400 bg-brand-500/10 shadow-glow-brand'
                        : hasFiles
                            ? 'border-success-500/60 bg-success-500/5'
                            : dragError
                                ? 'border-danger-500/60 bg-danger-500/5'
                                : 'border-surface-600 bg-surface-800/40 hover:border-brand-500/60 hover:bg-surface-700/40'
                    }
        `}
            >
                <input {...getInputProps()} />

                {hasFiles ? (
                    <div className="w-full space-y-3 animate-fade-in">
                        <div className="flex flex-col items-center gap-2 mb-2">
                            <div className="w-10 h-10 rounded-full bg-success-500/20 flex items-center justify-center">
                                <CheckCircle2 className="w-5 h-5 text-success-400" />
                            </div>
                            <p className="text-sm font-semibold text-white">
                                {files.length} {files.length === 1 ? 'File' : 'Files'} Ready
                            </p>
                        </div>

                        <div className="max-h-64 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
                            {files.map((file, idx) => (
                                <div key={`${file.name}-${idx}`} className="flex items-center justify-between p-2 rounded-lg bg-surface-700/50 border border-surface-600">
                                    <div className="flex items-center gap-2 min-w-0">
                                        <FileText className="w-4 h-4 text-brand-400 flex-shrink-0" />
                                        <div className="min-w-0">
                                            <p className="text-xs font-medium text-white truncate">{file.name}</p>
                                            <p className="text-[10px] text-gray-500">{formatSize(file.size)}</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={removeFile(idx)}
                                        className="p-1 hover:bg-danger-500/20 rounded-md text-gray-500 hover:text-danger-400 transition-colors"
                                    >
                                        <X className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            ))}
                        </div>

                        {!isDragActive && (
                            <p className="text-[10px] text-center text-gray-500 pt-2 border-t border-surface-700">
                                Drag more files or <span className="text-brand-400">click to browse</span>
                            </p>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col items-center gap-2 text-center">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${isDragActive ? 'bg-brand-500/30' : 'bg-surface-700'}`}>
                            {isDragActive ? (
                                <Upload className="w-6 h-6 text-brand-400 animate-bounce" />
                            ) : (
                                <FileText className="w-6 h-6 text-gray-400" />
                            )}
                        </div>
                        <div>
                            <p className="text-sm font-medium text-gray-200">
                                {isDragActive
                                    ? (multiple ? 'Drop your resumes here' : 'Drop your resume here')
                                    : (multiple ? 'Drag & drop resumes' : 'Drag & drop your resume')
                                }
                            </p>
                            <p className="text-xs text-gray-500 mt-0.5">
                                or <span className="text-brand-400 font-medium">click to browse</span> — PDF only, max 10 MB
                                {multiple && <span className="block mt-1 text-brand-500/80">Support for 100+ files at once</span>}
                            </p>
                        </div>
                    </div>
                )}
            </div>

            {dragError && (
                <div className="flex items-center gap-2 mt-2 px-3 py-2 rounded-lg bg-danger-500/10 border border-danger-500/20">
                    <AlertCircle className="w-4 h-4 text-danger-400 flex-shrink-0" />
                    <p className="text-xs text-danger-400">{dragError}</p>
                </div>
            )}
        </div>
    )
}
