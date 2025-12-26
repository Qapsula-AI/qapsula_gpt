#!/bin/bash
# deploy.sh - простой деплой
echo "🚀 Deploying to Qapsula server..."

# Копируем только измененные файлы
scp app.py root@176.114.67.32:/root/qapsula_gpt/

# Перезапускаем бота
ssh root@176.114.67.32 "cd /root/qapsula_gpt && sudo systemctl restart qapsula-bot.service"

echo "✅ Bot updated!"