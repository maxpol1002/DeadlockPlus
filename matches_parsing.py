from telegram.ext import CallbackContext

from dlfunc import get_active_matches

from dbfunc import get_users_uids, insert_users_matches, update_user_matches


def parse_users_matches(user_uids: list, active_matches):
    found_matches = []
    user_uids_set = set(user_uids)
    for match in active_matches:
        for player in match['players']:
            if player['account_id'] in user_uids_set:
                found_matches.append(match)
                update_user_matches(player['account_id'], match['match_id'])

    return found_matches


async def parse_matches_job(context: CallbackContext):
    active_matches = get_active_matches()
    users_uids = get_users_uids()
    users_matches = parse_users_matches(users_uids, active_matches)
    if users_matches:
        insert_users_matches(users_matches)


async def start_job(context: CallbackContext):
    context.job_queue.run_repeating(parse_matches_job, interval=60, first=0)

