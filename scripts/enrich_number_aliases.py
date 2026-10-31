import sqlite3, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect('doramas.db')
c = conn.cursor()

c.execute("SELECT id, code, title, aliases FROM doramas")
rows = c.fetchall()

NUM_MAPPINGS = {
    227: ["O'n Ikki Farishta", "On Ikki Farishta", "12 Farishta", "12 ta farishta", "Twelve"],
    163: ["25 21", "25-21", "Yigirma besh yigirma bir", "Twenty Five Twenty One"],
    117: ["9 dumli tulki", "9 dumli tulki 1", "To'qqiz dumli tulki", "To'qqiz dumli tulki 1-fasl"],
    138: ["9 dumli tulki 2", "9 dumli tulki 1938", "To'qqiz dumli tulki 2-fasl", "Tale of the Nine Tailed 1938"],
    168: ["Yuz kunlik yolg'on", "Yuz kunlik yolgon", "100 kunlik yolg'on", "100 Days of Deception"],
    101: ["Doktor X", "Doctor X", "Oq Mafia", "Doktor x"],
    106: ["Darbadar ruh 1", "Darbadar ruh 1-fasl", "Alchemy of Souls 1"],
    140: ["Darbadar ruh 2", "Darbadar ruh 2-fasl", "Alchemy of Souls 2"],
    112: ["Ojiz qahramon 1", "Weak Hero 1"],
    136: ["Ojiz qahramon 2", "Weak Hero 2"],
    118: ["Ovchi itlar 1", "Bloodhounds 1"],
    135: ["Ovchi itlar 2", "Bloodhounds 2"],
    124: ["Qotillar do'koni 1", "A Shop for Killers 1"],
    137: ["Qotillar do'koni 2", "A Shop for Killers 2"],
    142: ["Pentxaus 1", "Penthouse 1"],
    143: ["Pentxaus 2", "Penthouse 2"],
    144: ["Pentxaus 3", "Penthouse 3"],
    347: ["Xalk 1", "Xalk bir", "Hulk 1", "Hulk 2003"],
    348: ["Xalk 2", "Xalk ikki", "Hulk 2", "The Incredible Hulk 2008"],
    349: ["She-Hulk", "Ayol Xalk", "Ayol Halk", "She Hulk"],
}

updated = 0
for d_id, code, title, existing_aliases in rows:
    if code in NUM_MAPPINGS:
        curr = [a.strip() for a in (existing_aliases or "").split(",") if a.strip()]
        new_aliases = list(curr)
        for cand in NUM_MAPPINGS[code]:
            if cand.lower() not in [x.lower() for x in new_aliases]:
                new_aliases.append(cand)
        final_str = ", ".join(new_aliases)
        if final_str != (existing_aliases or ""):
            c.execute("UPDATE doramas SET aliases = ? WHERE id = ?", (final_str, d_id))
            updated += 1
            print(f"[{code}] Updated aliases -> {final_str}")

conn.commit()
conn.close()
print(f"Successfully enriched {updated} doramas in doramas.db")
