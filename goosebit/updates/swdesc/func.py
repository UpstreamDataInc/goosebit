import hashlib

from anyio import AsyncFile


async def sha1_hash_file(fileobj: AsyncFile):
    last = await fileobj.tell()
    await fileobj.seek(0)
    sha1_hash = hashlib.sha1()
    buf = bytearray(2**18)
    view = memoryview(buf)
    while True:
        size = await fileobj.readinto(buf)
        if size == 0:
            break
        sha1_hash.update(view[:size])

    await fileobj.seek(last)
    return sha1_hash.hexdigest()
