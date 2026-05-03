"""
Faster-Whisper STT service.

Drop-in replacement for Deepgram batch transcription.
Exposes a single POST /transcribe endpoint that returns TranscriptSegment-compatible JSON.

Environment:
  MODEL_SIZE      whisper model (tiny / base / small / medium / large-v3)  default: base
  DEVICE          cpu or cuda                                               default: cpu
  COMPUTE_TYPE    int8 / float16 / float32                                  default: int8
"""

import io
import logging
import os
import tempfile
import wave
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from faster_whisper import WhisperModel
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_SIZE = os.getenv('MODEL_SIZE', 'base')
DEVICE = os.getenv('DEVICE', 'cpu')
COMPUTE_TYPE = os.getenv('COMPUTE_TYPE', 'int8')
MODEL_DIR = os.getenv('MODEL_DIR', '/models')

logger.info(f'Loading Whisper model={MODEL_SIZE} device={DEVICE} compute={COMPUTE_TYPE}')
_model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE, download_root=MODEL_DIR)
logger.info('Whisper model loaded.')

app = FastAPI(title='Faster-Whisper STT', version='1.0.0')


class Word(BaseModel):
    word: str
    start: float
    end: float
    probability: float


class Segment(BaseModel):
    id: int
    text: str
    start: float
    end: float
    words: List[Word]
    speaker: Optional[str] = None


class TranscribeResponse(BaseModel):
    segments: List[Segment]
    language: str
    duration: float


@app.get('/health')
def health():
    return {'status': 'ok', 'model': MODEL_SIZE, 'device': DEVICE}


@app.post('/transcribe', response_model=TranscribeResponse)
async def transcribe(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    word_timestamps: bool = Form(True),
):
    """
    Transcribe an audio file.

    Returns segments compatible with omi TranscriptSegment format.
    Accepts WAV, MP3, OGG, OPUS, WEBM — any format FFmpeg handles.
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail='Empty audio file')

    # Write to a temp file — faster_whisper needs a path or numpy array
    suffix = os.path.splitext(file.filename or '.wav')[1] or '.wav'
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments_iter, info = _model.transcribe(
            tmp_path,
            language=language,
            word_timestamps=word_timestamps,
            vad_filter=True,
            vad_parameters={'min_silence_duration_ms': 300},
        )

        out_segments: List[Segment] = []
        for i, seg in enumerate(segments_iter):
            words = []
            if word_timestamps and seg.words:
                words = [
                    Word(
                        word=w.word,
                        start=round(w.start, 3),
                        end=round(w.end, 3),
                        probability=round(w.probability, 4),
                    )
                    for w in seg.words
                ]
            out_segments.append(
                Segment(
                    id=i,
                    text=seg.text.strip(),
                    start=round(seg.start, 3),
                    end=round(seg.end, 3),
                    words=words,
                )
            )

        return TranscribeResponse(
            segments=out_segments,
            language=info.language,
            duration=round(info.duration, 3),
        )
    finally:
        os.unlink(tmp_path)


@app.post('/transcribe/stream')
async def transcribe_stream(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
):
    """Lightweight endpoint returning only text (no word timestamps). Faster for real-time use."""
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail='Empty audio file')

    suffix = os.path.splitext(file.filename or '.wav')[1] or '.wav'
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments_iter, info = _model.transcribe(
            tmp_path,
            language=language,
            word_timestamps=False,
            vad_filter=True,
        )
        text = ' '.join(seg.text.strip() for seg in segments_iter)
        return {'text': text, 'language': info.language}
    finally:
        os.unlink(tmp_path)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8001)
