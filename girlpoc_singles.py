from score_fetcher import ScoreFetcher
import json
import datetime

sf = ScoreFetcher()
sf.debug = False


class Player:
    def __init__(self, name: str, hard: bool, intro_wild: bool):
        self.name = name
        self.eligibility = {
            "hard": hard,
            "intro_wild": intro_wild,
            "wild": True,  # always eligible
        }
    
    @property
    def can_compete_hard(self) -> bool:
        return self.eligibility['hard']
    
    @property
    def can_compete_intro_wild(self) -> bool:
        return self.eligibility['intro_wild']
    
    @property
    def can_compete_wild(self) -> bool:
        return self.eligibility['wild']


def load_from_json(path):
    with open(path) as file:
        return json.load(file)


if __name__ == "__main__":
    event_folder = './girlpoc-25-singles/'
    
    # load config
    config = load_from_json(event_folder + 'config.json')
    start_date = config['start_date']
    end_date = config['end_date']
    attempts_to_count = config['attempts_to_count']

    # load gauntlets
    hard_gauntlet = load_from_json(event_folder + 'hard.json')
    intro_wild_gauntlet = load_from_json(event_folder + 'intro_wild.json')
    wild_gauntlet = load_from_json(event_folder + 'wild.json')

    # load players
    player_names = load_from_json(event_folder + 'players.json')
    
    # check player eligibility for each gauntlet
    players: list[Player] = []
    for player in player_names:
        searches = [
            sf.load_player_scores(
                player_name=player,
                difficulty=list(range(18,26)),
                score_gte=99000,
                end=start_date,  # only disqualify based on scores beforehand
                take=1
            ),
            sf.load_player_scores(
                player_name=player,
                difficulty=list(range(21,26)),
                score_gte=99000,
                end=start_date,  # only disqualify based on scores beforehand
                take=1
            )
        ]
        results = sf.exec_load_player_scores(searches)
        hard_check = len(results[0]) < 1
        wild_check = len(results[1]) < 1
        players.append(Player(player, hard_check, wild_check))
    
    for player in players:
        if player.can_compete_hard:
            # get hard songs
            continue
        if player.can_compete_intro_wild:
            # get intro_wild songs
            continue
        if player.can_compete_wild:
            # get wild songs
            continue
