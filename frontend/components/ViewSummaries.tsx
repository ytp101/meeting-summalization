import { fetchMeetingSummaries } from '@/app/action'
import MeetingSummaries from '@/components/meetingSummariesComponents'

export default async function ViewSummaries() {
  const summaries = await fetchMeetingSummaries()

  return (
    <div className="pt-10">
      <MeetingSummaries data={summaries} />
    </div>
  )
}
