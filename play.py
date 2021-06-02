import os
from pathlib import Path

import re
import random
import torch

from getconfig import settings
from storymanager import Story
from utils import *
from gpt3generator import GPT3Generator


def get_generator():
    generator = GPT3Generator(model_path="model")
    return generator


def load_prompt(f, frmat=True):
    with f.open('r', encoding="utf-8") as file:
        lines = file.read().strip().split('\n')
        if len(lines) < 2:
            context = lines[0]
            prompt = ""
        else:
            context = lines[0]
            prompt = ' '.join(lines[1:])
        if frmat:
            return format_result(context), format_result(prompt)
        return context, prompt


def new_story(generator, context, prompt, memory=None):
    if memory is None:
        memory = []
    context = context.strip()
    prompt = prompt.strip()
    
    story = Story(generator, context, memory)
    story.act(prompt)

    story.print_story()
    return story


def save_story(story, file_override=None, autosave=False):
    if not file_override:
        savefile = story.savefile
        while True:
            print()
            tmp_file = input_line("Включено автосохранение. Пожалуйста, введите название файла для сохранения: ", "query")
            savefile = savefile if not tmp_file or len(tmp_file.strip()) == 0 else tmp_file
            if not savefile or len(savefile.strip()) == 0:
                output("Пожалуйста, введите корректное название файла для сохранения.", "error")
            else:
                break
    else:
        savefile = file_override
    savefile = os.path.splitext(savefile.strip())[0]
    savefile = re.sub(r"^ *saves *[/\\] *(.*) *(?:\.json)?", "\\1", savefile).strip()
    story.savefile = savefile
    savedata = story.to_json()
    finalpath = "saves/" + savefile + ".json"
    os.makedirs(os.path.dirname(finalpath), exist_ok=True)
    
    with open(finalpath, 'w') as f:
        f.write(savedata)
        if not autosave:
            output("Успешно сохранено: " + savefile, "message")


def load_story(f, gen):
    with f.open('r', encoding="utf-8") as file:
        story = Story(gen, "")
        savefile = os.path.splitext(file.name.strip())[0]
        savefile = re.sub(r"^ *saves *[/\\] *(.*) *(?:\.json)?", "\\1", savefile).strip()
        story.savefile = savefile
        story.from_json(file.read())
        return story, story.context, story.actions[-1] if len(story.actions) > 0 else ""


def instructions():
    print()
    print("***Инструкция:***")
    print("Существуют следующие команды: \n")
    print('    "/save"           Сохранение игры')
    print('    "/help"           Вывести эту инструкцию еще раз')
    print()
    
    
def print_intro():
    print()
    
    with open(Path("interface", "title.txt"), "r", encoding="utf-8") as f:
        output(f.read())
    
    with open(Path("interface", "start.txt"), "r", encoding="utf-8") as f:
        output(f.read(), wrap=False)


class GameManager:
    def __init__(self, gen: GPT3Generator):
        self.generator = gen
        self.story, self.context, self.prompt = None, None, None
    
    
    def init_story(self):
        self.story, self.context, self.prompt = None, None, None
        list_items(["Выбрать стартовый сюжет",
                    "Загрузить сохраненую игру"],
                   "menu")
        new_game_op = input_number(2)
        
        if new_game_op == 0:
            prompt_file = select_file(Path("prompts"), ".txt")
            if prompt_file:
                self.context, self.prompt = load_prompt(prompt_file)
            else:
                return False
        elif new_game_op == 1:
            story_file = select_file(Path("saves"), ".json")
            if story_file:
                self.story, self.context, self.prompt = load_story(story_file, self.generator)
            else:
                return False
        
        if self.story is None:
            save_file = ""
            if settings.getboolean("autosave"):
                while True:
                    save_file = input_line("Включено автосохранение. Пожалуйста, введите название файла для сохранения: ", "query")
                    if not save_file or len(save_file.strip()) == 0:
                        output("Пожалуйста, введите корректное название файла для сохранения.", "error")
                    else:
                        break
            instructions()
            output("Создаём историю...", "loading-message")
            self.story = new_story(self.generator, self.context, self.prompt)
            self.story.savefile = save_file
        else:
            instructions()
            output("Загружаем историю...", "loading-message")
            self.story.print_story()
        
        if settings.getboolean("autosave"):
            save_story(self.story, file_override=self.story.savefile, autosave=True)
        
        return True
    
    def process_command(self, cmd_regex):
        command = cmd_regex.group(1).strip().lower()
        output(f"Применение команды: /{command} ...", "loading-message")
        if command == "save":
            save_story(self.story, file_override=self.story.savefile)
        elif command == "help":
            instructions()
        else:
            output(f"Неизвестная команда: /{command}", "error")
        return False
        
    
    def process_action(self, action):
        action = format_input(action)
        
        if action != "":
            
            result = self.story.act(action)
            output(result, "ai-text")

    
    
    def play_story(self):
        
        if not self.init_story():
            return
        
        while True:
            print()
            action = input_line("Продолжение истории > ", "main-prompt")
            
            cmd_regex = re.search(r"^(?: *вы *)?/([^ ]+) *(.*)$", action, flags=re.I)
            
            if cmd_regex:
                if self.process_command(cmd_regex):
                    return
            else:
                if self.process_action(action):
                    return
        
        if settings.getboolean("autosave"):
            save_story(self.story, file_override=self.story.savefile, autosave=True)
        

if __name__ == "__main__":
    try:
        gm = GameManager(get_generator())
        while True:
            torch.cuda.empty_cache()
            print_intro()
            gm.play_story()
    except Exception:
        print(Exception.text())
        exit(1)

