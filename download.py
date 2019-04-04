import aiohttp
import asyncio


async def download_data(data, workers=10):
    downloader = Downloader(data, workers=workers)
    await downloader.run()


class Downloader:
    def __init__(self, data, workers=10):
        self._data = data
        self._loop = asyncio.get_event_loop()
        self._lock = asyncio.Semaphore(workers)
        self._processed = 0
        self._processing = 0
        self._total = len(data)
        self._session = None

    def _printProgress(self):
        print('\r{}/{} - {}'.format(self._processed, self._total, self._processing), end='\r')

    def _sync_writer(self, file_path, content):
        with open(file_path, 'wb') as f:
            f.write(content)

    async def _write_to_file(self, dest, content):
        self._loop.run_in_executor(
            None, self._sync_writer, dest, content)

    async def _process(self, url, dest):
        self._processing += 1
        self._printProgress()

        async with self._session.get(url) as response:
            await self._write_to_file(dest, await response.read())

        self._processing -= 1
        self._processed += 1
        self._printProgress()

    async def run(self):
        async with aiohttp.ClientSession() as session:
            self._session = session
            coroutines = []
            for url, dest in self._data.items():
                async with self._lock:
                    coroutines.append(self._process(url, dest))
            await asyncio.gather(*coroutines)


