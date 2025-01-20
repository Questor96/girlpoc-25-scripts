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
        self.hard_scores = {}
        self.intro_to_wild_scores = {}
        self.wild_scores = {}
    
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


def get_event_scores(
    player: Player,
    chart_ids: list,
    start_date: datetime,
    end_date: datetime,
    attempts_to_count: int
):
    search = sf.load_player_scores(
        player_name=player.name,
        chart_ids=chart_ids,
        start=start_date,
        end=end_date,
        sort_field="created_at",
        order="asc"
    )
    result = sf.exec_load_player_scores(search)
    scores = {
        chart_id: []
        for chart_id in chart_ids
    }
    for score in result:
        chart_id = score["song_chart_id"]
        if len(scores[chart_id]) <= attempts_to_count:
            scores[chart_id].append(score["score"])
        else:
            continue
    return scores


if __name__ == "__main__":
    event_folder = './girlpoc-25-singles/'
    
    # load config
    config = load_from_json(event_folder + 'config.json')
    start_date = config['start_date']
    end_date = config['end_date']
    attempts_to_count = config['attempts_to_count']

    # load gauntlets
    hard_gauntlet = load_from_json(event_folder + 'hard.json')
    hard_charts = sf.filter_charts_by_song(hard_gauntlet)

    intro_wild_gauntlet = load_from_json(event_folder + 'intro_wild.json')
    intro_wild_charts = sf.filter_charts_by_song(intro_wild_gauntlet)

    wild_gauntlet = load_from_json(event_folder + 'wild.json')
    wild_charts = sf.filter_charts_by_song(wild_gauntlet)

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
    
    # retrieve event scores for players
    for player in players:
        if player.can_compete_hard:
            scores = get_event_scores(
                player=player,
                chart_ids=hard_charts,
                start_date=start_date,
                end_date=end_date,
                attempts_to_count=attempts_to_count
            )
            player.hard_scores = scores

        if player.can_compete_intro_wild:
            scores = get_event_scores(
                player=player,
                chart_ids=intro_wild_charts,
                start_date=start_date,
                end_date=end_date,
                attempts_to_count=attempts_to_count
            )
            player.intro_to_wild_scores = scores

        if player.can_compete_wild:
            scores = get_event_scores(
                player=player,
                chart_ids=wild_charts,
                start_date=start_date,
                end_date=end_date,
                attempts_to_count=attempts_to_count
            )
            player.wild_scores = scores
