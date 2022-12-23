import functools
import struct
from dataclasses import dataclass

from pkm_trade_spoofer import utils

POKE_TEXT_MAX_LEN = 10
POKEMON_N_BYTES = 48
MAX_PARTY_POKEMON = 6

Bytes = list[int] | bytearray

_ifb_fn = functools.partial(int.from_bytes, byteorder="big")


@dataclass
class PP:
    pp_ups: int
    current_pps: int

    @classmethod
    def from_byte(cls, b: int) -> "PP":
        return cls(
            pp_ups=b >> 6 & 0x3,
            current_pps=b & 0x3F,
        )


@dataclass
class EVs:
    hp: int
    attack: int
    defense: int
    speed: int
    special: int

    @classmethod
    def parse_ivs(cls, bs: Bytes) -> "EVs":
        # Attack, Defense, Speed, and Special.
        iv_repr = _ifb_fn(bs)
        return cls(
            hp=0,
            attack=iv_repr & 0xF,
            defense=iv_repr >> 4 & 0xF,
            speed=iv_repr >> 8 & 0xF,
            special=iv_repr >> 12 & 0xF,
        )

    @classmethod
    def parse_evs(cls, bs: Bytes) -> "EVs":
        return cls(
            hp=_ifb_fn(_pop_n(bs, 2)),
            attack=_ifb_fn(_pop_n(bs, 2)),
            defense=_ifb_fn(_pop_n(bs, 2)),
            speed=_ifb_fn(_pop_n(bs, 2)),
            special=_ifb_fn(_pop_n(bs, 2)),
        )


@dataclass
class Stats:
    max_hp: int
    hp: int
    attack: int
    defense: int
    speed: int
    special_attack: int
    special_defense: int

    @classmethod
    def parse_bytes(cls, bs: Bytes) -> "Stats":
        return cls(
            max_hp=_ifb_fn(_pop_n(bs, 2)),
            hp=_ifb_fn(_pop_n(bs, 2)),
            attack=_ifb_fn(_pop_n(bs, 2)),
            defense=_ifb_fn(_pop_n(bs, 2)),
            speed=_ifb_fn(_pop_n(bs, 2)),
            special_attack=_ifb_fn(_pop_n(bs, 2)),
            special_defense=_ifb_fn(_pop_n(bs, 2)),
        )


# Generation 2 pokemon binary protocol:
# https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_data_structure_(Generation_II)
@dataclass
class Pokemon:
    dex_id: int
    item_held_id: int
    moves_ids: list[int]
    moves_pps: list[PP]
    OT: int
    exp_points: int
    evs: EVs
    ivs: EVs
    friendship_remaining_egg_cycles: int
    pokerus: int  # TODO: Figure out pokerus values
    caught_data: int
    level: int
    status_cond: int
    stats: Stats

    @classmethod
    def from_bytes(cls, bs: list[int] | bytearray) -> "Pokemon":
        return cls(
            dex_id=bs.pop(0),
            item_held_id=bs.pop(0),
            moves_ids=_pop_n(bs, 4),
            OT=_ifb_fn(_pop_n(bs, 2)),
            exp_points=_ifb_fn(_pop_n(bs, 3)),
            evs=EVs.parse_evs(_pop_n(bs, 10)),
            ivs=EVs.parse_ivs(_pop_n(bs, 2)),
            moves_pps=[PP.from_byte(o) for o in _pop_n(bs, 4)],
            friendship_remaining_egg_cycles=bs.pop(0),
            pokerus=bs.pop(0),
            caught_data=_ifb_fn(_pop_n(bs, 2)),
            level=bs.pop(0),
            status_cond=_pop_n(bs, 2)[0],  # remove unused byte too
            stats=Stats.parse_bytes(bs),
        )

    def to_bytes(self) -> bytes:
        padding = [0] * (4 - len(self.moves_ids))
        padded_moves = self.moves_ids + padding

        ivs = 0
        ivs |= self.ivs.attack
        ivs |= self.ivs.defense << 4
        ivs |= self.ivs.speed << 8
        ivs |= self.ivs.special << 12
        ivs &= 0xFFFF

        moves_pps = [
            (pp.pp_ups << 6 | pp.current_pps) & 0xFF if pp else 0
            for pp in self.moves_pps
        ] + padding

        return struct.pack(
            ">6BH3B6H6BH3B7H",
            self.dex_id,
            self.item_held_id,
            *padded_moves,
            self.OT,
            (self.exp_points >> 16) & 0xFF,
            (self.exp_points >> 8) & 0xFF,
            self.exp_points & 0xFF,
            self.evs.hp,
            self.evs.attack,
            self.evs.defense,
            self.evs.speed,
            self.evs.special,
            ivs,
            *moves_pps,
            self.friendship_remaining_egg_cycles,
            self.pokerus,
            self.caught_data,
            self.level,
            self.status_cond,
            0,
            self.stats.hp,
            self.stats.max_hp,
            self.stats.attack,
            self.stats.defense,
            self.stats.speed,
            self.stats.special_attack,
            self.stats.special_defense,
        )


