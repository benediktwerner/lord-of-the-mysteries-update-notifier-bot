- Telegram Bot API: https://core.telegram.org/bots/api
- Getting Telegram Bot updates: `curl 'https://api.telegram.org/bot$BOT_KEY/getUpdates'`
- https://docs.aws.amazon.com/lambda/latest/dg/python-package.html

## Deployment

- Dependencies layer
  - `pip install --target ./python -r requirements.txt`
  - `zip -r dependencies-layer.zip python`
- Function
  - `zip deployment.zip lambda_function.py`
