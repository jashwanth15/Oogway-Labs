import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from backend.app.db.database import Base
from backend.app.db.models import SessionModel, MessageModel, ArtifactModel


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_session_lifecycle_and_cascade(test_db):
    # 1. Create Session
    session = SessionModel(title="Test PMF Session", model_used="ollama:mistral")
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)
    assert session.id is not None

    # 2. Add Messages
    user_msg = MessageModel(
        session_id=session.id,
        role="user",
        content="How do I calculate PMF?"
    )
    test_db.add(user_msg)
    await test_db.commit()
    await test_db.refresh(user_msg)

    asst_msg = MessageModel(
        session_id=session.id,
        role="assistant",
        content="According to Rahul Vohra, ask users how disappointed they would be.",
        citations=[{"guest": "Rahul Vohra", "episode_id": "rahul-vohra"}]
    )
    test_db.add(asst_msg)
    await test_db.commit()
    await test_db.refresh(asst_msg)

    # 3. Add Artifact
    art = ArtifactModel(
        session_id=session.id,
        message_id=asst_msg.id,
        title="PMF Survey Template",
        artifact_type="markdown",
        content="# PMF Survey\nHow disappointed would you be?"
    )
    test_db.add(art)
    await test_db.commit()
    await test_db.refresh(art)

    # 4. Verify associations
    stmt = select(MessageModel).where(MessageModel.session_id == session.id)
    res = await test_db.execute(stmt)
    messages = res.scalars().all()
    assert len(messages) == 2

    stmt_art = select(ArtifactModel).where(ArtifactModel.session_id == session.id)
    res_art = await test_db.execute(stmt_art)
    artifacts = res_art.scalars().all()
    assert len(artifacts) == 1
    assert artifacts[0].title == "PMF Survey Template"

    # 5. Delete Session and verify cascade delete
    await test_db.delete(session)
    await test_db.commit()

    res_post_del = await test_db.execute(stmt)
    assert len(res_post_del.scalars().all()) == 0

    res_art_del = await test_db.execute(stmt_art)
    assert len(res_art_del.scalars().all()) == 0
