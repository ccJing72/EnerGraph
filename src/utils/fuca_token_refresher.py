"""fuca_token_refresher — 福加平台 API Token 自动刷新工具

所属层：utils
依赖：httpx, pycryptodome (Crypto.PublicKey.RSA, Crypto.Cipher.PKCS1_v1_5)
对接算法层：N/A（对接福加 EMP Admin 认证 API）

认证流程（逆向自 aiot-fuca.com 前端）：
  1. RSA 加密密码（512-bit PKCS1v15，公钥嵌入前端 encrypt.76f0cfe5.js）
  2. POST /emp-admin/auth/account — 登录
  3. GET  /emp-admin/auth/account/mb/token?loginName=xxx&tenantId=yyy — 获取 Token

用法:
  - 作为库调用: from src.utils.fuca_token_refresher import refresh_token
  - 作为 CLI:   python -m src.utils.fuca_token_refresher
"""
import base64
import logging
import os
import re
from pathlib import Path
from typing import Optional

import httpx
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

logger = logging.getLogger(__name__)

# ── 常量 ──────────────────────────────────────────────────────────

# 福加前端 RSA 公钥（DER base64, 512-bit, exponent 65537）
# 来源: aiot-fuca.com/assets/encrypt.76f0cfe5.js
_FUCA_RSA_PUBLIC_KEY_B64 = (
    "MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAM51dgYtMyF+tTQt"
    "80sfFOpSV27a7t9uaUVeFrdGiVxscuizE7H8SMntYqfn9lp8"
    "a5GH5P1/GGehVjUD2gF/4kcCAwEAAQ=="
)

_DEFAULT_BASE_URL = "https://aiot-fuca.com"
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _PROJECT_ROOT / ".env"


# ── 核心函数 ──────────────────────────────────────────────────────


def _encrypt_password(plaintext: str, public_key_b64: str = _FUCA_RSA_PUBLIC_KEY_B64) -> str:
    """使用福加前端 RSA 公钥加密密码（PKCS1v15 padding）。

    Args:
        plaintext: 明文密码
        public_key_b64: DER 编码的 RSA 公钥 base64 字符串

    Returns:
        base64 编码的密文
    """
    der_bytes = base64.b64decode(public_key_b64)
    key = RSA.import_key(der_bytes)
    cipher = PKCS1_v1_5.new(key)
    encrypted = cipher.encrypt(plaintext.encode("utf-8"))
    return base64.b64encode(encrypted).decode("ascii")


