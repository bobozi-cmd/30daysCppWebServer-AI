from openai import OpenAI
import os
from pathlib import Path
import argparse
from typing import List
import re

# TODO: fill those configs
base_url = ""
api_key = ""
model = "gpt-4o"

client = OpenAI(api_key=api_key, base_url=base_url)

resp = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "hello"}]
)

print(resp.choices[0].message.content)
