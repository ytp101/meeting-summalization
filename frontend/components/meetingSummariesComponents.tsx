'use client'

import { MeetingSummary } from '@/types/meetingSummaries'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

type Props = {
  data: MeetingSummary[]
}

export default function MeetingSummaries({ data }: Props) {
  if (!data || data.length === 0) {
    return <p className="text-center text-muted-foreground">No meeting summaries available.</p>
  }

  return (
    <div className='h-[85vh] overflow-x-auto rounded-md border'>
      <div className="min-w-[1400px]">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Source Filename</TableHead>
              <TableHead>Source Path</TableHead>
              <TableHead>WAV Path</TableHead>
              <TableHead>Transcript Path</TableHead>
              <TableHead>Summary Path</TableHead>
              <TableHead>Created At</TableHead>
              <TableHead className="text-right">Download</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((item, index) => (
              <TableRow key={index}>
                <TableCell>{item.id}</TableCell>
                <TableCell className="max-w-[200px] truncate" title={item.source_filename}>
                  {item.source_filename}
                </TableCell>
                <TableCell className="max-w-[200px] truncate" title={item.source_path}>
                  {item.source_path}
                </TableCell>
                <TableCell className="max-w-[200px] truncate" title={item.wav_path}>
                  {item.wav_path}
                </TableCell>
                <TableCell className="max-w-[200px] truncate" title={item.transcript_path}>
                  {item.transcript_path}
                </TableCell>
                <TableCell className="max-w-[200px] truncate" title={item.summary_path}>
                  {item.summary_path}
                </TableCell>
                <TableCell>
                  <Badge variant="outline">
                    {new Date(item.created_at).toLocaleDateString()}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() =>
                      window.open(
                        `http://localhost:8000/download/${item.transcript_path.replace(/^.*[\\/]/, '')}`,
                        '_blank'
                      )
                    }
                  >
                    ⬇ Download
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
