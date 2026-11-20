"""Build host segments with RAMP/CONFORM for given shot ids -> work/seg/<seq>_s0.mkv; print ramp log + segment paths."""
import sys
import make_ep03 as m
for i, s in enumerate(m.sc["shots"]):
    if s["id"] in sys.argv[1:]:
        out, d = m.studio_segment(i, s)
        print("SEG", s["id"], out, round(d, 2), flush=True)
