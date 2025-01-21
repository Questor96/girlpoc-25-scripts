from score_fetcher import ScoreFetcher
import json
import datetime
import pprint
from gcs.google_auth import gspread_auth
from gspread.cell import Cell


debug = False
sf = ScoreFetcher()
sf.debug = debug

# lazy printer for debugging:)
pp = pprint.PrettyPrinter(indent=2)

class Player:
    def __init__(self, name: str, hard: bool, intro_wild: bool):
        self.name = name
        self.eligibility = {
            "hard": hard,
            "intro_wild": intro_wild,
            "wild": True,  # always eligible
        }
        self.hard_scores = {}
        self.intro_wild_scores = {}
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
    
    @property
    def has_hard_scores(self) -> bool:
        return self._count_nonzero_scores(self.hard_scores) > 0
    
    @property
    def has_intro_wild_scores(self) -> bool:
        return self._count_nonzero_scores(self.intro_wild_scores) > 0
    
    @property
    def has_wild_scores(self) -> bool:
        return self._count_nonzero_scores(self.wild_scores) > 0

    @staticmethod
    def _count_nonzero_scores(scores:dict):
        return len([
            score
            for score in scores.values()
            if score > 0
        ])

    def set_hard_scores(self, hard_scores, hard_charts):
        self.hard_scores = self._maximize_scores(hard_scores, hard_charts)
    
    def set_intro_wild_scores(self, intro_wild_scores, intro_wild_charts):
        self.intro_wild_scores = self._maximize_scores(intro_wild_scores, intro_wild_charts)
    
    def set_wild_scores(self, wild_scores, wild_charts):
        self.wild_scores = self._maximize_scores(wild_scores, wild_charts)

    def _maximize_scores(self, scores, charts):
        return {
            chart_id: self._maximize_score(scores, chart_id)
            for chart_id in charts
        }

    @staticmethod
    def _maximize_score(scores, chart_id):
        max_score=0
        for score in scores.get(chart_id, []):
            if score > max_score:
                max_score = score
        return max_score


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
    [result] = sf.exec_load_player_scores([search])
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


def get_song_title_by_chart_id(song_info_aug, chart_id):
    [song_title] = [
        song["title"]
        for song in song_info_aug
        if song["chart_id"] == chart_id
    ]
    return song_title


"""
Table Template
    1           2       3       4       ...
1   <empty>     song1   song2   song3   ...
2   player_name score1  score2  score3
3   player_name score1  score2  score3
N
"""
def write_results_header_to_spreadsheet(sheet, charts, gauntlet) -> None:
    cells = []
    row = 1
    col = 2  # skip [1,1]
    cells.append(Cell(row, col, "eligible for ranking"))
    col += 1
    for chart_id in charts:
        cells.append(Cell(row, col, get_song_title_by_chart_id(gauntlet, chart_id)))
        col += 1
    sheet.update_cells(cells)

def write_results_row_to_spreadsheet(sheet, row, name, eligibility, scores, charts) -> None:
    cells = []
    col = 1 
    cells.append(Cell(row, col, name))
    col += 1
    cells.append(Cell(row, col, eligibility))
    col += 1
    for chart_id in charts:
        cells.append(Cell(row, col, scores[chart_id]))
        col += 1
    sheet.update_cells(cells)


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
        scores = get_event_scores(
            player=player,
            chart_ids=hard_charts,
            start_date=start_date,
            end_date=end_date,
            attempts_to_count=attempts_to_count
        )
        player.set_hard_scores(scores, hard_charts)

        scores = get_event_scores(
            player=player,
            chart_ids=intro_wild_charts,
            start_date=start_date,
            end_date=end_date,
            attempts_to_count=attempts_to_count
        )
        player.set_intro_wild_scores(scores, intro_wild_charts)

        scores = get_event_scores(
            player=player,
            chart_ids=wild_charts,
            start_date=start_date,
            end_date=end_date,
            attempts_to_count=attempts_to_count
        )
        player.set_wild_scores(scores, wild_charts)

    # report results
    gs = gspread_auth()
    results_spreadsheet = gs.open_by_key(load_from_json(event_folder + 'singles_results_spreadsheet_key.json').get('key'))

    # Hard
    sheet = results_spreadsheet.worksheet("Hard")
    sheet.clear()
    write_results_header_to_spreadsheet(
        sheet=sheet,
        charts=hard_charts,
        gauntlet=hard_gauntlet
    )
    row = 2
    for player in players:
        if not player.has_hard_scores:
            continue
        write_results_row_to_spreadsheet(
            sheet=sheet,
            row=row,
            name=player.name,
            eligibility=player.can_compete_hard,
            scores=player.hard_scores,
            charts=hard_charts
        )
        row += 1

    # Intro Wild
    sheet = results_spreadsheet.worksheet("Intro to Wild")
    sheet.clear()
    write_results_header_to_spreadsheet(
        sheet=sheet,
        charts=intro_wild_charts,
        gauntlet=intro_wild_gauntlet
    )
    row = 2
    for player in players:
        if not player.has_intro_wild_scores:
            continue
        write_results_row_to_spreadsheet(
            sheet=sheet,
            row=row,
            name=player.name,
            eligibility=player.can_compete_intro_wild,
            scores=player.intro_wild_scores,
            charts=intro_wild_charts
        )
        row += 1
    
    # Wild
    sheet = results_spreadsheet.worksheet("Wild")
    sheet.clear()
    write_results_header_to_spreadsheet(
        sheet=sheet,
        charts=wild_charts,
        gauntlet=wild_gauntlet
    )
    row = 2
    for player in players:
        if not player.has_wild_scores:
            continue
        write_results_row_to_spreadsheet(
            sheet=sheet,
            row=row,
            name=player.name,
            eligibility=player.can_compete_wild,
            scores=player.wild_scores,
            charts=wild_charts
        )
        row += 1
    
    if debug:
        # print max score per chart
        print("HARD")
        for player in players:
            scores = player.hard_scores
            for chart_id in hard_charts:
                song_title = get_song_title_by_chart_id(hard_gauntlet, chart_id)
                score = scores[chart_id]
                print("\t".join([player.name, song_title, str(score)]))
            print()

        print("INTRO TO WILD")
        for player in players:
            scores = player.intro_wild_scores
            for chart_id in intro_wild_charts:
                song_title = get_song_title_by_chart_id(intro_wild_gauntlet, chart_id)
                score = scores[chart_id]
                print("\t".join([player.name, song_title, str(score)]))
            print()
        
        print("WILD")
        for player in players:
            scores = player.wild_scores
            for chart_id in wild_charts:
                song_title = get_song_title_by_chart_id(wild_gauntlet, chart_id)
                score = scores[chart_id]
                print("\t".join([player.name, song_title, str(score)]))
            print()
