from custom_types.discord import MemberId

from random import sample

from custom_types.impostors import GameId


class Game:
    def __init__(self, game_id: GameId, members: list[MemberId], num_impostors: int):
        self._game_id = game_id
        self._members = list(set(members))

        # Assert this will be a valid game
        if not num_impostors <= len(self._members):
            raise AssertionError(
                "Number of impostors cannot be less than number of members!"
            )

        # Separate impostors and normals
        self._impostors = sample(members, num_impostors)
        self._normals: list[MemberId] = [
            member for member in self._members if member not in self._impostors
        ]

    @property
    def game_id(self) -> GameId:
        return self._game_id

    @property
    def members(self) -> list[MemberId]:
        return self._members

    @property
    def impostors(self) -> list[MemberId]:
        return self._impostors

    @property
    def normals(self) -> list[MemberId]:
        return self._normals

    def check_impostor(self, member: MemberId) -> bool:
        return member in self.impostors

    def check_normal(self, member: MemberId) -> bool:
        return member in self.normals


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
        return self._games[game_id]

    # Checkers
    def _check_game_id(self, game_id: GameId) -> bool:
        return game_id < len(self._games)

    # Asserters
    def _assert_game_id(self, game_id: GameId):
        if not self._check_game_id(game_id):
            raise RuntimeError(f"GameId {game_id} is invalid.")

    def start_game(self, members: list[MemberId], num_impostors: int) -> GameId:
        game_id = len(self._games)
        game = Game(game_id, members, num_impostors)
        self._games.append(game)
        return game_id

    def get_impostor_ids(self, game_id: GameId) -> list[MemberId]:
        self._assert_game_id(game_id)

        game = self._get_game(game_id)
        return game.impostors

    def get_normal_ids(self, game_id: GameId) -> list[MemberId]:
        self._assert_game_id(game_id)

        game = self._get_game(game_id)
        return game.normals

    def check_impostor(self, game_id: GameId, member: MemberId) -> bool:
        self._assert_game_id(game_id)

        game = self._get_game(game_id)
        return game.check_impostor(member)

    def check_normal(self, game_id: GameId, member: MemberId) -> bool:
        self._assert_game_id(game_id)

        game = self._get_game(game_id)
        return game.check_normal(member)
