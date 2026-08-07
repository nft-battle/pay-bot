def esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fmt_money(amount: float, asset: str = "USDT") -> str:
    return f"{amount:,.2f} {asset}".replace(",", " ")


def user_ref(username: str, user_id: int) -> str:
    if username:
        return f"@{esc(username)}"
    return f"<code>{user_id}</code>"