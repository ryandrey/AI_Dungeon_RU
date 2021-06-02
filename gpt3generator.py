import os

import torch
import torch.nn.functional as F
import re
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from getconfig import settings
from utils import *

DTYPE = torch.float64 if torch.cuda.is_available() else torch.float32

def getTokens(tokenizer, l):
    tokenizer.encode()

    
def hackyEncode(tokenizer, s):
    return tokenizer.encode('====\n ' + s)[2:]


def hackyWhiteSpaceCutter(prompt):
    return re.search(r'\s*$', prompt).group(0)


def memory_merge(prompt, context, tokenizer, maxHistory=2048):
    prompt_tokens = tokenizer.encode(prompt, add_special_tokens=False, add_prefix_space=True)
    context_tokens = hackyEncode(tokenizer, hackyWhiteSpaceCutter(prompt) + context)
    context_tokens = context_tokens[-(maxHistory - len(prompt_tokens)):]
    
    prompt_tokens.extend(context_tokens)
    context_tokens = prompt_tokens

    if len(context_tokens) > maxHistory:
        context_tokens = context_tokens[-maxHistory:]
    return context_tokens


def top_k_top_p_filtering(logits, top_k=0, top_p=0.0, filter_value=-float("Inf")):

    top_k = min(top_k, logits.size(-1))
    if top_k > 0:
        indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
        logits[indices_to_remove] = filter_value
    if top_p > 0.0:
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

        sorted_indices_to_remove = cumulative_probs > top_p

        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
        sorted_indices_to_remove[..., 0] = 0

        indices_to_remove = sorted_indices_to_remove.scatter(
            dim=-1, index=sorted_indices, src=sorted_indices_to_remove
        )
        logits[indices_to_remove] = filter_value
    return logits


def sample_sequence(
        model,
        length,
        context,
        device="cpu",
        stop_tokens=None,
        tokenizer=None
):
    top_k = settings.getint("top-k")
    top_p = settings.getfloat("top-p")
    temperature = settings.getfloat("temp")
    repetition_penalty = settings.getfloat("rep-pen")
    
    context_tokens = context
    context = torch.tensor(context, dtype=torch.long, device=device)

    generated = context
    next_token = context
    past = None

    clines = 0
    with torch.no_grad():
        for j in range(length):
            input_ids_next = next_token

            output = model(input_ids=input_ids_next, past_key_values=past)
            logits, past = output.logits, output.past_key_values
            logits = logits[-1, :].float()

            if settings.getboolean('top-p-first'):
                logits = top_k_top_p_filtering(logits, top_k=top_k, top_p=top_p)

            logits = logits / (temperature if temperature > 0 else 1.0)

            for k in set(generated.tolist()):
                logits[k] /= repetition_penalty
            
            if not settings.getboolean('top-p-first'):
                logits = top_k_top_p_filtering(logits, top_k=top_k, top_p=top_p)

            if temperature == 0:
                next_token = torch.argmax(logits, dim=-1).unsqueeze(-1)
            else:
                next_token = torch.multinomial(
                    F.softmax(logits, dim=-1), num_samples=1
                )
            generated = torch.cat((generated, next_token), dim=-1)

            o = generated[len(context_tokens):].tolist()
            generated.text = tokenizer.decode(
                o, clean_up_tokenization_spaces=False, skip_special_tokens=True
            )
    return generated

class GPT3Generator:
    
    def __init__(self, model_path=""):
        self.generate_num = settings.getint("generate-num")
        self.max_history_tokens = 2048 - self.generate_num
        self.stop_token = "<|endoftext|>"
        
        self.device = torch.device("cuda" if DTYPE == torch.float64 else "cpu")
        
        self.tokenizer = GPT2Tokenizer.from_pretrained(model_path)
        self.model = GPT2LMHeadModel.from_pretrained(model_path)
        self.model.to(DTYPE).to(self.device)
        self.model.eval()
        
        
    def sample_sequence(self, context_tokens=None, generate_num=None, stop_tokens=None):
        out = sample_sequence(
            model=self.model,
            context=context_tokens,
            length=generate_num,
            device=self.device,
            stop_tokens=stop_tokens,
            tokenizer=self.tokenizer)
        return out
    
    
    def result_replace(self, result, allow_action=False):
        if len(result) == 0:
            return ""
        first_letter_capitalized = result[0].isupper()
        result = result.replace('."', '".')
        result = result.replace("#", "")
        result = result.replace("*", "")

        result = result.replace("\n\n", "\n")

        if not first_letter_capitalized:
            result = result[0].lower() + result[1:]

        return result
    
    
    def generate_raw(self, context, prompt='', stop_tokens=None):
        
        context_tokens = memory_merge(prompt, context, self.tokenizer, self.max_history_tokens)
        
        out = self.sample_sequence(
            context_tokens,
            generate_num=self.generate_num,
            stop_tokens=stop_tokens,
        )
        text = out.text

        if self.stop_token:
            index = text.find(self.stop_token)
            if index == -1:
                index = None
            text = text[:index]
        if stop_tokens is not None:
            for stop_token in stop_tokens:
                index = text.find(self.stop_token)
                if index == -1:
                    index = None
                text = text[:index]
        return text
        
    
    def generate(self, context, prompt='', depth=0):
        
        text = self.generate_raw(context, prompt, stop_tokens=self.tokenizer.encode([">"]))
        
        result = self.result_replace(text)
        
        if depth > 6 and len(result) == 0:
            pass
        if len(result) == 0:
            if depth < 20:
                return self.generate(context, prompt, depth=depth + 1)
            else:
                pass

        return result
