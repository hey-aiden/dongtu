from app.llm import bailian_text_audio


def transform_text_audio(prompt: str) -> str:
    audio_url = bailian_text_audio(prompt=prompt)
    return {"audio_url": audio_url}
