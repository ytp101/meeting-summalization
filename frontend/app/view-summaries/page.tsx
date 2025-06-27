import { fetchMeetingSummaries } from '@/app/view-summaries/action';
import MeetingSummaries from '@/components/meetingSummariesComponents';

export default async function viewSummariesPage() {
    const result = await fetchMeetingSummaries();
    return (
        <MeetingSummaries data={result} />
    );
}