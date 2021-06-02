import re
import json

from getconfig import settings
from utils import output, format_result, format_input

class Story:
    
    def __init__(self, generator, context='', memory=None):
        if memory is None:
            memory = []
        self.generator = generator
        self.context = context
        self.memory = memory
        self.actions = []
        self.results = []
        self.savefile = ''
        
        
    def act(self, action, record=True, format=True):
        result = self.generator.generate(
            self.get_story() + action,
            self.context + ' '.join(self.memory)
        )
        if record:
            self.actions.append(format_input(action))
            self.results.append(format_input(result))
        return format_result(result) if format else result
    
    
    def print_action_result(self, i, wrap=True, color=True):
        col1 = 'user-text' if color else None
        col2 = 'ai-text' if color else None
        if i == 0 or len(self.actions) == 1:
            start = format_result(self.context + ' ' + self.actions[0])
            result = format_result(self.results[0])
            is_start_end = re.match(r"[.!?]\s*$", start)  # if start ends logically
            is_result_continue = re.match(r"^\s*[a-z.!?,\"]", result)  # if result is a continuation
            sep = ' ' if not is_start_end and is_result_continue else '\n'
            if not self.actions[0]:
                output(self.context, col1, self.results[0], col2, sep=sep)
            else:
                output(self.context, col1)
                output(self.actions[0], col1, self.results[0], col2, sep=sep)
        else:
            if i < len(self.actions) and self.actions[i].strip() != "":
                caret = "> " if re.match(r"^ *you +", self.actions[i], flags=re.I) else ""
                output(format_result(caret + self.actions[i]), col1, wrap=wrap)
            if i < len(self.results) and self.results[i].strip() != "":
                output(format_result(self.results[i]), col2, wrap=wrap)
    
    
    def print_story(self, wrap=True, color=True):
        for i in range(0, max(len(self.actions), len(self.results))):
            self.print_action_result(i, wrap=wrap, color=color)
    
    
    def __str__(self):
        return self.context + ' ' + self.get_story()
    
    
    def get_story(self):
        lines = [val for pair in zip(self.actions, self.results) for val in pair]
        return '\n\n'.join(lines)
    
    
    def from_json(self, j):
        d = json.loads(j)
        settings["temp"] = str(d["temp"])
        settings["top-p"] = str(d["top-p"])
        settings["top-k"] = str(d["top-k"])
        settings["rep-pen"] = str(d["rep-pen"])
        self.context = d["context"]
        self.memory = d["memory"]
        self.actions = d["actions"]
        self.results = d["results"]
        
        
    def to_json(self):
        d = {}
        d["temp"] = settings.getfloat('temp')
        d["top-p"] = settings.getfloat("top-p")
        d["top-k"] = settings.getint("top-k")
        d["rep-pen"] = settings.getfloat("rep-pen")
        d["context"] = self.context
        d["memory"] = self.memory
        d["actions"] = self.actions
        d["results"] = self.results
        return json.dumps(d)