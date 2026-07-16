import asyncio

import pytest
from tortoise.exceptions import IntegrityError, MultipleObjectsReturned

from goosebit.db.models import Hardware


@pytest.mark.asyncio
async def test_hardware_model_revision_is_unique(db: None) -> None:
    # the schema must enforce the constraint get_or_create relies on
    await Hardware.create(model="default", revision="default")

    with pytest.raises(IntegrityError):
        await Hardware.create(model="default", revision="default")

    # a differing revision (or model) is still allowed
    await Hardware.create(model="default", revision="other")
    assert await Hardware.filter(model="default").count() == 2


@pytest.mark.asyncio
async def test_hardware_get_or_create_is_idempotent(db: None) -> None:
    hw1, created1 = await Hardware.get_or_create(model="board", revision="rev1")
    assert created1 is True

    hw2, created2 = await Hardware.get_or_create(model="board", revision="rev1")
    assert created2 is False
    assert hw2.id == hw1.id

    # one row per pair, so MultipleObjectsReturned can no longer happen
    assert await Hardware.filter(model="board", revision="rev1").count() == 1
    try:
        await Hardware.get_or_create(model="board", revision="rev1")
    except MultipleObjectsReturned:  # pragma: no cover - regression guard
        pytest.fail("get_or_create raised MultipleObjectsReturned for a unique pair")


@pytest.mark.asyncio
async def test_hardware_get_or_create_concurrent(db: None) -> None:
    # overlapping get_or_create calls must converge on one row
    results = await asyncio.gather(
        Hardware.get_or_create(model="race", revision="rev"),
        Hardware.get_or_create(model="race", revision="rev"),
    )
    ids = {hw.id for hw, _ in results}
    assert len(ids) == 1
    assert await Hardware.filter(model="race", revision="rev").count() == 1
