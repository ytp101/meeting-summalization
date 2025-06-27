export interface MeetingSummary {
  id: number;
  task_id: string;
  source_file: string;
  wav_file: string;
  transcript_file: string;
  created_at: string; // ISO timestamp (e.g., "2024-06-26T09:15:30Z")
}
