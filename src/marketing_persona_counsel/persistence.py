from pathlib import Path
from local_first_common.db import CONTENT_QUALITY_DB_PATH
from sqlmodel import Session, SQLModel, create_engine, select
from .models import CouncilResult, EvaluationRecord

DEFAULT_DB_PATH = CONTENT_QUALITY_DB_PATH


def get_engine(db_path: Path = DEFAULT_DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    sqlite_url = f"sqlite:///{db_path}"
    engine = create_engine(sqlite_url)
    SQLModel.metadata.create_all(engine)
    return engine


def save_council_result(result: CouncilResult, db_path: Path = DEFAULT_DB_PATH):
    engine = get_engine(db_path)
    with Session(engine) as session:
        for p_eval in result.evaluations:
            record = EvaluationRecord(
                timestamp=result.timestamp,
                source_title=result.source_title,
                source_location=result.source_location,
                persona_name=p_eval.persona_name,
                sentiment=p_eval.sentiment,
                interest_score=p_eval.interest_score,
                engagement_score=p_eval.engagement_score,
                friendliness_score=p_eval.friendliness_score,
                shareability_score=p_eval.shareability_score,
                outstanding_questions="\n".join(p_eval.outstanding_questions),
                tips_to_improve="\n".join(p_eval.tips_to_improve),
                narrative=p_eval.narrative,
            )
            session.add(record)
        session.commit()


def get_history(source_location: str, db_path: Path = DEFAULT_DB_PATH) -> list[EvaluationRecord]:
    engine = get_engine(db_path)
    with Session(engine) as session:
        statement = select(EvaluationRecord).where(EvaluationRecord.source_location == source_location)
        return list(session.exec(statement).all())
