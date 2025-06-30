# Google 登入用戶密碼管理功能

## 📋 問題背景

當用戶通過 Google 登入註冊時，Django 會創建用戶帳號但不會設定密碼。這意味著這些用戶無法使用傳統的 username + 密碼方式登入，只能依賴 Google 登入。

## 🎯 解決方案

我們實現了智能密碼管理功能，可以自動檢測用戶狀態並提供相應的密碼管理選項：

### 🔄 智能檢測機制

系統會自動檢測用戶是否有可用的密碼（使用 `user.has_usable_password()` 方法）：

- **沒有密碼的用戶**（如 Google 登入用戶）：顯示「設定密碼」表單
- **已有密碼的用戶**：顯示「修改密碼」表單

## 🚀 功能特色

### 1. 動態表單選擇
```python
# 在 ProfileView 中自動選擇適當的表單
if has_usable_password:
    password_form = CustomPasswordChangeForm(user=request.user)
    password_form_type = 'change'
else:
    password_form = CustomSetPasswordForm(user=request.user)
    password_form_type = 'set'
```

### 2. 兩種不同的表單

#### 設定密碼表單 (`CustomSetPasswordForm`)
- **適用對象**：Google 登入等社交登入用戶
- **功能**：為沒有密碼的用戶設定初始密碼
- **欄位**：只需要新密碼和確認密碼，無需舊密碼

#### 修改密碼表單 (`CustomPasswordChangeForm`)
- **適用對象**：已有密碼的用戶
- **功能**：修改現有密碼
- **欄位**：需要舊密碼、新密碼和確認新密碼

### 3. 智能用戶介面
- **動態標題**：根據用戶狀態顯示「設定登入密碼」或「修改密碼」
- **說明提示**：為 Google 用戶提供清楚的密碼設定說明
- **狀態指示**：在第三方登入管理頁面顯示當前登入方式狀態

## 💡 用戶體驗

### Google 登入用戶的體驗流程

1. **初次登入**：用戶通過 Google 成功登入
2. **發現提示**：在「第三方登入管理」中看到密碼設定提示
3. **設定密碼**：前往「密碼管理」頁面設定密碼
4. **多重登入**：設定後可以選擇 Google 登入或 username + 密碼登入

### 已有密碼用戶的體驗

1. **正常使用**：可以使用任何已連結的登入方式
2. **密碼管理**：在「密碼管理」頁面修改密碼
3. **狀態清楚**：系統明確顯示可用的登入方式

## 🔧 技術實現

### 1. 表單設計
```python
class CustomSetPasswordForm(SetPasswordForm):
    """設定密碼表單（適用於沒有密碼的用戶）"""
    new_password1 = forms.CharField(
        label='設定密碼',
        help_text='設定密碼後，您可以使用 username + 密碼的方式登入'
    )

class CustomPasswordChangeForm(PasswordChangeForm):
    """修改密碼表單（適用於已有密碼的用戶）"""
    old_password = forms.CharField(label='當前密碼')
```

### 2. 視圖邏輯
```python
def get(self, request):
    # 檢查用戶密碼狀態
    has_usable_password = request.user.has_usable_password()
    
    # 選擇適當的表單
    if has_usable_password:
        password_form = CustomPasswordChangeForm(user=request.user)
        password_form_type = 'change'
    else:
        password_form = CustomSetPasswordForm(user=request.user)
        password_form_type = 'set'
```

### 3. 模板適配
```html
{% if password_form_type == 'set' %}
    <!-- 設定密碼介面 -->
    <h3>設定登入密碼</h3>
    <div class="alert alert-info">
        您目前是通過 Google 登入註冊的用戶...
    </div>
{% else %}
    <!-- 修改密碼介面 -->
    <h3>修改密碼</h3>
{% endif %}
```

## 📊 狀態追蹤

### 用戶狀態檢查方法

```python
# 檢查用戶是否有可用密碼
user.has_usable_password()

# 可能的狀態：
# True: 用戶有密碼，可以使用 username + 密碼登入
# False: 用戶沒有密碼，只能使用社交登入
```

### 在模板中的應用

```html
{% if not has_usable_password %}
    <p>您目前是 Google 用戶，若需要使用 username + 密碼登入，請到「密碼管理」設定密碼</p>
{% else %}
    <p>您已設定密碼，可以使用 {{ user.username }} + 密碼的方式登入</p>
{% endif %}
```

## 🔐 安全性考量

### 1. 會話管理
```python
# 設定或修改密碼後，更新會話避免用戶被登出
update_session_auth_hash(request, user)
```

### 2. 表單驗證
- 使用 Django 內建的密碼驗證器
- 確保密碼強度符合要求
- 防止 CSRF 攻擊

### 3. 用戶通知
- 成功設定密碼後顯示確認訊息
- 告知用戶新的登入方式選項

## 🎉 使用場景

### 場景 1：新的 Google 用戶
```
用戶通過 Google 註冊 → 系統創建無密碼帳號 → 用戶可選擇設定密碼 → 支援雙重登入方式
```

### 場景 2：現有用戶連結 Google
```
用戶有密碼帳號 → 連結 Google 帳號 → 可選擇任一方式登入 → 可在密碼管理中修改密碼
```

### 場景 3：忘記密碼的 Google 用戶
```
Google 用戶忘記是否設定過密碼 → 系統自動檢測 → 顯示適當的管理介面
```

## 📝 使用說明

### 對於 Google 登入用戶

1. **登入系統**：使用 Google 帳號登入
2. **進入個人資料**：點擊右上角個人資料連結
3. **密碼管理**：切換到「密碼管理」標籤
4. **設定密碼**：填寫新密碼和確認密碼
5. **確認設定**：點擊「設定密碼」按鈕
6. **成功提示**：看到成功訊息後，即可使用 username + 密碼登入

### 對於已有密碼的用戶

1. **登入系統**：使用任何可用的登入方式
2. **進入個人資料**：點擊右上角個人資料連結
3. **密碼管理**：切換到「密碼管理」標籤
4. **修改密碼**：輸入舊密碼和新密碼
5. **確認修改**：點擊「儲存修改」按鈕

## ✅ 最佳實踐

1. **用戶引導**：在第三方登入管理頁面提供清楚的說明
2. **狀態透明**：讓用戶明確知道自己的登入選項
3. **安全提醒**：設定密碼後提醒用戶記住新的登入方式
4. **彈性選擇**：用戶可以選擇只使用 Google 登入或設定密碼支援雙重方式

---

這個功能完美解決了 Google 登入用戶無法使用 username + 密碼登入的問題，同時保持了良好的用戶體驗和系統安全性。 