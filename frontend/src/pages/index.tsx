import { useState, useEffect } from 'react'
import Head from 'next/head'
import { useRouter } from 'next/router'
import axios from 'axios'

interface Agency {
  id: number
  name: string
  year: number
  created_at: string
}

export default function Home() {
  const router = useRouter()
  const [agencies, setAgencies] = useState<Agency[]>([])
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newAgency, setNewAgency] = useState({ name: '', year: new Date().getFullYear() })

  useEffect(() => {
    loadAgencies()
  }, [])

  const loadAgencies = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/agencies')
      setAgencies(response.data)
    } catch (error) {
      console.error('Error loading agencies:', error)
    }
  }

  const createAgency = async () => {
    try {
      const response = await axios.post('http://localhost:8000/api/agencies', newAgency)
      const agency = response.data

      // Create a report for this agency
      const reportResponse = await axios.post('http://localhost:8000/api/reports', {
        agency_id: agency.id
      })

      // Navigate to report page
      router.push(`/report/${reportResponse.data.id}`)
    } catch (error) {
      console.error('Error creating agency:', error)
      alert('Failed to create agency')
    }
  }

  const openAgency = async (agencyId: number) => {
    try {
      // Create new report for existing agency
      const response = await axios.post('http://localhost:8000/api/reports', {
        agency_id: agencyId
      })
      router.push(`/report/${response.data.id}`)
    } catch (error) {
      console.error('Error:', error)
    }
  }

  return (
    <>
      <Head>
        <title>ClearDOH - NY DOH Cost Report Automation</title>
        <meta name="description" content="Automated DOH Cost Report generation" />
      </Head>

      <div className="min-h-screen py-12 px-4">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold mb-4 text-primary">ClearDOH</h1>
            <p className="text-xl text-gray-600">
              NY DOH Home Care Cost Report Automation
            </p>
            <p className="text-gray-500 mt-2">
              Generate complete audit-ready reports in 5 minutes
            </p>
          </div>

          {/* Create New Button */}
          <div className="text-center mb-8">
            <button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="btn-primary text-lg"
            >
              + Create New Cost Report
            </button>
          </div>

          {/* Create Form */}
          {showCreateForm && (
            <div className="card max-w-md mx-auto mb-8">
              <h2 className="text-2xl font-semibold mb-4">New Agency</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Agency Name</label>
                  <input
                    type="text"
                    className="input w-full"
                    value={newAgency.name}
                    onChange={(e) => setNewAgency({ ...newAgency, name: e.target.value })}
                    placeholder="Enter agency name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Year</label>
                  <input
                    type="number"
                    className="input w-full"
                    value={newAgency.year}
                    onChange={(e) => setNewAgency({ ...newAgency, year: parseInt(e.target.value) })}
                  />
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={createAgency}
                    className="btn-primary flex-1"
                    disabled={!newAgency.name}
                  >
                    Create & Start
                  </button>
                  <button
                    onClick={() => setShowCreateForm(false)}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Recent Agencies */}
          {agencies.length > 0 && (
            <div className="card">
              <h2 className="text-2xl font-semibold mb-6">Recent Agencies</h2>
              <div className="grid gap-4">
                {agencies.map((agency) => (
                  <div
                    key={agency.id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-primary cursor-pointer transition-colors"
                    onClick={() => openAgency(agency.id)}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <h3 className="text-lg font-semibold">{agency.name}</h3>
                        <p className="text-gray-500">Year: {agency.year}</p>
                      </div>
                      <div className="text-sm text-gray-400">
                        Created: {new Date(agency.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-6 mt-12">
            <div className="card text-center">
              <div className="text-4xl mb-3">📤</div>
              <h3 className="text-lg font-semibold mb-2">Upload Files</h3>
              <p className="text-gray-600">
                Drag & drop payroll, trial balance, and visit data
              </p>
            </div>
            <div className="card text-center">
              <div className="text-4xl mb-3">🤖</div>
              <h3 className="text-lg font-semibold mb-2">Auto-Tag</h3>
              <p className="text-gray-600">
                AI-powered tagging with 92%+ confidence
              </p>
            </div>
            <div className="card text-center">
              <div className="text-4xl mb-3">✅</div>
              <h3 className="text-lg font-semibold mb-2">Generate Report</h3>
              <p className="text-gray-600">
                Complete Excel file ready for submission
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
