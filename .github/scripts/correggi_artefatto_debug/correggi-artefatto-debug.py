import re, sys, glob, os

PATTERN = re.compile(
    r"agentId: [0-9a-f]+ \(use SendMessage with to: '[0-9a-f]+', summary: '&lt;5-10 word recap&gt;' to continue this agent\)\s*"
    r"<usage>subagent_tokens: \d+\s*tool_uses: \d+\s*duration_ms: \d+</usage>",
    re.DOTALL,
)

FILES = [
    "testi-in-vigore-francia/index.html",
    "testi-in-vigore-spagna/index.html",
    "testi-in-vigore-belgio/index.html",
    "testi-in-vigore-polonia/index.html",
    "testi-in-vigore-lussemburgo/index.html",
]

def main():
    changed = []
    for rel in FILES:
        path = os.path.join(sys.argv[1], rel)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        new_content, n = PATTERN.subn("", content)
        if n != 1:
            print(f"ATTENZIONE: {rel} — trovate {n} occorrenze (attese 1)")
        if new_content != content:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            changed.append(rel)
            print(f"Corretto: {rel}")
    print(f"\nTotale file corretti: {len(changed)}")

if __name__ == "__main__":
    main()
