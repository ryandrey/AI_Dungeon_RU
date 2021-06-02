import configparser

config = configparser.ConfigParser()
config.read("config.ini")
settings = config["Settings"]

colorschemefile = settings["backup-color-scheme"]
colorconfig = configparser.ConfigParser()
colorconfig.read(colorschemefile)
colors = colorconfig["Colors"]


setting_info = {
    "temp":             ["Higher values make the AI more random.", 0.4],
    "rep-pen":          ["Controls how repetitive the AI is allowed to be.", 1.2],
    "text-wrap-width":  ["Maximum width of lines printed by computer.", 80],
    "console-bell":     ["Beep after AI generates text.", "on"],
    "top-keks":         ["Number of words the AI can randomly choose.", 20],
    "action-sugg":      ["How many actions to generate; 0 is off.", 4],
    "action-d20":       ["Makes actions difficult.", "off"],
    "action-temp":      ["How random the suggested actions are.", 1],
    "prompt-toolkit":   ["Whether or not to use the prompt_toolkit library.", "on"],
    "autosave":         ["Whether or not to save after every action.", "on"],
    "generate-num":     ["Approximate number of words to generate.", 60],
    "top-p":            ["Changes number of words nucleus sampled by the AI.", 0.9],
    "log-level":        ["Development log level. <30 is for developers.", 30],
    "gpt2-sparse":      ["Экспериментальная генерация", "off"],
    "gpt2-sparse-level":["Уровень разреженности", 1.2],
}