BASE_URL = "https://www.lazygpt.cn/api"
API_KEY = "lazygpt-B9CzqJP3vbhqH3BF8m0BnMV2A61jdlDaG"
MODEL_SETTINGS = [
        {
            "model": "gpt-3.5-turbo",
            "max_tokens": 8000,
            "token_setting": "gpt-3.5-turbo"
        },
        {
            "model": "gpt-3.5-turbo-16k",
            "max_tokens": 16000,
            "token_setting": "gpt-4"
        },
        {
            "model": "gpt-4",
            "max_tokens": 8000,
            "token_setting": "gpt-4"
        },
        {
            "model": "gpt-4-0125-preview",
            "max_tokens": 128000,
            "token_setting": "gpt-4"
        },
        {
            "model": "gpt-4-vision-preview",
            "max_tokens": 128000,
            "token_setting": "gpt-4"
        }
    ]

TOKEN_SETTINGS = {
        "gpt-3.5-turbo": {
            "tokens_per_message": 4,
            "tokens_per_name": -1
        },
        "gpt-4": {
            "tokens_per_message": 3,
            "tokens_per_name": 1
        }
    }




