def transform_text_img(prompt: str) -> dict:
    """调用文生图模型"""
    from app.llm.bailian.text_img import bailian_text_img

    return bailian_text_img(prompt=prompt)
