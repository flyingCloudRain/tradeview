# GitHub Secrets 快速配置

## 一键复制配置

访问：https://github.com/flyingCloudRain/tradeview/settings/secrets/actions

### 方式 1: 使用自定义登录密钥（推荐）

#### Secret 1: CLOUDBASE_ENV_ID
```
trade-view-0gtiozig72c07cd0
```

#### Secret 2: CLOUDBASE_PRIVATE_KEY_ID
```
c1dfb226-e002-4060-aa0f-13ca168f00b2
```

#### Secret 3: CLOUDBASE_PRIVATE_KEY
```
-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQDUQraX/oPn4haiTRgtM4u1Sy0SgPf+8tTnwU5OoGl+AwLt8oie
eBxGzpVV74wyKUg8PrRXKftEeia6k3FaPJjymjZC+bE1idryrp988jl0qvVXDjVl
Sq47gkLXVis7/rdzoFbxlwB72SZG8rV/KSpL42WYkmrpNS5kM2XLg8aSjQIDAQAB
AoGATrcu388TO7ssiaPtg1XKScFHRcVuMq37JrcZQy9Z79FOFNAMujfwxJF38BaV
90Q39Z+LYYfAFvT1x9tF/iDa1vBUOHdMuV4AMpaclpD6O88u3lvD6XbIB6Ay2lnv
0Xy3fQlrxID+vBA+PKYMY4e9DTH58QDwNq1+LI6qybG1NEECQQDp1Fxi6dobex03
jf7oCSl562gSjYM8XGH+OOq3gFgP/BP4MjnfJnElX5IsiEXURW2pWsiYVJppXR6K
QBTQZ8RbAkEA6GLRvPsW5OuKZYy4CllH4+hAxwzHULSgS/nNeabkz8vJfDt9xvxI
5rudo96WUVlFjArH8Pk9diby8eAwwTOZNwJATMGaBhovr3+tapQhDfgb9lqREi4D
22eT/0idu9jUj4K2521NU/QhhhwmNpoRGgokYkhbuq1i9p1LriQ08OhvKwJBAIOW
YVl3fLFHxuhV1GjXwWOGQhf0XnCOty4OV5GJNYuMw5y7Oy+P79/nYQ5HniqWOFFi
UXFcULc0uuDHqBPemeUCQQDeyMoIZSi4VqkG/AUYBoS4CclIqLHsjW4C4zdyi79q
z4QEOpPFfweylVkagSX5RYUC6Ey8Q3PppPhktck7sxIT
-----END RSA PRIVATE KEY-----
```

### 方式 2: 使用腾讯云 API 密钥（备用方案）

如果自定义密钥不可用，可以使用以下密钥：

#### Secret 1: CLOUDBASE_ENV_ID
```
trade-view-0gtiozig72c07cd0
```

#### Secret 2: TCB_SECRET_ID
```
YOUR_TENCENT_CLOUD_SECRET_ID
```

#### Secret 3: TCB_SECRET_KEY
```
YOUR_TENCENT_CLOUD_SECRET_KEY
```

## 配置步骤

1. 点击 **New repository secret**
2. 输入 Secret 名称（如 `CLOUDBASE_ENV_ID`）
3. 粘贴对应的值
4. 点击 **Add secret**
5. 重复以上步骤配置其他 Secrets

### 数据库迁移配置（可选但推荐）

#### Secret: DATABASE_URL
```
postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

**示例**:
```
postgresql://postgres:your_password@db.uvtmbjgndhcmlupridss.supabase.co:5432/postgres
```

**注意**: 
- 将 `[YOUR-PASSWORD]` 替换为实际的数据库密码
- 将 `[YOUR-PROJECT-REF]` 替换为 Supabase 项目引用
- 如果未配置，部署时会跳过数据库迁移步骤

## 验证配置

配置完成后，推送代码测试：

```bash
git push origin main
```

然后在 Actions 页面查看部署状态：
https://github.com/flyingCloudRain/tradeview/actions
