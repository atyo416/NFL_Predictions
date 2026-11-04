"""Exact franchise identities and designated sides; ambiguous events need review."""
from .data_loader import ALIASES
from .analysis import TEAM_DIVISION
from .ensemble import timestamp
from .odds_store import key

NAMES=['Arizona Cardinals','Atlanta Falcons','Baltimore Ravens','Buffalo Bills','Carolina Panthers','Chicago Bears','Cincinnati Bengals','Cleveland Browns','Dallas Cowboys','Denver Broncos','Detroit Lions','Green Bay Packers','Houston Texans','Indianapolis Colts','Jacksonville Jaguars','Kansas City Chiefs','Los Angeles Chargers','Los Angeles Rams','Las Vegas Raiders','Miami Dolphins','Minnesota Vikings','New England Patriots','New Orleans Saints','New York Giants','New York Jets','Philadelphia Eagles','Pittsburgh Steelers','Seattle Seahawks','San Francisco 49ers','Tampa Bay Buccaneers','Tennessee Titans','Washington Commanders']
CODES=['ARI','ATL','BAL','BUF','CAR','CHI','CIN','CLE','DAL','DEN','DET','GB','HOU','IND','JAX','KC','LAC','LA','LV','MIA','MIN','NE','NO','NYG','NYJ','PHI','PIT','SEA','SF','TB','TEN','WAS']
TEAM_NAMES={name.casefold():code for name,code in zip(NAMES,CODES)}
TEAM_NAMES.update({'oakland raiders':'LV','san diego chargers':'LAC','st. louis rams':'LA','st louis rams':'LA','washington football team':'WAS','washington redskins':'WAS'})


def team(value):
    text=str(value).strip();code=ALIASES.get(text.upper(),text.upper())
    if code in TEAM_DIVISION:return code
    if text.casefold() in TEAM_NAMES:return TEAM_NAMES[text.casefold()]
    raise ValueError(f'Unknown exact team identifier: {text}')


def nfl_season(kickoff):
    at=timestamp(kickoff).tz_convert('America/New_York')
    return at.year-1 if at.month<=3 else at.year


def match(quote,schedules,tolerance_seconds=300):
    s=schedules[schedules.game_type.eq('REG')].copy()
    h=team(quote['home_team']);a=team(quote['away_team']);at=timestamp(quote['kickoff'])
    same=s[s.season.eq(int(quote['season']))&s.home_team.map(team).eq(h)&s.away_team.map(team).eq(a)]
    fingerprint=key(same[['game_id','season','kickoff','home_team','away_team']].astype(str).to_dict('records'))
    near=same[(same.kickoff-at).dt.total_seconds().abs().le(tolerance_seconds)]
    result={'quote_id':quote['quote_id'],'provider':quote['provider'],'event_id':quote['event_id'],'schedule_fingerprint':fingerprint,'game_id':None,'status':'unmatched','candidate_game_ids':same.game_id.tolist()}
    if len(near)==1:
        g=near.iloc[0];status=str(g.get('status','')).lower()
        result.update(game_id=g.game_id,status='matched' if status not in ['canceled','cancelled','postponed','suspended'] else 'event_unavailable',schedule_kickoff=g.kickoff.isoformat(),neutral=bool(g.get('neutral',False)))
    elif len(near)>1:result['status']='ambiguous'
    elif len(same):result['status']='kickoff_changed_review'
    else:
        reversed_=s[s.season.eq(int(quote['season']))&s.home_team.map(team).eq(a)&s.away_team.map(team).eq(h)]
        if len(reversed_):result['status']='home_away_reversed_review'
    result['match_id']=key(result);return result
