// components/MeetingSummaries.tsx
import { MeetingSummary } from '@/types/meetingSummaries'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'

export default function MeetingSummaries({ data }: { data: MeetingSummary[] }) {
  return (
    <ScrollArea className="h-[90vh] p-6">
      <h1 className="text-3xl font-bold mb-4">📋 All Meeting Records</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.map((m) => (
          <Card key={m.id} className="hover:shadow-md transition">
            <CardHeader>
              <CardTitle className="flex justify-between">
                <span>{m.task_id}</span>
                <Badge variant="outline">
                  {new Date(m.created_at).toLocaleDateString()}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-1">
              <p><strong>Source:</strong> {m.source_file}</p>
              <p><strong>WAV:</strong> {m.wav_file}</p>
              <p><strong>Transcript:</strong> {m.transcript_file?.slice(0, 80) || 'N/A'}...</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </ScrollArea>
  )
}
