import asyncio

from faker import Faker
from faker.providers import company

import goosebit
from goosebit.db.models import (
    Device,
    Hardware,
    Rollout,
    Software,
    UpdateModeEnum,
    UpdateStateEnum,
)

fake = Faker()
fake.add_provider(company)


async def generate_sample_data() -> None:
    await Rollout.all().delete()
    await Device.all().delete()
    await Software.all().delete()
    await Hardware.all().delete()

    hardware1 = await Hardware.create(model="router", revision="1.1")
    hardware2a = await Hardware.create(model="ap", revision="1.0")
    hardware2b = await Hardware.create(model="ap", revision="2.0")

    software_for_hw1 = []
    software_for_hw2 = []

    versions = ["0.12.0", "0.1.0", "1.0.1", "1.0.0-alpha2", "1.0.0-rc1", "1.0.0-rc12", "10.0.0", "1.0.0"]
    for version in versions:
        size = fake.random_int(min=100000, max=1000000)
        software = await Software.create(version=version, hash=fake.sha1(), size=size, uri=fake.uri())
        await software.compatibility.add(hardware1)
        software_for_hw1.append(software)

    versions = [
        "0.1.0",
        "0.3.0",
        "0.2.0",
        "0.4.0",
    ]
    for version in versions:
        size = fake.random_int(min=100000, max=1000000)
        software = await Software.create(version=version, hash=fake.sha1(), size=size, uri=fake.uri())
        await software.compatibility.add(hardware2a)
        await software.compatibility.add(hardware2b)
        software_for_hw2.append(software)

    for i in range(50):
        update_mode = fake.random_element([UpdateModeEnum.ROLLOUT, UpdateModeEnum.LATEST, UpdateModeEnum.ASSIGNED])
        hardware = fake.random_element([hardware1, hardware2a, hardware2b])
        software = (
            fake.random_element(software_for_hw1) if hardware == hardware1 else fake.random_element(software_for_hw2)
        )
        await Device.create(
            id=fake.uuid4(),
            name=fake.bs(),
            feed=fake.random_element(["dev", "qa", "live"]) if update_mode == UpdateModeEnum.ROLLOUT else "",
            last_state=fake.random_element(
                [UpdateStateEnum.REGISTERED, UpdateStateEnum.ERROR, UpdateStateEnum.FINISHED, UpdateStateEnum.RUNNING]
            ),
            update_mode=update_mode,
            hardware=hardware,
            assigned_software=software if update_mode == UpdateModeEnum.ASSIGNED else None,
        )

    for software in software_for_hw1 + software_for_hw2:
        feed = fake.random_element(["dev", "qa", "live"])
        await Rollout.create(name=f"Release {software.version} to {feed}", feed=feed, software_id=software.id)

    print("Sample data created!")


async def run() -> None:
    db_ready = await goosebit.db.init()
    if db_ready:
        await generate_sample_data()
        await goosebit.db.close()
    else:
        print("Failed to initialize database")


def main() -> None:
    asyncio.run(run())
