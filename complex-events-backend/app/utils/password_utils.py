"""密码工具模块

使用 Flask-Bcrypt 进行密码哈希和校验。
数据库中 users 表的密码字段将使用 bcrypt 格式存储。

注意：check_password 额外支持 scrypt 格式（Django 兼容），
用于兼容旧系统中使用 scrypt 哈希的用户密码。
"""

import base64

import scrypt as _scrypt

from app.extension import bcrypt


def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希（新注册用户使用此格式）"""
    return bcrypt.generate_password_hash(password).decode("utf-8")


def _check_scrypt(password: str, hashed: str) -> bool:
    """校验 scrypt 格式密码（Django 格式: scrypt:N:r:p$salt$hash）

    注：Django 的 salt 以原始字符串形式存储，直接作为 scrypt salt 输入，
        hash 部分则是 base64 编码后的 scrypt 输出。
    """
    try:
        parts = hashed.split("$", 2)
        if len(parts) != 3:
            return False
        param_str, salt_str, hash_b64 = parts
        params = param_str.split(":")
        N = int(params[1])
        r = int(params[2])
        p = int(params[3])

        # Django 存储的 salt 是原始字符串，直接 encode 为 UTF-8 字节使用
        salt_bytes = salt_str.encode("utf-8")

        # hash 部分需 base64 解码
        padding = 4 - len(hash_b64) % 4
        if padding != 4:
            hash_b64 += "=" * padding
        expected = base64.b64decode(hash_b64)

        actual = _scrypt.hash(
            password.encode("utf-8"),
            salt_bytes,
            N=N,
            r=r,
            p=p,
            buflen=len(expected),
        )
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
