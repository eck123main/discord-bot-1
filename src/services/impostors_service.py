from custom_types.discord import MemberId

from random import sample

from custom_types.impostors import GameId

from defaults.paths import WORDS_PATH

import json
import random


class Game:
    def __init__(
        self,
        game_id: GameId,
        members: list[MemberId],
        num_impostors: int,
        category: str | None,
    ):
        self._game_id = game_id
        self._members = list(set(members))
        self._category = "unknown" if not category else category.lower()

        # Assert this will be a valid game
        if not num_impostors <= len(self._members):
            raise AssertionError(
                "Number of impostors cannot be less than number of members!"
            )

        # Separate impostors and normals
        self._impostors = sample(members, num_impostors)
        self._normals: list[MemberId] = [
            member_id for member_id in self._members if member_id not in self._impostors
        ]

        # Determine the secret word
        self._word: str
        with open(WORDS_PATH) as f:
            words: dict[str, list[str]] = json.load(f)

        if self._category == "unknown":
            self._category = random.choice(list(words.keys()))

        elif self._category not in words:
            raise AssertionError("Category is not in the word bank.")

        self._word = random.choice(words[self._category])

    @property
    def game_id(self) -> GameId:
        return self._game_id

    @property
    def members(self) -> list[MemberId]:
        return self._members

    @property
    def category(self) -> str:
        return self._category

    @property
    def impostors(self) -> list[MemberId]:
        return self._impostors

    @property
    def normals(self) -> list[MemberId]:
        return self._normals

    def check_impostor(self, member_id: MemberId) -> bool:
        return member_id in self.impostors

    def check_normal(self, member_id: MemberId) -> bool:
        return member_id in self.normals

    def get_initial_message(self, member_id: MemberId) -> str:
        if self.check_normal(member_id):
            return f"Normal! Word: {self._word}"

        if self.check_impostor(member_id):
            return f"Impostor! Category: {self.category}"

        raise AssertionError("MemberId is invalid.")


class ImpostorsService:
    def __init__(self):
        # self.games[GameId] = Game
        self._games: list[Game] = []

    # Getters
    @property
    def games(self) -> list[Game]:
        return self._games

    # Getters but with extra steps
    def _get_game(self, game_id: GameId) -> Game:
        self._assert_game_id(game_id)
        return self._games[game_id]

    def _get_game_unchecked(self, game_id: GameId) -> Game:
        return self._games[game_id]

    # Checkers
    def _check_game_id(self, game_id: GameId) -> bool:
        return game_id < len(self._games)

    # Asserters
    def _assert_game_id(self, game_id: GameId):
        if not self._check_game_id(game_id):
            raise RuntimeError(f"GameId {game_id} is invalid.")

    def start_game(
        self, members: list[MemberId], num_impostors: int, category: str | None
    ) -> GameId:
        game_id = len(self._games)
        game = Game(game_id, members, num_impostors, category)
        self._games.append(game)
        return game_id

    def get_impostor_ids(self, game_id: GameId) -> list[MemberId]:
        game = self._get_game(game_id)

        return game.impostors

    def get_normal_ids(self, game_id: GameId) -> list[MemberId]:
        game = self._get_game(game_id)

        return game.normals

    def check_impostor(self, game_id: GameId, member_id: MemberId) -> bool:
        game = self._get_game(game_id)

        return game.check_impostor(member_id)

    def check_normal(self, game_id: GameId, member_id: MemberId) -> bool:
        game = self._get_game(game_id)

        return game.check_normal(member_id)

    def get_initial_message(self, game_id: GameId, member_id: MemberId) -> str:
        game = self._get_game(game_id)

        return game.get_initial_message(member_id)
