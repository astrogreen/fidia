from astropy.io import fits
from glob import glob

extinfo = dict()

for filename in glob("*1_comp.fits"):
    with fits.open(filename) as f:
        exts = [ext.name for ext in f if ext.name != ""]
        extinfo[filename] = exts

for filename, extlist in extinfo.items():
    print(filename + ":")
    [print("   {}".format(n)) for n in extlist]
    print("  (%s extensions)" % len(extlist))



extsets = []

set_fns = []

for n, exts in extinfo.items():
    s = set(exts)
    try:
        idx = extsets.index(s)
    except ValueError:
        extsets.append(s)
        set_fns.append([])
        idx = -1
    set_fns[idx].append(n)

for i, s in enumerate(extsets): 
    print("Files:")
    print("    %s" % ", ".join(set_fns[i]))
    print("  (total %s files)" % len(set_fns[i]))
    print("have these %s extensions:" % len(extsets[i]))
    for f in sorted(extsets[i]):
        print("    %s" % f)

sizes = [len(s) for s in set_fns]

canonical_set = extsets[sizes.index(max(sizes))]

for i, s in enumerate(extsets): 
    print("Files:")
    print("    %s" % ", ".join(set_fns[i]))
    print("  (total %s files)" % len(set_fns[i]))
    extras = s - canonical_set
    print("have these %s extra extensions:" % len(extras))
    for f in sorted(extras):
        print("    %s" % f)
    missing = canonical_set - s
    print("and these %s missing extensions:" % len(missing))
    for f in sorted(missing):
        print("    %s" % f)
    