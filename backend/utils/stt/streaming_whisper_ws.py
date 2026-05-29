import asyncio
import json
import os
from typing import Callable, Optional

import websockets

from utils.stt.vad_gate import GatedDeepgramSocket
import logging

logger = logging.getLogger(__name__)

_FASTER_WHISPER_WS_URL = os.getenv('FASTER_WHISPER_WS_URL')


class _WhisperWSSocket:
    """Drop-in replacement for SafeDeepgramSocket backed by Faster-Whisper WS.

    Implements the same send/finish/finalize/is_connection_dead interface so that
    transcribe.py can use it without modification.
    """

    _is_safe_dg_socket = True  # Duck-type marker (matches SafeDeepgramSocket)

    def __init__(self, ws_url: str, stream_transcript_fn):
        self._ws_url = ws_url
        self._stream_transcript = stream_transcript_fn
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._closed = False
        self._dead = False
        self._death_reason: Optional[str] = None
        self._task: Optional[asyncio.Task] = None

    async def _run(self):
        try:
            async with websockets.connect(self._ws_url, ping_interval=20, ping_timeout=20) as ws:

                async def _sender():
                    while not self._closed:
                        try:
                            data = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                        except asyncio.TimeoutError:
                            continue
                        if data is None:
                            break
                        try:
                            await ws.send(data)
                        except Exception as e:
                            logger.warning(f'WhisperWS send error: {e}')
                            self._dead = True
                            self._death_reason = f'send {type(e).__name__}: {e}'
                            break

                async def _receiver():
                    while not self._closed:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                        except asyncio.TimeoutError:
                            continue
                        except Exception as e:
                            if not self._closed:
                                logger.warning(f'WhisperWS recv error: {e}')
                                self._dead = True
                                self._death_reason = f'recv {type(e).__name__}: {e}'
                            break
                        self._handle_message(msg)

                await asyncio.gather(_sender(), _receiver(), return_exceptions=True)

        except Exception as e:
            if not self._closed:
                logger.error(f'WhisperWSSocket connection error: {e}')
                self._dead = True
                self._death_reason = f'connect {type(e).__name__}: {e}'

    def _handle_message(self, msg: str):
        try:
            data = json.loads(msg)
            alts = data.get('channel', {}).get('alternatives', [])
            if not alts:
                return
            words = alts[0].get('words', [])
            if not words:
                return

            segments = []
            for word in words:
                speaker_label = f"SPEAKER_{word.get('speaker', 0)}"
                text = word.get('punctuated_word') or word.get('word', '')
                if not text:
                    continue
                if not segments or segments[-1]['speaker'] != speaker_label:
                    segments.append({'speaker': speaker_label, 'start': word['start'], 'end': word['end'], 'text': text, 'is_user': False, 'person_id': None})
                else:
                    last = segments[-1]
                    last['text'] += f' {text}'
                    last['end'] = word['end']

            if segments:
                self._stream_transcript(segments)

        except Exception as e:
            logger.warning(f'WhisperWS message parse error: {e}')

    @property
    def is_connection_dead(self) -> bool:
        return self._dead

    @property
    def death_reason(self) -> Optional[str]:
        return self._death_reason

    def send(self, data: bytes) -> None:
        if self._closed or self._dead:
            return
        try:
            self._queue.put_nowait(data)
        except asyncio.QueueFull:
            logger.warning('WhisperWS audio queue full — dropping chunk')

    def finalize(self) -> None:
        pass  # Faster-Whisper flushes automatically on silence/timeout

    def finish(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._queue.put_nowait(None)
        except asyncio.QueueFull:
            pass
        if self._task and not self._task.done():
            self._task.cancel()

    def set_close_reason(self, reason: str) -> None:
        if self._death_reason is None:
            self._death_reason = reason


async def process_audio_whisper_ws(
    stream_transcript,
    language: str,
    sample_rate: int,
    channels: int,
    vad_gate=None,
    is_active: Optional[Callable[[], bool]] = None,
):
    """Create a Faster-Whisper streaming WebSocket connection.

    Drop-in replacement for process_audio_dg when DEEPGRAM_API_KEY is absent
    and FASTER_WHISPER_WS_URL is configured.
    """
    base_url = (_FASTER_WHISPER_WS_URL or 'ws://faster-whisper-ws:8002').rstrip('/')
    lang_param = f'?language={language}' if language and language != 'auto' else ''
    ws_url = f'{base_url}/v1/listen{lang_param}'

    if vad_gate is not None:
        _original = stream_transcript

        def stream_transcript(segments):
            vad_gate.remap_segments(segments)
            _original(segments)

    socket = _WhisperWSSocket(ws_url, stream_transcript)
    loop = asyncio.get_event_loop()
    socket._task = loop.create_task(socket._run())

    logger.info(f'process_audio_whisper_ws: connected to {ws_url}')

    if vad_gate is not None:
        return GatedDeepgramSocket(socket, gate=vad_gate)
    return socket
