"""
Faster-Whisper Streaming STT — WebSocket server.

Drop-in streaming replacement for Deepgram's live transcription API.
Accepts binary PCM16 audio over WebSocket, returns transcription results
in a Deepgram-compatible JSON format so the Omi backend needs minimal changes.

Protocol:
  Client → Server  binary frames  (PCM16, 16 kHz, mono)
  Server → Client  JSON frames    {type, channel: {alternatives: [{transcript, words}]}}
  Client → Server  text "close"   graceful shutdown

Environment:
  MODEL_SIZE      tiny / base / small / medium / large-v3  (default: base)
  DEVICE          cpu / cuda                               (default: cpu)
  COMPUTE_TYPE    int8 / float16 / float32                 (default: int8)
  SAMPLE_RATE     audio sample rate expected from client   (default: 16000)
  FLUSH_SECS      seconds of audio to accumulate per chunk (default: 1.5)
  SILENCE_SECS    seconds of silence to trigger a flush    (default: 0.3)
"""

import asyncio
import io
import json
import logging
import os
import wave
from collections import deque
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from faster_whisper import WhisperModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_SIZE = os.getenv('MODEL_SIZE', 'base')
DEVICE = os.getenv('DEVICE', 'cpu')
COMPUTE_TYPE = os.getenv('COMPUTE_TYPE', 'int8')
MODEL_DIR = os.getenv('MODEL_DIR', '/models')
SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', '16000'))
FLUSH_SECS = float(os.getenv('FLUSH_SECS', '1.5'))
SILENCE_SECS = float(os.getenv('SILENCE_SECS', '0.3'))

BYTES_PER_SAMPLE = 2  # PCM16
FLUSH_BYTES = int(FLUSH_SECS * SAMPLE_RATE * BYTES_PER_SAMPLE)
SILENCE_BYTES = int(SILENCE_SECS * SAMPLE_RATE * BYTES_PER_SAMPLE)

logger.info(f'Loading Whisper model={MODEL_SIZE} device={DEVICE} compute={COMPUTE_TYPE}')
_model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE, download_root=MODEL_DIR)
logger.info('Whisper model loaded — WS STT service ready.')

app = FastAPI(title='Faster-Whisper Streaming STT', version='1.0.0')


# ---------------------------------------------------------------------------
# Deepgram-compatible response builder
# ---------------------------------------------------------------------------

def _build_response(transcript: str, words: List[dict], is_final: bool = True) -> str:
    """Build a Deepgram-compatible JSON response."""
    return json.dumps(
        {
            'type': 'Results',
            'is_final': is_final,
            'speech_final': is_final,
            'channel': {
                'alternatives': [
                    {
                        'transcript': transcript,
                        'confidence': 0.99,
                        'words': words,
                    }
                ]
            },
        }
    )


# ---------------------------------------------------------------------------
# PCM → WAV helper
# ---------------------------------------------------------------------------

def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Transcribe helper (sync, run in executor)
# ---------------------------------------------------------------------------

def _transcribe_pcm(pcm_bytes: bytes, language: Optional[str] = None) -> List[dict]:
    """Transcribe PCM bytes. Returns list of Deepgram-compatible word dicts."""
    if not pcm_bytes or len(pcm_bytes) < BYTES_PER_SAMPLE * 320:
        return []

    wav_bytes = _pcm_to_wav(pcm_bytes)
    buf = io.BytesIO(wav_bytes)

    segments_iter, info = _model.transcribe(
        buf,
        language=language,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={'min_silence_duration_ms': 200},
    )

    words = []
    for seg in segments_iter:
        if seg.words:
            for w in seg.words:
                words.append(
                    {
                        'word': w.word.strip(),
                        'punctuated_word': w.word.strip(),
                        'start': round(w.start, 3),
                        'end': round(w.end, 3),
                        'confidence': round(w.probability, 4),
                        'speaker': 0,
                    }
                )
        else:
            # No word timestamps (shouldn't happen with word_timestamps=True)
            words.append(
                {
                    'word': seg.text.strip(),
                    'punctuated_word': seg.text.strip(),
                    'start': round(seg.start, 3),
                    'end': round(seg.end, 3),
                    'confidence': 0.9,
                    'speaker': 0,
                }
            )

    return words


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.get('/health')
def health():
    return {'status': 'ok', 'model': MODEL_SIZE, 'device': DEVICE}


@app.websocket('/v1/listen')
async def websocket_listen(ws: WebSocket, language: Optional[str] = None):
    """
    Deepgram-compatible streaming STT WebSocket endpoint.

    Query params:
      language  BCP-47 language code (optional, auto-detected if omitted)
    """
    await ws.accept()
    logger.info(f'WS STT: client connected lang={language}')

    loop = asyncio.get_event_loop()
    audio_buffer = bytearray()
    time_offset = 0.0  # running offset of processed audio in seconds
    active = True

    async def flush_buffer(buf: bytearray, final: bool = False) -> float:
        """Transcribe accumulated audio and send results. Returns duration of processed audio."""
        if not buf:
            return 0.0
        pcm_snapshot = bytes(buf)
        duration = len(pcm_snapshot) / (SAMPLE_RATE * BYTES_PER_SAMPLE)

        words = await loop.run_in_executor(None, _transcribe_pcm, pcm_snapshot, language)

        if words:
            transcript = ' '.join(w['punctuated_word'] for w in words)
            # Shift word timestamps by the accumulated time offset
            for w in words:
                w['start'] = round(w['start'] + time_offset, 3)
                w['end'] = round(w['end'] + time_offset, 3)

            response = _build_response(transcript, words, is_final=final)
            try:
                await ws.send_text(response)
            except Exception:
                pass

        return duration

    try:
        while active:
            try:
                # Non-blocking receive with timeout so we can flush on silence
                raw = await asyncio.wait_for(ws.receive(), timeout=FLUSH_SECS)
            except asyncio.TimeoutError:
                # Flush whatever we have on timeout (client went silent)
                if audio_buffer:
                    duration = await flush_buffer(audio_buffer)
                    time_offset += duration
                    audio_buffer.clear()
                continue

            # Text control messages
            if 'text' in raw:
                msg = raw['text']
                if isinstance(msg, str) and msg.lower() in ('close', 'done', 'finish'):
                    logger.info('WS STT: client requested close')
                    break
                continue

            # Binary audio chunk
            if 'bytes' in raw:
                chunk = raw['bytes']
                if chunk:
                    audio_buffer.extend(chunk)

            # Flush when we have enough audio
            if len(audio_buffer) >= FLUSH_BYTES:
                duration = await flush_buffer(audio_buffer)
                time_offset += duration
                audio_buffer.clear()

    except WebSocketDisconnect:
        logger.info('WS STT: client disconnected')
    except Exception as e:
        logger.exception(f'WS STT error: {e}')
    finally:
        # Final flush
        if audio_buffer:
            await flush_buffer(audio_buffer, final=True)
        try:
            await ws.close()
        except Exception:
            pass
        logger.info('WS STT: connection closed')


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
