'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

type MeetingSummary = {
  filename: string
  summary: string
  processing_time_seconds: number
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [summaries, setSummaries] = useState<MeetingSummary[]>([])

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

      if (!res.ok) {
        throw new Error(`Upload failed with status ${res.status}`)
      }

      const data = await res.json()
      setSummaries([data]) // Or handle multiple summaries if returned as array
    } catch (err) {
      console.error('Upload error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto py-10 space-y-6">
      <div className="space-y-2">
        <Label htmlFor="file">🎙️ Upload Audio File</Label>
        <Input
          id="file"
          type="file"
          accept="audio/*"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        <Button onClick={handleUpload} disabled={!file || loading} className="w-full">
          {loading ? '⏳ Transcribing...' : '🚀 Upload & Summarize'}
        </Button>
      </div>

      <Separator />

      {summaries.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">📄 Meeting Summary</h2>
          {summaries.map((item, idx) => (
            <Card key={idx}>
              <CardHeader>
                <CardTitle>📁 {item.filename}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{item.summary}</p>
                <p className="text-xs text-gray-500 mt-2">
                  ⏱️ Processed in {item.processing_time_seconds} seconds
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
