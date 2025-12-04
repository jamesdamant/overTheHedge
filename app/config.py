import configparser

config = configparser.ConfigParser()
config.read("config.ini")

def get_config(section, key):
    return config[section][key]