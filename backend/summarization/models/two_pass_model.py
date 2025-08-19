from pydantic import BaseModel, Field 
from typing import List, Optional, Literal, Dict, Any

class WordSpan(BaseModel): 
    w: str = Field(..., description="word text")
    start_ms: int 
    end_ms: int 
    conf: Optional[float] = None 

class Participant(BaseModel):
    id: str 
    name: Optional[str] = None 
    role: Optional[str] = None 

class Utterance(BaseModel): 
    id: Optional[str] = None 
    speaker: str 
    start_ms: Optional[int] = None 
    end_ms: Optional[int] = None 
    text: str 
    words: Optional[List[WordSpan]] = None 

class MeetingDoc(BaseModel): 
    meeting_id: str 
    meta: Dict[str, Any] = Field(default_factory=dict)
    participants: Optional[List[Participant]] = None
    utterances: List[Utterance]

class ChunkSummary(BaseModel):
    window_index: int
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    summary: str
    decisions: List[str] = Field(default_factory=list)
    action_items: List[Dict[str, Any]] = Field(default_factory=list)

class FinalSummary(BaseModel):
    meeting_id: str
    model_pass1: str
    model_pass2: str
    executive_summary: str
    decisions: List[str]
    action_items: List[Dict[str, Any]]
    provenance: Dict[str, Any] = Field(default_factory=dict)