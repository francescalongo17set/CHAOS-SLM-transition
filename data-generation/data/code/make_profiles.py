"""Stage 5a: 300 invented client profiles (book 16.4). No real person: surnames, ages, cities are invented."""
import json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
(ROOT / "seeds").mkdir(exist_ok=True)
rng = random.Random(20261110)

SURNAMES = ["Rossi", "Bianchi", "Ferretti", "Marchetti", "Colombo", "Greco", "Bellini", "Fontana", "Moretti", "Gallo", "Leone", "Mancini",
            "Barbieri", "Villa", "Conti", "Costa", "Giordano", "Rinaldi", "Caruso", "Ferrara", "Sala", "Pellegrini", "Monti", "Basile",
            "Parisi", "Silvestri", "Testa", "Neri", "Orlando", "Piras", "Serra", "Cattaneo", "Valentini", "De Angelis", "Fabbri", "Lombardi",
            "Martini", "Palumbo", "Riva", "Santoro", "Vitale", "Zanetti", "Bruni", "Guerra", "Longo", "Marini", "Pagano", "Ricci", "Sartori", "Tedesco"]
RISK = ["prudente", "moderato", "equilibrato", "dinamico", "molto prudente", "orientato alla crescita"]
GOALS = ["integrare la pensione", "pagare gli studi dei figli", "comprare casa", "proteggere il patrimonio", "accumulare un capitale",
         "avere un reddito aggiuntivo", "lasciare un capitale agli eredi", "finanziare un progetto personale"]
SITUATIONS = ["libero professionista", "dipendente pubblico", "pensionato", "imprenditore con una piccola azienda", "insegnante",
              "artigiano", "infermiera", "lavoratore autonomo", "commerciante", "ingegnere dipendente", "agricoltore", "coppia con due figli",
              "giovane alla prima assunzione", "vedovo", "famiglia monoreddito"]
CITIES = ["Brescia", "Cuneo", "Pisa", "Bari", "Udine", "Salerno", "Ancona", "Lecce", "Varese", "Trento", "Perugia", "Cagliari", "Modena", "Novara", "Catania"]
VAGUE = ["un cliente tranquillo", "un cliente giovane", "una persona con poca esperienza", "un cliente di ieri", "un cliente anziano", "un cliente benestante"]

out = []
for i in range(300):
    age = rng.choice([rng.randint(26, 40), rng.randint(41, 58), rng.randint(59, 78)])
    sit = rng.choice(SITUATIONS)
    if sit == "giovane alla prima assunzione":
        age = rng.randint(24, 32)
    if sit == "pensionato":
        age = rng.randint(63, 80)
    horizon = rng.choice([3, 5, 7, 8, 10, 12, 15, 20])
    name = rng.choice(SURNAMES) if rng.random() < 0.75 else rng.choice("ABCDEFGHLMNPRSTV") + "."
    out.append({"profile_id": f"cp-{i+1:03d}", "name": name, "age": age, "city": rng.choice(CITIES), "situation": sit,
                "risk_attitude": rng.choice(RISK), "horizon_years": horizon, "goal": rng.choice(GOALS), "vague_label": rng.choice(VAGUE)})
with open(ROOT / "seeds/client_profiles.jsonl", "w", encoding="utf-8") as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(len(out), "profiles")
