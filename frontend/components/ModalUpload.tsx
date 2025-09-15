'use client'

import { useEffect, useRef, useState, useTransition } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { useRouter } from 'next/navigation'

export default function ModalUpload() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, startTransition] = useTransition()
  const [taskId, setTaskId] = useState<string | null>(null)
  const [progress, setProgress] = useState<number>(0)
  const [statusText, setStatusText] = useState<string>('Idle')
  const esRef = useRef<EventSource | null>(null)
  const router = useRouter()

  const handleUpload = async () => {
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)

    startTransition(async () => {
      try {
        const base = process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8000'
        const res = await fetch(`${base}/uploadfile/async`, {
          method: 'POST',
          body: formData,
        })

        if (!res.ok) throw new Error('Upload failed')
        const data = await res.json()
        const id = data.task_id as string
        setTaskId(id)
        setStatusText('Processing...')
        // Start SSE
        const es = new EventSource(`${base}/progress/stream/${id}`)
        esRef.current = es
        es.onmessage = (evt) => {
          try {
            const ev = JSON.parse(evt.data)
            const p = typeof ev.progress === 'number' ? ev.progress : progress
            setProgress(Math.max(0, Math.min(100, p)))
            const svc = ev.service ? String(ev.service) : 'gateway'
            const step = ev.step ? String(ev.step) : 'step'
            const status = ev.status ? String(ev.status) : 'progress'
            setStatusText(`${svc}: ${step} (${status})`)
            const isFinal = ev.final === true || (svc === 'gateway' && step === 'done')
            if (isFinal) {
              es.close()
              esRef.current = null
              // Refresh summaries list when done
              router.refresh()
            }
            if (status === 'error') {
              es.close()
              esRef.current = null
            }
          } catch (e) {
            console.error('SSE parse error', e)
          }
        }
        es.onerror = (e) => {
          console.warn('SSE error', e)
        }
      } catch (err) {
        console.error('Upload error:', err)
      }
    })
  }

  useEffect(() => {
    return () => {
      esRef.current?.close()
    }
  }, [])

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="default">📤 Upload Meeting</Button>
      </DialogTrigger>
      <DialogContent className="space-y-4">
        <DialogTitle>Upload MP4 or MP3</DialogTitle>
        <Label htmlFor="file">Choose audio/video file</Label>
        <Input
          id="file"
          type="file"
          accept="audio/*,video/*"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        <Button onClick={handleUpload} disabled={!file || loading}>
          {loading ? '⏳ Uploading...' : '🚀 Upload & Refresh'}
        </Button>
        {taskId && (
          <div className="space-y-2">
            <div className="text-sm text-gray-600">Task: {taskId}</div>
            <div className="w-full h-3 bg-gray-200 rounded">
              <div
                className="h-3 bg-blue-500 rounded"
                style={{ width: `${progress}%`, transition: 'width 200ms linear' }}
              />
            </div>
            <div className="text-sm">{statusText} — {progress}%</div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
