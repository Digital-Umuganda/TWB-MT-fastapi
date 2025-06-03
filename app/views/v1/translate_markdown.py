from fastapi import APIRouter, status
from app.views.v1.translate import TranslationRequest, TranslationResponse, fetch_model_data_from_request, translate_text
import re

translate_markdown = APIRouter(prefix='/api/v1/translate_markdown')

def remove_markdown(text):
    """Remove markdown formatting from text while preserving positions."""
    segments = []
    current_pos = 0
    
    # Define markdown patterns
    patterns = [
        (r'(\*\*|__)(.*?)\1', 'bold'),  # Bold
        (r'(\*|_)(.*?)\1', 'italic'),  # Italics
        (r'\[(.*?)\]\((.*?)\)', 'link'),  # Links
        (r'`(.*?)`', 'code'),  # Inline code
        (r'~~(.*?)~~', 'strikethrough')  # Strikethrough
    ]
    
    # Find all markdown segments
    all_matches = []
    for pattern, mark_type in patterns:
        for match in re.finditer(pattern, text):
            content = match.group(2) if mark_type != 'link' else match.group(1)
            all_matches.append({
                'start': match.start(),
                'end': match.end(),
                'content': content,
                'original': match.group(0),
                'type': mark_type,
                'url': match.group(2) if mark_type == 'link' else None
            })
    
    # Sort matches by position
    all_matches.sort(key=lambda x: x['start'])
    
    # Split text into markdown and non-markdown segments
    for match in all_matches:
        if current_pos < match['start']:
            # Add non-markdown text segment
            segments.append({
                'type': 'text',
                'content': text[current_pos:match['start']],
                'original': text[current_pos:match['start']]
            })
        segments.append(match)
        current_pos = match['end']
    
    # Add remaining text if any
    if current_pos < len(text):
        segments.append({
            'type': 'text',
            'content': text[current_pos:],
            'original': text[current_pos:]
        })
    
    # Extract plain text for translation
    plain_text = ''.join([seg['content'] for seg in segments])
    
    return plain_text, segments

def reapply_markdown(segments, translated_text):
    """Reapply markdown formatting to translated text while handling different language lengths."""
    result = ""
    translated_segments = []
    current_pos = 0
    
    # Split translated text into segments based on original segment lengths and positions
    for segment in segments:
        # Get the next chunk of translated text
        if segment['type'] == 'text':
            # For non-markdown text, take the next portion of translated text
            translated_content = translated_text[current_pos:current_pos + len(segment['content'])]
            current_pos += len(segment['content'])
            translated_segments.append(translated_content)
        else:
            # For markdown text, translate the content separately to maintain formatting
            translated_content = translate_text(model_id, segment['content'], src, tgt)
            translated_segments.append(translated_content)
    
    # Reconstruct the markdown text
    for i, segment in enumerate(segments):
        if segment['type'] == 'text':
            result += translated_segments[i]
        elif segment['type'] == 'link':
            result += f"[{translated_segments[i]}]({segment['url']})"
        elif segment['type'] == 'bold':
            result += f"**{translated_segments[i]}**"
        elif segment['type'] == 'italic':
            result += f"*{translated_segments[i]}*"
        elif segment['type'] == 'code':
            result += f"`{translated_segments[i]}`"
        elif segment['type'] == 'strikethrough':
            result += f"~~{translated_segments[i]}~~"
    
    return result

@translate_markdown.post('/markdown', status_code=status.HTTP_200_OK)
async def translate_markdown_text(request: TranslationRequest) -> TranslationResponse:
    global model_id, src, tgt
    model_id, src, tgt = fetch_model_data_from_request(request)
    
    # Split text into segments and get plain text
    plain_text, segments = remove_markdown(request.text)
    
    # Translate the main text
    translated_text = translate_text(model_id, plain_text, src, tgt)
    
    # Reapply markdown with proper translations
    translated_markdown = reapply_markdown(segments, translated_text)
    
    return TranslationResponse(translation=translated_markdown)