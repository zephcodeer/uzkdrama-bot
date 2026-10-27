import urllib.request

redirect_urls = [
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHASfNz6ylbbW2oYUCP2TTeBjYrJgfJifwOTuysnI5QdF0r54fyqsdkVICU2QZyEy32L5PE0vrTvcDjwjOeQVr_ttzyink6D6tt2z44M-lRXhsw1as-kvf5_c5ueRI=",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFa-f_XR6XVdZ9LwucqJv4ROA5kCCzLsBfGSnu8cNYEzjRO1iMiw1njxq2JII_mrA53L93V0zIc19gi7p6hIjgipWzKvfN_AWveSAL5STBWvtG_50-NCWrp_IYxIag=",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFVPlfEAfUHWNHAvjaBW_OH_WPs-lmc-8HYWApnrDltiK9dVfKGw6_BgIFJtIWAvce9waqdd-JNxXb2x-Q3RTXkrmyJT5pzjzGSX3eG6JOGHe_Ii9bQpUZODvSlrqk=",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHA_-CWEBgCtXgm35utLqygiRPRTRlMjeK5mKYifKp5NiSfS3cq5VFShQ9BcedWYe4IijfQkKxsSH7aQ5EiybsTXh8EJv_QWnPYDjdlE3M6OzGQuBxb4yFJtfHqLVI=",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHzi5o95_DjyZhKNJCUV5gqu_JMZg84leZtap8-LNvm8WFPVli6zn09WANJvPFmkbwHTxTeoSkYIR8lpEL47iN0nB3o4--dU1e8rMTZsjrChu-Tmcn8frsatW1rubg=",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG9QQNWpkIgfdL51j2ZKgzaBrhHgVwPX9EUHqXKCArmrHvA-DHwanVPvf8HYh2TvncxwGFS_mLPsVJ9ZwCpaytzSQ8Ys9f-nd-CHd9ahcNjux6EpcDIlBF4ESTVnsM=",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFqlSU2JeBVu-LCsMWlrDfWW6knym3fztUksRRrfuapJGzXTBA1--n95iu2vOm-CPA6xG4q5e71rnn9IhmDrQKcQ9RCEmmGVKj34JsjV_c26Plh41mx6msAfdGAD_U="
]

for i, u in enumerate(redirect_urls, 1):
    req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            final_url = resp.geturl()
            print(f"Item {i} -> {final_url}")
    except Exception as e:
        print(f"Item {i} error: {e}")