def _login(base_url: str, login_name: str, encrypted_password: str) -> dict:
    """调用福加登录 API。

    Args:
        base_url: API 基础 URL
        login_name: 登录账号
        encrypted_password: RSA 加密后的密码

    Returns:
        登录响应 data 字段

    Raises:
        RuntimeError: 登录失败时
    """
    resp = httpx.post(
        f"{base_url}/emp-admin/auth/account",
        json={"loginName": login_name, "password": encrypted_password},
        timeout=15,
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("code") != 200:
        raise RuntimeError(f"登录失败: {body.get('message', '未知错误')}")
    data = body.get("data", {})
    if not data.get("success"):
        raise RuntimeError("登录返回 success=false")
    return data


def _fetch_token(base_url: str, login_name: str, tenant_id: str) -> str:
    """获取 API Token（登录后调用 mb/token 接口）。

    Args:
        base_url: API 基础 URL
        login_name: 登录账号
        tenant_id: 租户 ID

    Returns:
        新的 token 字符串

    Raises:
        RuntimeError: 获取 token 失败时
    """
    resp = httpx.get(
        f"{base_url}/emp-admin/auth/account/mb/token",
        params={"loginName": login_name, "tenantId": tenant_id},
        headers={"tenant_id": tenant_id},
        timeout=15,
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("code") != 200:
        raise RuntimeError(f"获取 Token 失败: {body.get('message', '未知错误')}")
    token = body.get("data", {}).get("token")
    if not token:
        raise RuntimeError("Token 为空")
    return token


def _update_env_file(token: str) -> None:
    """更新 .env 文件中的 FUCA_API_TOKEN 字段。

    如果字段已存在则替换值，不存在则在文件末尾追加。

    Args:
        token: 新的 token 值
    """
    if not _ENV_FILE.exists():
        logger.warning(".env 文件不存在，跳过写入")
        return

    content = _ENV_FILE.read_text(encoding="utf-8")
    pattern = re.compile(r"^FUCA_API_TOKEN=.*$", re.MULTILINE)

    if pattern.search(content):
        new_content = pattern.sub(f"FUCA_API_TOKEN={token}", content)
    else:
        # 追加到文件末尾
        if not content.endswith("\n"):
            content += "\n"
        new_content = content + f"FUCA_API_TOKEN={token}\n"

    _ENV_FILE.write_text(new_content, encoding="utf-8")
    logger.info(f".env 中 FUCA_API_TOKEN 已更新 (token 长度: {len(token)})")


def refresh_token(
    login_name: Optional[str] = None,
    password: Optional[str] = None,
    tenant_id: Optional[str] = None,
    base_url: Optional[str] = None,
    update_env: bool = True,
) -> str:
    """刷新福加 API Token（登录 → 获取 token → 更新 .env）。

    参数优先使用显式传入值，否则从环境变量读取。

    Args:
        login_name: 福加平台登录账号（默认读取 FUCA_LOGIN_NAME 环境变量）
        password: 福加平台明文密码（默认读取 FUCA_PASSWORD 环境变量）
        tenant_id: 租户 ID（默认读取 FUCA_TENANT_ID 环境变量）
        base_url: API 基础 URL（默认读取 FUCA_API_BASE_URL 环境变量）
        update_env: 是否将新 token 写入 .env 文件（默认 True）

    Returns:
        新的 token 字符串

    Raises:
        ValueError: 缺少必要配置时
        RuntimeError: API 调用失败时
    """
    login_name = login_name or os.getenv("FUCA_LOGIN_NAME")
    password = password or os.getenv("FUCA_PASSWORD")
    tenant_id = tenant_id or os.getenv("FUCA_TENANT_ID")
    base_url = base_url or os.getenv("FUCA_API_BASE_URL", _DEFAULT_BASE_URL)

    if not login_name:
        raise ValueError("缺少 FUCA_LOGIN_NAME（登录账号），请在 .env 中配置")
    if not password:
        raise ValueError("缺少 FUCA_PASSWORD（登录密码），请在 .env 中配置")
    if not tenant_id:
        raise ValueError("缺少 FUCA_TENANT_ID（租户 ID），请在 .env 中配置")

    logger.info(f"开始刷新福加 Token: 账号={login_name}, 租户={tenant_id}")

    # Step 1: RSA 加密密码
    encrypted_pwd = _encrypt_password(password)
    logger.debug("密码已 RSA 加密")

    # Step 2: 登录
    _login(base_url, login_name, encrypted_pwd)
    logger.info("登录成功")

    # Step 3: 获取 Token
    new_token = _fetch_token(base_url, login_name, tenant_id)
    logger.info(f"Token 获取成功 (长度: {len(new_token)})")

    # Step 4: 更新 .env 文件
    if update_env:
        _update_env_file(new_token)

    # Step 5: 更新当前进程的 os.environ（立即生效，无需重启）
    os.environ["FUCA_API_TOKEN"] = new_token

    return new_token


# ── CLI 入口 ──────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # CLI 模式下确保 .env 已加载
    from dotenv import load_dotenv
    if _ENV_FILE.exists():
        load_dotenv(_ENV_FILE)

    try:
        token = refresh_token()
        print(f"\n✅ Token 刷新成功!")
        print(f"   新 Token: {token[:20]}...{token[-10:]}")
        print(f"   .env 文件已更新")
    except Exception as e:
        print(f"\n❌ Token 刷新失败: {e}")
        raise SystemExit(1)
