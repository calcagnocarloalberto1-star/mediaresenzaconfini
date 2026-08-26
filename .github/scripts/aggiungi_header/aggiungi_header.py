import re, os, sys

NAV_RE = re.compile(
    r'(<div class="nav-links">.*?)\n(</div>\n<form class="search-box")',
    re.DOTALL,
)
# Variant for HTML embedded as a JS string literal (e.g. pubblica/index.html's
# in-browser article editor), where newlines are the two literal characters \n
# rather than an actual newline byte.
NAV_RE_ESCAPED = re.compile(
    r'(<div class="nav-links">.*?)\\n(</div>\\n<form class="search-box")',
    re.DOTALL,
)
NEW_LINK = '<a href="/come-si-scrive-e-come-si-dice/">Come si scrive e come si dice</a>'
ALREADY_MARKER = NEW_LINK + '\n</div>\n<form class="search-box"'
ALREADY_MARKER_ESCAPED = NEW_LINK + '\\n</div>\\n<form class="search-box"'

def process(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if ALREADY_MARKER in content or ALREADY_MARKER_ESCAPED in content:
        return "skip-already"

    if '<div class="nav-links">' not in content:
        return "skip-no-nav"

    new_content, n = NAV_RE.subn(
        lambda m: m.group(1) + "\n" + NEW_LINK + "\n" + m.group(2), content, count=1
    )
    if n == 0:
        new_content, n = NAV_RE_ESCAPED.subn(
            lambda m: m.group(1) + "\\n" + NEW_LINK + "\\n" + m.group(2), content, count=1
        )
    if n == 0:
        return "skip-no-match"

    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return "patched"
    return "skip-no-change"

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    counts = {}
    no_match_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirpath.split(os.sep):
            continue
        for fn in filenames:
            if not fn.endswith(".html"):
                continue
            path = os.path.join(dirpath, fn)
            result = process(path)
            counts[result] = counts.get(result, 0) + 1
            if result == "skip-no-match":
                no_match_files.append(path)

    print("Riepilogo:")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")
    if no_match_files:
        print(f"\nFile con nav-links ma pattern non riconosciuto ({len(no_match_files)}):")
        for p in no_match_files[:30]:
            print(f"  {p}")

if __name__ == "__main__":
    main()
