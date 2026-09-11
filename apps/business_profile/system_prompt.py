def render_system_prompt(**kwargs):
    system_prompt_template=f"""
{tag_if_exist(kwargs['system_prompt'], 'system_prompt')}

<response_format>
    text_response...
    ```json
    {{
        "quick_replies": ["...", ...], // optional, use only when needed
    }}
    ```
    # the json block is optional, use when quick replies needed
    # never use json in the response text for tool calls, use actual tool call
</response_format>

{tag_if_exist(kwargs['business_info'], 'business_info')}

{tag_if_exist(kwargs['products'], 'products')}

{tag_if_exist(kwargs['media_files'], 'media_files')}

{tag_if_exist(kwargs['order_fields'], 'order_fields')}

"""
    return system_prompt_template.strip()

def tag_if_exist(text: str, tag: str) -> str:
    if text:
        return f"<{tag}>\n{text}\n</{tag}>"
    return ""