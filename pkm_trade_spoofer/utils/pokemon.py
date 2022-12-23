_POKE_TEXT_OFS = 0x3F
_POKE_TEXT_TERMINATOR = 0x50
_POKE_TEXT_MAX_LEN = 10


def pokestr_to_python_str(bs: bytearray) -> str:
    return "".join(
        chr(b - _POKE_TEXT_OFS) for b in bs[: bs.index(_POKE_TEXT_TERMINATOR)]
    )


def python_text_to_pokestr(s: str) -> bytes:
    if len(s) > _POKE_TEXT_MAX_LEN:
        raise Exception(
            f"Pokemon strings have a maximum length of {_POKE_TEXT_MAX_LEN}",
        )

    ps = [0] * (_POKE_TEXT_MAX_LEN + 1)
    for i, c in enumerate(s):
        ps[i] = ord(c) + _POKE_TEXT_OFS
    ps[len(s)] = _POKE_TEXT_TERMINATOR

    return bytes(ps)
