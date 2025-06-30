export interface MeetingSummary {
  id: number;
  source_filename: string;
  source_path: string;
  wav_path: string;
  transcript_path: string;
  summary_path: string;
  created_at: string; // ISO timestamp (e.g., "2024-06-26T09:15:30Z")
}