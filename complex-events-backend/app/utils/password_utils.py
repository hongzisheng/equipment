"""密码工具模块

使用 Flask-Bcrypt 进行密码哈希和校验。
数据库中 users 表的密码字段将使用 bcrypt 格式存储。

注意：check_password 额外支持 scrypt 格式（Django 兼容），
用于兼容旧系统中使用 scrypt 哈希的用户密码。
"""

import base64
import hashlib

from app.extension import bcrypt


def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希（新注册用户使用此格式）"""
    return bcrypt.generate_password_hash(password).decode("utf-8")


def _check_scrypt(password: str, hashed: str) -> bool:
    """校验 scrypt 格式密码（Django 格式: scrypt:N:r:p$salt$hash）"""
    try:
        parts = hashed.split("$", 2)
        if len(parts) != 3:
            return False
        param_str, salt_b64, hash_b64 = parts
        params = param_str.split(":")
        N = int(params[1])
        r = int(params[2])
        p = int(params[3])

        def b64_decode(s: str) -> bytes:
            padding = 4 - len(s) % 4
            if padding != 4:
                s += "=" * padding
            return base64.b64decode(s)

        salt = b64_decode(salt_b64)
        expected = b64_decode(hash_b64)
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=N, r=r, p=p)
        return actual == expected
    except Exception:
        return False


def check_password(password: str, hashed: str) -> bool:
    """校验明文密码与哈希是否匹配（支持 bcrypt 和 scrypt 格式）"""
    # 1. 先尝试 bcrypt
    try:
        return bcrypt.check_password_hash(hashed, password)
    except ValueError:
        pass

    # 2. 再尝试 scrypt（兼容旧数据）
    if hashed.startswith("scrypt:"):
        return _check_scrypt(password, hashed)

    return False
