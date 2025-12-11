#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')

from app.api.v1.endpoints.render import enhance_prompt_for_video

async def test():
    test_prompts = [
        'a ball is dancing',
        'hello world',
        'create something',
        'learn coding',
        'never give up'
    ]

    print("Testing prompt enhancement:")
    print("=" * 50)

    for prompt in test_prompts:
        enhanced = await enhance_prompt_for_video(prompt)
        print(f'Original: "{prompt}"')
        print(f'Enhanced: "{enhanced}"')
        print('---')

if __name__ == "__main__":
    asyncio.run(test())