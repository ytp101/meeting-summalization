import { fetchMeetingSummaries } from '@/app/action'
// import MeetingSummaries from '@/components/meetingSummariesComponents'
import ResizableTable from '@/components/ResizableTable'

export default async function ViewSummaries() {
  const summaries = await fetchMeetingSummaries()

  return (
    <div className="pt-10">
      <ResizableTable data={summaries} />
    </div>
  )
}
