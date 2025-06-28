import random
from aiogram.types import ReactionTypeUnion, ReactionTypeEmoji
from typing_extensions import Literal


def get_reaction_by_level(is_positive: bool = True, level: Literal[1] = 1) -> ReactionTypeUnion | None:
    if is_positive and level == 1:
        emoji = random.choice(['🔥', '👏', '🎉', '💯'])
        return ReactionTypeEmoji(emoji=emoji)