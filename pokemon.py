import math
import random
from typing import NamedTuple, Optional, cast

import pokebase as pb

from models import PP, EVs, Pokemon, Stats


class ApiLink(NamedTuple):
    name: str
    url: str


class VersionGroupDetail(NamedTuple):
    level_learned_at: int
    version_group: ApiLink
    move_learn_method: ApiLink


class Move(NamedTuple):
    move: ApiLink
    version_group_details: list[VersionGroupDetail]


class PokeApiStats(NamedTuple):
    base_stat: int
    stat: ApiLink


def pokemon_by_id(
    pokemon_id: int,
    *,
    ivs: EVs,
    item_held_id: Optional[int] = None,
    OT: Optional[int] = None
) -> Pokemon:
    pkm = pb.pokemon(pokemon_id)
    level = 1
    move_ids = [
        _resource_id(m.move)
        for m in pkm.moves
        if _is_valid_move(cast(Move, m), level, 2)
    ][:4]

    stats_dict = _stats_to_dict(pkm.stats)
    for k, v in stats_dict.items():
        if k == "special-attack" or k == "special-defense":
            iv = ivs.special
        else:
            iv = getattr(ivs, k)

        if k == "hp":
            stats_dict[k] = math.floor((((v + iv) * 2) * level) / 100) + level + 10
        else:
            stats_dict[k] = math.floor((((v + iv) * 2) * level) / 100) + 5

    return Pokemon(
        dex_id=pokemon_id,
        item_held_id=item_held_id or 0,
        moves_ids=move_ids,
        moves_pps=[PP(0, current_pps=1)] * len(move_ids),
        evs=EVs(0, 0, 0, 0, 0),
        OT=OT or random.randint(1, 10000),
        exp_points=0,
        ivs=ivs,
        friendship_remaining_egg_cycles=70,
        pokerus=0,
        caught_data=0,
        level=level,
        status_cond=0,
        stats=Stats(
            max_hp=stats_dict["hp"],
            hp=stats_dict["hp"],
            attack=stats_dict["attack"],
            defense=stats_dict["defense"],
            speed=stats_dict["speed"],
            special_attack=stats_dict["special-attack"],
            special_defense=stats_dict["special-defense"],
        ),
    )


def _stats_to_dict(stats: list[PokeApiStats]) -> dict[str, int]:
    return {st.stat.name: st.base_stat for st in stats}


def _is_valid_move(move: Move, current_level: int, gen: int) -> bool:
    try:
        version_info = [
            vg
            for vg in move.version_group_details
            if _resource_id(vg.version_group) <= gen
        ][0]
    except IndexError:
        return False

    return version_info.level_learned_at <= current_level


def _resource_id(api_link: ApiLink) -> int:
    return int(api_link.url.removesuffix("/").split("/")[-1])
