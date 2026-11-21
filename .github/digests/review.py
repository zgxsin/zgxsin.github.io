"""Review the rendered digest and return any issues that block publishing."""

import json


LESSONS = {
    "facts": "Check every material number, unit, and date against the cited excerpt. Omit unsupported precision.",
    "attribution": "Attribute vendor claims, label preprints, and distinguish third-party reporting from primary evidence.",
    "status": "Distinguish an announcement, an evaluation kit, a shipping product, and a completed deployment or deal.",
    "readiness": "Tie readiness to a named platform and use case. Require documented field evidence for deployment-ready ratings.",
    "citations": "Use the source that directly supports the claim. Narrow or drop claims that only have indirect support.",
    "video": "Use only source-provided demos that clearly show the hardware or technique described in the selected update.",
    "scope": "Require a concrete, substantive development relevant to the digest topic. Skip generic overviews and weak matches.",
}


def load_lessons(path):
    if not path.exists():
        return set()
    ids = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(ids, list) or any(not isinstance(lesson, str) or lesson not in LESSONS for lesson in ids):
        raise SystemExit("The digest profile contains unknown learned rules.")
    return set(ids)


def save_lessons(path, learned, issues):
    updated = learned | {issue["lesson"] for issue in issues}
    if updated != learned:
        pending = path.with_suffix(".tmp")
        pending.write_text(json.dumps(sorted(updated), indent=2) + "\n", encoding="utf-8")
        pending.replace(path)
    return updated


def drafting_prompt(prompt, learned):
    if not learned:
        return prompt
    rules = "\n".join(f"- {LESSONS[lesson]}" for lesson in sorted(learned))
    return f"{prompt}\n\nDrafting rules learned from past reviews\n\n{rules}"


def review_issues(post, sources, *, prompt, gemini):
    schema = {
        "type": "object",
        "properties": {
            "approved": {"type": "boolean"},
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string"},
                        "lesson": {"type": "string", "enum": list(LESSONS)},
                    },
                    "required": ["detail", "lesson"],
                },
            },
        },
        "required": ["approved", "issues"],
    }
    result = gemini.generate_json(
        prompt=prompt, schema=schema,
        input_data={"post": post, "sources": sources},
    )
    if not isinstance(result, dict) or type(result.get("approved")) is not bool:
        raise SystemExit("AI review returned an invalid verdict.")
    issues = result.get("issues")
    if not isinstance(issues, list) or any(
        not isinstance(issue, dict)
        or not isinstance(issue.get("detail"), str)
        or not issue["detail"].strip()
        or not isinstance(issue.get("lesson"), str)
        or issue["lesson"] not in LESSONS
        for issue in issues
    ):
        raise SystemExit("AI review returned an invalid issue list.")
    if result["approved"] == bool(issues):
        raise SystemExit("AI review verdict and issue list are inconsistent.")
    return [{"detail": " ".join(issue["detail"].split()), "lesson": issue["lesson"]} for issue in issues]
