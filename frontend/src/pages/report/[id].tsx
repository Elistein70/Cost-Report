import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import axios from 'axios'
import { useDropzone } from 'react-dropzone'

interface Report {
  id: number
  agency_id: number
  status: string
  flagged_items_count: number
  payroll_tb_variance?: number
  payroll_hours_variance?: number
}

interface FlaggedItem {
  id: number
  item_type: string
  original_value: string
  suggested_tag: string
  confidence: number
  reviewed: boolean
  approved: boolean
  sheet_name?: string
  row_number?: number
}

export default function ReportPage() {
  const router = useRouter()
  const { id } = router.query

  const [report, setReport] = useState<Report | null>(null)
  const [flaggedItems, setFlaggedItems] = useState<FlaggedItem[]>([])
  const [uploadStatus, setUploadStatus] = useState({
    payroll: false,
    trial_balance: false,
    visits: false,
  })
  const [processing, setProcessing] = useState(false)
  const [currentStep, setCurrentStep] = useState<'upload' | 'review' | 'generate'>('upload')

  useEffect(() => {
    if (id) {
      loadReport()
    }
  }, [id])

  const loadReport = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/reports/${id}`)
      setReport(response.data)

      // Update step based on status
      if (response.data.status === 'review') {
        setCurrentStep('review')
        loadFlaggedItems()
      } else if (response.data.status === 'completed') {
        setCurrentStep('generate')
      }
    } catch (error) {
      console.error('Error loading report:', error)
    }
  }

  const loadFlaggedItems = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/reports/${id}/flagged-items`)
      setFlaggedItems(response.data)
    } catch (error) {
      console.error('Error loading flagged items:', error)
    }
  }

  // File upload handlers
  const onDropPayroll = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    const formData = new FormData()
    formData.append('file', file)

    try {
      await axios.post(`http://localhost:8000/api/reports/${id}/upload/payroll`, formData)
      setUploadStatus({ ...uploadStatus, payroll: true })
    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed')
    }
  }, [id, uploadStatus])

  const onDropTrialBalance = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    const formData = new FormData()
    formData.append('file', file)

    try {
      await axios.post(`http://localhost:8000/api/reports/${id}/upload/trial-balance`, formData)
      setUploadStatus({ ...uploadStatus, trial_balance: true })
    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed')
    }
  }, [id, uploadStatus])

  const onDropVisits = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    const formData = new FormData()
    formData.append('file', file)

    try {
      await axios.post(`http://localhost:8000/api/reports/${id}/upload/visits`, formData)
      setUploadStatus({ ...uploadStatus, visits: true })
    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed')
    }
  }, [id, uploadStatus])

  const { getRootProps: getPayrollProps, getInputProps: getPayrollInput, isDragActive: isPayrollDrag } = useDropzone({ onDrop: onDropPayroll })
  const { getRootProps: getTBProps, getInputProps: getTBInput, isDragActive: isTBDrag } = useDropzone({ onDrop: onDropTrialBalance })
  const { getRootProps: getVisitsProps, getInputProps: getVisitsInput, isDragActive: isVisitsDrag } = useDropzone({ onDrop: onDropVisits })

  const startProcessing = async () => {
    if (!uploadStatus.payroll || !uploadStatus.trial_balance || !uploadStatus.visits) {
      alert('Please upload all required files first')
      return
    }

    setProcessing(true)
    try {
      await axios.post(`http://localhost:8000/api/reports/${id}/process`)

      // Poll for completion
      const interval = setInterval(async () => {
        const response = await axios.get(`http://localhost:8000/api/reports/${id}`)
        if (response.data.status === 'review') {
          clearInterval(interval)
          setProcessing(false)
          setCurrentStep('review')
          loadFlaggedItems()
        }
      }, 3000)
    } catch (error) {
      console.error('Processing error:', error)
      setProcessing(false)
      alert('Processing failed')
    }
  }

  const updateFlaggedItem = async (itemId: number, approved: boolean, correctedTag?: string) => {
    try {
      await axios.put(`http://localhost:8000/api/flagged-items/${itemId}`, {
        approved,
        user_corrected_tag: correctedTag
      })
      loadFlaggedItems()
    } catch (error) {
      console.error('Update error:', error)
    }
  }

  const generateFinalReport = async () => {
    try {
      const response = await axios.post(`http://localhost:8000/api/reports/${id}/generate`)
      alert('Report generated successfully!')
      setCurrentStep('generate')
      loadReport()
    } catch (error: any) {
      console.error('Generation error:', error)
      alert(error.response?.data?.detail || 'Generation failed')
    }
  }

  const downloadReport = async () => {
    window.open(`http://localhost:8000/api/reports/${id}/download/excel`, '_blank')
  }

  if (!report) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  return (
    <>
      <Head>
        <title>Cost Report - ClearDOH</title>
      </Head>

      <div className="min-h-screen py-8 px-4">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <button onClick={() => router.push('/')} className="text-primary mb-4">
              ← Back to Home
            </button>
            <h1 className="text-3xl font-bold">Cost Report #{report.id}</h1>
            <div className="flex gap-4 mt-2 text-sm">
              <span className="px-3 py-1 bg-gray-200 rounded">Status: {report.status}</span>
            </div>
          </div>

          {/* Progress Steps */}
          <div className="card mb-8">
            <div className="flex justify-between items-center">
              <div className={`flex-1 text-center ${currentStep === 'upload' ? 'text-primary font-semibold' : 'text-gray-400'}`}>
                <div className="text-2xl mb-2">📤</div>
                <div>1. Upload Files</div>
              </div>
              <div className="flex-1 h-1 bg-gray-300 mx-4"></div>
              <div className={`flex-1 text-center ${currentStep === 'review' ? 'text-primary font-semibold' : 'text-gray-400'}`}>
                <div className="text-2xl mb-2">👁️</div>
                <div>2. Review</div>
              </div>
              <div className="flex-1 h-1 bg-gray-300 mx-4"></div>
              <div className={`flex-1 text-center ${currentStep === 'generate' ? 'text-primary font-semibold' : 'text-gray-400'}`}>
                <div className="text-2xl mb-2">📊</div>
                <div>3. Generate</div>
              </div>
            </div>
          </div>

          {/* Upload Section */}
          {currentStep === 'upload' && (
            <div className="space-y-6">
              <div className="card">
                <h2 className="text-xl font-semibold mb-4">Upload Required Files</h2>
                <div className="grid gap-4">
                  {/* Payroll */}
                  <div
                    {...getPayrollProps()}
                    className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                      isPayrollDrag ? 'border-primary bg-blue-50' : 'border-gray-300'
                    } ${uploadStatus.payroll ? 'bg-green-50 border-green-500' : ''}`}
                  >
                    <input {...getPayrollInput()} />
                    <div className="text-4xl mb-2">{uploadStatus.payroll ? '✅' : '📄'}</div>
                    <p className="font-semibold">Payroll Register</p>
                    <p className="text-sm text-gray-500">PDF or CSV</p>
                  </div>

                  {/* Trial Balance */}
                  <div
                    {...getTBProps()}
                    className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                      isTBDrag ? 'border-primary bg-blue-50' : 'border-gray-300'
                    } ${uploadStatus.trial_balance ? 'bg-green-50 border-green-500' : ''}`}
                  >
                    <input {...getTBInput()} />
                    <div className="text-4xl mb-2">{uploadStatus.trial_balance ? '✅' : '📄'}</div>
                    <p className="font-semibold">Trial Balance</p>
                    <p className="text-sm text-gray-500">Excel or CSV</p>
                  </div>

                  {/* Visits */}
                  <div
                    {...getVisitsProps()}
                    className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                      isVisitsDrag ? 'border-primary bg-blue-50' : 'border-gray-300'
                    } ${uploadStatus.visits ? 'bg-green-50 border-green-500' : ''}`}
                  >
                    <input {...getVisitsInput()} />
                    <div className="text-4xl mb-2">{uploadStatus.visits ? '✅' : '📄'}</div>
                    <p className="font-semibold">Visit Data - Schedule 5</p>
                    <p className="text-sm text-gray-500">Excel or CSV</p>
                  </div>
                </div>

                <button
                  onClick={startProcessing}
                  disabled={!uploadStatus.payroll || !uploadStatus.trial_balance || !uploadStatus.visits || processing}
                  className="btn-primary w-full mt-6"
                >
                  {processing ? 'Processing...' : 'Start Processing'}
                </button>
              </div>
            </div>
          )}

          {/* Review Section */}
          {currentStep === 'review' && (
            <div className="space-y-6">
              <div className="card">
                <h2 className="text-xl font-semibold mb-4">
                  Review Flagged Items ({flaggedItems.filter(i => !i.reviewed).length} remaining)
                </h2>

                {flaggedItems.filter(i => !i.reviewed).length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-5xl mb-4">🎉</div>
                    <p className="text-xl font-semibold mb-2">All items reviewed!</p>
                    <p className="text-gray-600 mb-6">Ready to generate final report</p>
                    <button onClick={generateFinalReport} className="btn-primary">
                      Generate Final Report
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {flaggedItems.filter(i => !i.reviewed).map((item) => (
                      <div key={item.id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex-1">
                            <div className="text-sm text-gray-500 mb-1">
                              {item.item_type} • {item.sheet_name} • Row {item.row_number}
                            </div>
                            <div className="font-medium mb-1">"{item.original_value}"</div>
                            <div className="text-sm">
                              Suggested: <span className="font-semibold text-primary">{item.suggested_tag}</span>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className={`text-sm font-semibold ${
                              item.confidence >= 0.9 ? 'text-green-600' : 'text-yellow-600'
                            }`}>
                              {(item.confidence * 100).toFixed(0)}% confidence
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => updateFlaggedItem(item.id, true)}
                            className="btn-primary flex-1"
                          >
                            ✓ Approve
                          </button>
                          <button
                            onClick={() => {
                              const corrected = prompt('Enter correct tag:', item.suggested_tag)
                              if (corrected) {
                                updateFlaggedItem(item.id, true, corrected)
                              }
                            }}
                            className="btn-secondary flex-1"
                          >
                            ✏️ Correct
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Generate Section */}
          {currentStep === 'generate' && (
            <div className="card text-center">
              <div className="text-6xl mb-4">🎉</div>
              <h2 className="text-2xl font-bold mb-2">Report Generated!</h2>
              <p className="text-gray-600 mb-6">Your DOH Cost Report is ready to download</p>
              <button onClick={downloadReport} className="btn-primary">
                📥 Download Excel Report
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
