import { MeetingSummary } from '@/types/meetingSummaries';
import { pool } from '@/utils/psqlClient';

export async function fetchMeetingSummaries(): Promise<MeetingSummary[]> {
  const result = await pool.query(
    'SELECT * FROM meeting_summaries ORDER BY created_at DESC'
  );

  return result.rows.map((row) => ({
    ...row,
    created_at: new Date(row.created_at).toISOString(), // Ensure created_at is in ISO format
  }));
}