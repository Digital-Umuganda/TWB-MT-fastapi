from fastapi import APIRouter, status
from app.views.v1.translate import translator, TranslationRequest, TranslationResponse, fetch_model_data_from_request, translate_text
import re

translate_markdown = APIRouter(prefix='/api/v1/translate_markdown')
def remove_markdown(text):
    """Remove markdown formatting from text."""
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)  # Bold
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)  # Italics
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', text)  # Links
    text = re.sub(r'`(.*?)`', r'\1', text)  # Inline code
    text = re.sub(r'~~(.*?)~~', r'\1', text)  # Strikethrough
    return text

def reapply_markdown(original, modified):
    """Reapply markdown formatting after translation."""
    pattern = r'(\*\*.*?\*\*|\*.*?\*|__.*?__|_.*?_|\[.*?\]\(.*?\)|`.*?`|~~.*?~~)'
    matches = re.finditer(pattern, original)

    result = ""
    cursor = 0

    for match in matches:
        start, end = match.span()
        token = match.group()
        if cursor < start:
            result += modified[cursor:start]
        stripped = remove_markdown(token).strip()
        translated_stripped = translator(stripped)[0]['translation_text']
        result += token.replace(stripped, translated_stripped)
        cursor = end

    if cursor < len(original):
        result += modified[cursor:]
    
    return result



@translate_markdown.post('/markdown', status_code=status.HTTP_200_OK)
async def translate_markdown(request: TranslationRequest) -> TranslationResponse:
    model_id, src, tgt = fetch_model_data_from_request(request)
    
    def process_text(text,model_id,src,tgt):
        """Remove markdown, translate, and reapply markdown formatting."""
        plain_text = remove_markdown(text)
        translated_text = translate_text(model_id,plain_text,src,tgt)

        return reapply_markdown(text, translated_text)

    translated_markdown = process_text(request.text,model_id=model_id,src=src,tgt=tgt)
    return TranslationResponse(translation=translated_markdown)