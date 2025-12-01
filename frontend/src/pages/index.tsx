import { useState, useCallback } from 'react'
import Head from 'next/head'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'

export default function Home() {
  const [agencyName, setAgencyName] = useState('')
  const [year, setYear] = useState(new Date().getFullYear())
  const [reportId, setReportId] = useState<number | null>(null)

  // File upload states
  const [visitFile, setVisitFile] = useState<File | null>(null)
  const [tbFile, setTbFile] = useState<File | null>(null)
  const [payrollFile, setPayrollFile] = useState<File | null>(null)

  // Processing state
  const [processing, setProcessing] = useState(false)
  const [status, setStatus] = useState('')
  const [questions, setQuestions] = useState<string[]>([])
  const [downloadUrl, setDownloadUrl] = useState('')

  // Create agency and report
  const startReport = async () => {
    if (!agencyName) {
      alert('Please enter agency name')
      return
    }

    try {
      // Create agency
      const agencyRes = await axios.post('http://localhost:8000/api/agencies', {
        name: agencyName,
        year: year
      })

      // Create report
      const reportRes = await axios.post('http://localhost:8000/api/reports', {
        agency_id: agencyRes.data.id
      })

      setReportId(reportRes.data.id)
      setStatus('Ready to upload files')
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to create report')
    }
  }

  // Upload handlers
  const onDropVisit = useCallback(async (acceptedFiles: File[]) => {
    setVisitFile(acceptedFiles[0])
  }, [])

  const onDropTB = useCallback(async (acceptedFiles: File[]) => {
    setTbFile(acceptedFiles[0])
  }, [])

  const onDropPayroll = useCallback(async (acceptedFiles: File[]) => {
    setPayrollFile(acceptedFiles[0])
  }, [])

  const { getRootProps: getVisitProps, getInputProps: getVisitInput, isDragActive: isVisitDrag } = useDropzone({ onDrop: onDropVisit })
  const { getRootProps: getTBProps, getInputProps: getTBInput, isDragActive: isTBDrag } = useDropzone({ onDrop: onDropTB })
  const { getRootProps: getPayrollProps, getInputProps: getPayrollInput, isDragActive: isPayrollDrag } = useDropzone({ onDrop: onDropPayroll })

  // Process all files
  const processFiles = async () => {
    if (!reportId || !visitFile || !tbFile || !payrollFile) {
      alert('Please upload all 3 files first')
      return
    }

    setProcessing(true)
    setStatus('Uploading files...')

    try {
      // Upload Visit Data
      const visitForm = new FormData()
      visitForm.append('file', visitFile)
      await axios.post(`http://localhost:8000/api/reports/${reportId}/upload/visits`, visitForm)
      setStatus('Visit data uploaded ✓')

      // Upload Trial Balance
      const tbForm = new FormData()
      tbForm.append('file', tbFile)
      await axios.post(`http://localhost:8000/api/reports/${reportId}/upload/trial-balance`, tbForm)
      setStatus('Trial balance uploaded ✓')

      // Upload Payroll
      const payrollForm = new FormData()
      payrollForm.append('file', payrollFile)
      await axios.post(`http://localhost:8000/api/reports/${reportId}/upload/payroll`, payrollForm)
      setStatus('Payroll uploaded ✓')

      // Start processing
      setStatus('Processing files... (this may take 5-15 minutes)')
      await axios.post(`http://localhost:8000/api/reports/${reportId}/process`)

      // Poll for completion
      const interval = setInterval(async () => {
        const res = await axios.get(`http://localhost:8000/api/reports/${reportId}`)

        if (res.data.status === 'completed') {
          clearInterval(interval)
          setStatus('✅ Complete! Report generated successfully.')
          setDownloadUrl(`http://localhost:8000/api/reports/${reportId}/download/excel`)
          setProcessing(false)
        } else if (res.data.status === 'review') {
          clearInterval(interval)
          // Get questions
          const questionsRes = await axios.get(`http://localhost:8000/api/reports/${reportId}/questions`)
          setQuestions(questionsRes.data.questions || [])
          setStatus('⚠️ Processing complete - some questions need clarification')
          setProcessing(false)
        } else if (res.data.status === 'error') {
          clearInterval(interval)
          setStatus('❌ Error occurred during processing')
          setProcessing(false)
        } else {
          setStatus(`Processing... (${res.data.status})`)
        }
      }, 5000) // Poll every 5 seconds

    } catch (error: any) {
      console.error('Processing error:', error)
      setStatus('❌ Error: ' + (error.response?.data?.detail || 'Unknown error'))
      setProcessing(false)
    }
  }

  return (
    <>
      <Head>
        <title>ClearDOH - DOH Cost Report Automation</title>
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">ClearDOH</h1>
            <p className="text-gray-600">NY DOH Home Care Cost Report Automation</p>
          </div>

          {/* Main Card */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
            {/* Agency Info */}
            {!reportId ? (
              <div className="mb-8">
                <h2 className="text-2xl font-semibold mb-6 text-center">Start New Report</h2>
                <div className="max-w-md mx-auto space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Agency Name
                    </label>
                    <input
                      type="text"
                      value={agencyName}
                      onChange={(e) => setAgencyName(e.target.value)}
                      className="input w-full"
                      placeholder="e.g., Anchor and Nemo"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Report Year
                    </label>
                    <input
                      type="number"
                      value={year}
                      onChange={(e) => setYear(parseInt(e.target.value))}
                      className="input w-full"
                    />
                  </div>
                  <button
                    onClick={startReport}
                    disabled={!agencyName}
                    className="btn-primary w-full text-lg py-3"
                  >
                    Continue →
                  </button>
                </div>
              </div>
            ) : (
              <>
                {/* Upload Section */}
                <div className="mb-8">
                  <div className="text-center mb-6">
                    <h2 className="text-2xl font-semibold text-gray-900">
                      {agencyName} - {year}
                    </h2>
                    <p className="text-gray-600 mt-1">Upload your 3 required files</p>
                  </div>

                  <div className="grid md:grid-cols-3 gap-6 mb-8">
                    {/* 1. Visit Data */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-3">
                        1️⃣ Visit Data (Schedule 5)
                      </label>
                      <div
                        {...getVisitProps()}
                        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                          isVisitDrag ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                        } ${visitFile ? 'bg-green-50 border-green-500' : 'hover:border-blue-400'}`}
                      >
                        <input {...getVisitInput()} />
                        <div className="text-4xl mb-2">{visitFile ? '✅' : '📊'}</div>
                        <p className="text-sm font-medium text-gray-700">
                          {visitFile ? visitFile.name : 'Drop file or click'}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">Excel or CSV</p>
                      </div>
                    </div>

                    {/* 2. Trial Balance */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-3">
                        2️⃣ Trial Balance
                      </label>
                      <div
                        {...getTBProps()}
                        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                          isTBDrag ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                        } ${tbFile ? 'bg-green-50 border-green-500' : 'hover:border-blue-400'}`}
                      >
                        <input {...getTBInput()} />
                        <div className="text-4xl mb-2">{tbFile ? '✅' : '💼'}</div>
                        <p className="text-sm font-medium text-gray-700">
                          {tbFile ? tbFile.name : 'Drop file or click'}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">Excel or CSV</p>
                      </div>
                    </div>

                    {/* 3. Payroll */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-3">
                        3️⃣ Payroll Reports
                      </label>
                      <div
                        {...getPayrollProps()}
                        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                          isPayrollDrag ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                        } ${payrollFile ? 'bg-green-50 border-green-500' : 'hover:border-blue-400'}`}
                      >
                        <input {...getPayrollInput()} />
                        <div className="text-4xl mb-2">{payrollFile ? '✅' : '💵'}</div>
                        <p className="text-sm font-medium text-gray-700">
                          {payrollFile ? payrollFile.name : 'Drop file or click'}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">PDF, Excel or CSV</p>
                      </div>
                    </div>
                  </div>

                  {/* Process Button */}
                  <button
                    onClick={processFiles}
                    disabled={!visitFile || !tbFile || !payrollFile || processing}
                    className="btn-primary w-full text-lg py-4 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {processing ? '⏳ Processing...' : '🚀 Process & Generate Report'}
                  </button>
                </div>

                {/* Status */}
                {status && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <p className="text-blue-900 font-medium">{status}</p>
                  </div>
                )}

                {/* Questions */}
                {questions.length > 0 && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
                    <h3 className="text-lg font-semibold text-yellow-900 mb-3">
                      ❓ Questions for Clarification
                    </h3>
                    <ul className="space-y-2">
                      {questions.map((q, i) => (
                        <li key={i} className="text-yellow-800">
                          {i + 1}. {q}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Download */}
                {downloadUrl && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
                    <div className="text-5xl mb-3">🎉</div>
                    <h3 className="text-xl font-semibold text-green-900 mb-4">
                      Report Generated Successfully!
                    </h3>
                    <a
                      href={downloadUrl}
                      className="btn-primary inline-block"
                      download
                    >
                      📥 Download Excel Report
                    </a>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Info Footer */}
          <div className="text-center mt-8 text-gray-600 text-sm">
            <p>Following SOP procedures • Questions compiled for unclear items • Memory updated for next time</p>
          </div>
        </div>
      </div>
    </>
  )
}