# Party protocol:
# https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_data_structure_(Generation_I)
PARTY_N_BYTES = (
    (POKE_TEXT_MAX_LEN + 1)
    + 10
    + POKEMON_N_BYTES * MAX_PARTY_POKEMON
    + (POKE_TEXT_MAX_LEN + 1) * MAX_PARTY_POKEMON * 2
)


@dataclass
class Party:
    trainer_name: str
    pokemon: list[Pokemon]
    ots_names: list[str]
    pokemon_nicknames: list[str]

    @classmethod
    def from_bytes(cls, bs: Bytes) -> "Party":
        name = utils.pokemon.pokestr_to_python_str(
            bytearray(_pop_n(bs, POKE_TEXT_MAX_LEN + 1)),
        )
        n_pokes = bs.pop(0)
        _pop_n(bs, 9)  # Skip pokes ids and 2 unused bytes

        pokemon = [
            Pokemon.from_bytes(bytearray(_pop_n(bs, POKEMON_N_BYTES)))
            for _ in range(n_pokes)
        ]
        _pop_n(bs, (MAX_PARTY_POKEMON - n_pokes) * POKEMON_N_BYTES)

        ots_names = _parse_strs(bs, n_pokes, MAX_PARTY_POKEMON)
        pokemon_names = _parse_strs(bs, n_pokes, MAX_PARTY_POKEMON)

        return cls(
            trainer_name=name,
            pokemon=pokemon,
            ots_names=ots_names,
            pokemon_nicknames=pokemon_names,
        )

    def serialize(self) -> bytearray:
        n_pokemon_pad = MAX_PARTY_POKEMON - len(self.pokemon)
        dex_ids = [p.dex_id for p in self.pokemon]
        dex_ids.extend([0xFF] * (n_pokemon_pad + 1))

        party_header = struct.pack(
            ">11BB9B",
            *utils.pokemon.python_text_to_pokestr(self.trainer_name),
            len(self.pokemon),
            *dex_ids,
            0xF3,
            0x74,
        )
        serialized_pokemon = b"".join(p.to_bytes() for p in self.pokemon)
        serialized_pokemon += b"\0" * POKEMON_N_BYTES * n_pokemon_pad
        pkm_names = _serialize_strs(self.pokemon_nicknames, MAX_PARTY_POKEMON)
        ot_names = _serialize_strs(self.ots_names, MAX_PARTY_POKEMON)

        return bytearray(party_header + serialized_pokemon + ot_names + pkm_names)


def _parse_strs(bs: Bytes, actual_elements: int, max_elements: int) -> list[str]:
    names = [
        utils.pokemon.pokestr_to_python_str(
            bytearray(_pop_n(bs, POKE_TEXT_MAX_LEN + 1)),
        )
        for _ in range(actual_elements)
    ]
    _pop_n(bs, (max_elements - actual_elements) * (POKE_TEXT_MAX_LEN + 1))
    return names


def _serialize_strs(strs: list[str], max_elements: int) -> bytes:
    serialized_pkm_names = b"".join(
        utils.pokemon.python_text_to_pokestr(o) for o in strs
    )
    pad = max_elements - len(strs)
    serialized_pkm_names += b"\0" * (POKE_TEXT_MAX_LEN + 1) * pad
    return serialized_pkm_names


def _pop_n(bs: list[int] | bytearray, n: int = 2) -> list[int]:
    return [bs.pop(0) for _ in range(n)]
