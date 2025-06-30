'use client'

import { useState, useTransition } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { useRouter } from 'next/navigation'

export default function ModalUpload() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, startTransition] = useTransition()
  const router = useRouter()

  const handleUpload = async () => {
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)

    startTransition(async () => {
      try {
        const res = await fetch('http://localhost:8000/uploadfile/', {
          method: 'POST',
          body: formData,
        })

        if (!res.ok) throw new Error('Upload failed')

        // Re-fetch summaries list
        router.refresh()
      } catch (err) {
        console.error('Upload error:', err)
      }
    })
  }

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
      </DialogContent>
    </Dialog>
  )
}
