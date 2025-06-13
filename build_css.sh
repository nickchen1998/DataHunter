#!/bin/bash

echo "🎨 正在建構 Tailwind CSS..."

# 建構生產版本的 CSS
npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify

echo "✅ CSS 建構完成！"
echo "📁 輸出檔案：static/css/output.css"
echo ""
echo "💡 如果您想要監控檔案變更，請執行："
echo "   ./build_css.sh --watch"

if [ "$1" == "--watch" ]; then
    echo ""
    echo "👀 開始監控檔案變更..."
    npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch
fi 