'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [responseText, setResponseText] = useState('')
  const [loading, setLoading] = useState(false)

  const handleUpload = async () => {
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    setLoading(true)

    try {
      const res = await fetch('http://localhost:8000/uploadfile/', {
        method: 'POST',
        body: formData,
      })

      const data = await res.json()
      setResponseText(data?.summary || 'No summary returned.')
    } catch (err) {
      console.error('Upload error:', err)
      setResponseText('Failed to fetch summary.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-xl mx-auto py-10 space-y-4">
      <Label htmlFor="file">Upload Audio File</Label>
      <Input
        id="file"
        type="file"
        accept="audio/*"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <Button onClick={handleUpload} disabled={!file || loading}>
        {loading ? 'Transcribing...' : 'Upload & Summarize'}
      </Button>

      {responseText && (
        <div className="mt-6 p-4 border rounded bg-muted text-sm whitespace-pre`-wrap">
          {responseText}
        </div>
      )}
    </div>
  )
}