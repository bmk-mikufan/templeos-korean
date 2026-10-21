import re, pathlib
p = pathlib.Path("src/PersonalMenu.DD")
t = p.read_text(encoding="latin-1")
print("chars", len(t), "lines", t.count("\n"))
# menu labels: $MA... "Label"
labs = re.findall(r'\$MA[^"\n]*"([^"]+)"', t)
print("MA labels", len(labs))
for s in labs[:80]: print(repr(s))
print("---- LK labels ----")
lks = re.findall(r'\$LK,"([^"]+)"', t)
print(len(lks))
for s in lks[:40]: print(repr(s))
