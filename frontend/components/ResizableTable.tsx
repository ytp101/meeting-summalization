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
      accessorKey: 'source_filename',
      header: 'Source Filename',
    },
    {
      accessorKey: 'source_path',
      header: 'Source Path',
    },
    {
      accessorKey: 'wav_path',
      header: 'WAV Path',
    },
    {
      accessorKey: 'transcript_path',
      header: 'Transcript Path',
    },
    {
      accessorKey: 'summary_path',
      header: 'Summary Path',
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
