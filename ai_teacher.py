from openai import OpenAI
import os
from pathlib import Path
import argparse
from typing import List
import re
import time
import json

# TODO: fill those configs
base_url = ""
api_key = ""
model = "gpt-4o"

# global var
current_dir = Path(os.path.dirname(__file__))

class ContentManager:
    sys_template = """You are an Cpp Teacher, You need to teach student to learn web server's principle and implement.
The content of teaching is divided into many days, I will give you today's teaching content and code examples list.
You must follow the teaching content and guide students step by step in exploring knowledge. Don't tell students everything at once.
You can assume that the student **has learned all the pre-knowledge**, and if he does not know anything, he will ask you directly.
You should interact with students in a question and answer method and keep your answers concise.

Today's Teaching Task:
{task}

Today's Code Examples Lists:
{code_files}

##Output Format
```
Thoughts: ...
Action: None or code file selected from Code Examples Lists
```

Note:
- Students cannot see the sample code. You need to teach students step by step based on these examples and the tasks for the day.
- Thoughts is the content you want to teach.
- Your Language in Thoughts is {language}, But Action must be English.

"""

    def __init__(self, sday: str, language: str = "chinese") -> None:
        self.sday = sday
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.messages = []
        self.code_path = current_dir / "code" / sday
        self.language = language
        
        self._prepare_sys_prompt()

    def chat(self, content: str, role: str="user") -> str:
        self.messages.append({"role": role, "content": content})

        resp = self.client.chat.completions.create(
            model=model,
            messages=self.messages
        )

        resp_content = resp.choices[0].message.content
        self.messages.append({"role": "assistant", "content": resp_content})

        pattern = r'Thoughts:\s*(.*?)\nAction:\s*(.*)'
        match = re.search(pattern, resp_content.replace('```', ''), re.DOTALL)

        if match:
            thoughts = match.group(1).strip()
            action = match.group(2).strip()
            if 'None' not in action:
                print(f"Thinking...\n{thoughts}")
                print(f"Open {action}")
                code = self._get_code(action)
                return self.chat(content=f"The example code of {action}(Do not tell students you have example codes):\n```cpp{code}\n```", role="system")
        else:
            print(resp_content)
            raise RuntimeError("Cannot match the response")

        return thoughts
    

    def _get_code(self, file: str):
        if file in self.code_files:
            with open(os.path.join(self.code_path, file), "r") as fp:
                return fp.read()
        raise RuntimeError(f"Connot find {file}")

    def _prepare_sys_prompt(self):
        self.task = ""
        for file in os.listdir(current_dir):
            if file.endswith(".md") and file.startswith(self.sday):
                print(f"Found the task file: {file}")
                with open(file, "r") as fp:
                    self.task = fp.read()
        
        if self.task == "":
            raise RuntimeError(f"Connot Find the file with {self.sday} or the file has no content.")

        self.code_files: List[str] = []
        for root, dirs, files in os.walk(self.code_path):
            for file in files:
                if Path(file).suffix in [".cpp", ".hpp", ".c", ".h", ".cc", ".hh"]:
                    self.code_files.append(str(Path(os.path.join(root, file)).relative_to(self.code_path)))

        sys_prompt = self.sys_template.format(language=self.language, task=self.task, code_files=self.code_files)
        self.messages.append({"role": "system", "content": sys_prompt})

    def save(self):
        with open(f"history_{int(time.time())}.log", "w", encoding="utf-8") as fp:
            json.dump(self.messages, fp=fp, indent=4, ensure_ascii=False,)


def run(day: int):
    sday = f"day{day:02}"
    content_manager = ContentManager(sday=sday)
    step = 0

    try:
        while True:
            step += 1
            print("=" * 40, step, "=" * 40)
            content = input("please input your question(`q` to quit)>\n")
            while content == "":
                content = input("please input your question(`q` to quit)>\n")
            if content.lower() == 'q':
                break
            print()
            resp = content_manager.chat(content)
            print(f"Teacher:\n{resp}\n")
    finally:
        content_manager.save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--day", type=int, required=True, help="The day number of learning")
    args = parser.parse_args()

    run(day=args.day)


if __name__ == "__main__":
    main()
