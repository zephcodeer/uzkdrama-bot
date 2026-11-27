import asyncio
import sys

sys.path.insert(0, 'E:/Agent/Drama Bot')
import database as db
import keyboards as kb

async def test():
    d = await db.get_dorama_by_code(666)
    eps = await db.get_episodes(d['id'])
    display_items = kb.build_display_episodes(eps)
    
    # Test for ep 21
    current_item = next((it for it in display_items if it['start_ep'] <= 21 <= it['end_ep']), None)
    prev_item = next((it for it in reversed(display_items) if it['end_ep'] < current_item['start_ep']), None)
    next_item = next((it for it in display_items if it['start_ep'] > current_item['end_ep']), None)
    
    print('EP 21:')
    print('  prev_ep_target:', prev_item['start_ep'] if prev_item else None)
    print('  next_ep_target:', next_item['start_ep'] if next_item else None)
    assert prev_item['start_ep'] == 19
    assert next_item['start_ep'] == 22
    
    # Check generated keyboard for ep 21
    markup = kb.episode_player_kb(
        dorama_id=d['id'],
        current_ep=21,
        has_next=True,
        bookmarked=False,
        next_ep=next_item['start_ep'],
        prev_ep=prev_item['start_ep']
    )
    for row in markup.inline_keyboard:
        for btn in row:
            print(f'  Button: "{btn.text}" -> data="{btn.callback_data}"')

    # Test for ep 19
    current_item_19 = next((it for it in display_items if it['start_ep'] <= 19 <= it['end_ep']), None)
    prev_item_19 = next((it for it in reversed(display_items) if it['end_ep'] < current_item_19['start_ep']), None)
    next_item_19 = next((it for it in display_items if it['start_ep'] > current_item_19['end_ep']), None)
    print('EP 19:')
    print('  prev_ep_target:', prev_item_19['start_ep'] if prev_item_19 else None)
    print('  next_ep_target:', next_item_19['start_ep'] if next_item_19 else None)
    assert prev_item_19['start_ep'] == 18
    assert next_item_19['start_ep'] == 21

    print('ALL UNIT TESTS PASSED!')

if __name__ == '__main__':
    asyncio.run(test())
