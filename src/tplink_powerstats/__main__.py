import asyncio
import contextlib

from .main import main

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
with contextlib.suppress(KeyboardInterrupt):
    asyncio.run(main())
