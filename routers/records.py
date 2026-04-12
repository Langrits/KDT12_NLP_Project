# routers/records.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import supabase

router = APIRouter()


class RecordIn(BaseModel):
    date: str
    cards: list
    nlp_result: dict | None = None
    fortune: str | None = None
    summary: str | None = None
    condition: str | None = None
    tasks: list[str] | None = None
    advice: str | None = None
    advice_summary: str | None = None
    completed_tasks: list[str] | None = None
    incomplete_tasks: list[str] | None = None
    retrospective: str | None = None
    retro_summary: str | None = None


@router.post("", response_model=dict)
def save_record(record: RecordIn):
    data = record.model_dump()
    result = supabase.table("daily_records").upsert(data, on_conflict="date").execute()
    row = result.data[0]
    return {"id": row.get("id"), "date": row.get("date")}


@router.get("", response_model=list)
def get_records(year: int, month: int):
    start = f"{year:04d}-{month:02d}-01"
    if month == 12:
        end = f"{year + 1:04d}-01-01"
    else:
        end = f"{year:04d}-{month + 1:02d}-01"
    result = (
        supabase.table("daily_records")
        .select("date,summary,cards,nlp_result,retro_summary")
        .gte("date", start)
        .lt("date", end)
        .order("date", desc=True)
        .execute()
    )
    return result.data


@router.get("/{date}", response_model=dict)
def get_record(date: str):
    try:
        result = (
            supabase.table("daily_records")
            .select("*")
            .eq("date", date)
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(404, f"{date} 기록 없음")
    if not result.data:
        raise HTTPException(404, f"{date} 기록 없음")
    return result.data
