'use client'

import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  ColumnDef,
  ColumnResizeMode,
} from '@tanstack/react-table'
import { useRef, useState } from 'react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { MeetingSummary } from '@/types/meetingSummaries'

type Props = {
  data: MeetingSummary[]
}

export default function ResizableTable({ data }: Props) {
  const [columnResizeMode] = useState<ColumnResizeMode>('onChange')
  const tableContainerRef = useRef<HTMLDivElement>(null)

  const columns: ColumnDef<MeetingSummary>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
  },
  {
    accessorKey: 'work_id',
    header: 'Work ID',
  },
  {
    id: 'source_download',
    header: 'Source',
    cell: ({ row }) => {
      const workId = row.original.work_id
      return (
        <a
          href={`http://localhost:8010/download/${workId}/source`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-500 underline"
        >
          Download
        </a>
      )
    },
  },
  {
    id: 'wav_download',
    header: 'WAV',
    cell: ({ row }) => {
      const workId = row.original.work_id
      return (
        <a
          href={`http://localhost:8010/download/${workId}/wav`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-500 underline"
        >
          Download
        </a>
      )
    },
  },
  {
    id: 'transcript_download',
    header: 'Transcript',
    cell: ({ row }) => {
      const workId = row.original.work_id
      return (
        <a
          href={`http://localhost:8010/download/${workId}/transcript`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-500 underline"
        >
          Download
        </a>
      )
    },
  },
  {
    id: 'summary_download',
    header: 'Summary',
    cell: ({ row }) => {
      const workId = row.original.work_id
      return (
        <a
          href={`http://localhost:8010/download/${workId}/summary`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-500 underline"
        >
          Download
        </a>
      )
    },
  },
  {
    accessorKey: 'created_at',
    header: 'Created At',
    cell: ({ getValue }) => (
      <span>{new Date(getValue() as string).toLocaleDateString()}</span>
    ),
  },
]

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    columnResizeMode,
    columnResizeDirection: 'ltr',
    enableColumnResizing: true,
  })

  return (
    <div ref={tableContainerRef} className="overflow-x-auto border rounded-md">
      <Table style={{ width: table.getTotalSize() }}>
        <TableHeader>
          {table.getHeaderGroups().map(headerGroup => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map(header => (
                <TableHead
                  key={header.id}
                  style={{ width: header.getSize() }}
                  className="relative group"
                >
                  {flexRender(header.column.columnDef.header, header.getContext())}
                  {header.column.getCanResize() && (
                    <div
                      onMouseDown={header.getResizeHandler()}
                      onTouchStart={header.getResizeHandler()}
                      className="absolute right-0 top-0 h-full w-1 cursor-col-resize bg-transparent group-hover:bg-muted"
                    />
                  )}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows.map(row => (
            <TableRow key={row.id}>
              {row.getVisibleCells().map(cell => (
                <TableCell
                  key={cell.id}
                  style={{ width: cell.column.getSize() }}
                >
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
