#!/usr/bin/env python3
"""
清理舊應用的腳本
這個腳本會刪除已遷移到 crawlers 的舊應用目錄和文件
請在確認遷移成功後運行此腳本
"""

import os
import shutil
import sys

def confirm_deletion():
    """確認是否要執行刪除操作"""
    print("⚠️  警告：此操作將刪除以下目錄和文件：")
    print("   - gov_datas/ 目錄")
    print("   - symptoms/ 目錄")
    print("   - templates/symptoms.html")
    print("   - templates/gov_datas.html")
    print()
    print("請確保：")
    print("1. 數據遷移已成功完成")
    print("2. 新系統運行正常")
    print("3. 已備份重要資料")
    print()
    
    response = input("確定要繼續嗎？[y/N]: ").strip().lower()
    return response in ['y', 'yes']

def remove_directory(path):
    """安全地刪除目錄"""
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
            print(f"✓ 已刪除目錄: {path}")
        except Exception as e:
            print(f"✗ 刪除目錄失敗 {path}: {e}")
    else:
        print(f"○ 目錄不存在: {path}")

def remove_file(path):
    """安全地刪除文件"""
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"✓ 已刪除文件: {path}")
        except Exception as e:
            print(f"✗ 刪除文件失敗 {path}: {e}")
    else:
        print(f"○ 文件不存在: {path}")

def main():
    print("🧹 RAGPilot 舊應用清理工具")
    print("=" * 50)
    
    if not confirm_deletion():
        print("❌ 取消清理操作")
        return
    
    print("\n🗂️  開始清理...")
    
    # 刪除舊的應用目錄
    remove_directory("gov_datas")
    remove_directory("symptoms")
    
    # 刪除舊的模板文件
    remove_file("templates/symptoms.html")
    remove_file("templates/gov_datas.html")
    
    print("\n✅ 清理完成！")
    print()
    print("📝 後續步驟：")
    print("1. 測試所有功能是否正常")
    print("2. 提交 Git 變更")
    print("3. 部署到生產環境")

if __name__ == "__main__":
    main() 