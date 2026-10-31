import sqlite3, os

conn = sqlite3.connect(r'E:\Agent\Drama Bot\doramas.db')
c = conn.cursor()
c.execute("""
    UPDATE doramas 
    SET title = 'Oddiy bir kun (One Ordinary Day)',
        aliases = 'Oddiy bir kun, One Ordinary Day, Kim Soo-hyun, Cha Seung-won, Oddiy 1 kun'
    WHERE code = 357
""")
conn.commit()
conn.close()
print("357 updated cleanly")
