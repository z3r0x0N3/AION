from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any

from aion.eventbus import EventBus

GIT_CACHE: dict[str, dict[str, Any]] = {}


def enrich_file(path: str | Path, event_bus: EventBus | None = None) -> dict[str, Any]:
    p = Path(path)
    data: dict[str, Any] = {
        "path": str(p),
        "name": p.name,
        "extension": p.suffix.lower(),
        "is_dir": p.is_dir(),
        "size": 0,
        "mtime": 0.0,
        "atime": 0.0,
        "ctime": 0.0,
        "permissions": "",
        "owner": "",
        "group": "",
        "line_count": 0,
        "code_lines": 0,
        "comment_lines": 0,
        "blank_lines": 0,
        "language": _detect_language(p),
        "mime_type": "",
        "imports": [],
        "git_commits_30d": 0,
        "git_authors": [],
        "git_last_commit_msg": "",
        "git_branch": _git_branch(p),
        "checksum_md5": "",
        "checksum_sip32": "",
        "symlink_target": "",
        "hardlinks": 0,
        "inode": 0,
        "device": 0,
        "blocks": 0,
        "blksize": 0,
    }

    try:
        stat = p.stat()
        data["size"] = stat.st_size
        data["mtime"] = stat.st_mtime
        data["atime"] = stat.st_atime
        data["ctime"] = stat.st_ctime
        data["inode"] = stat.st_ino
        data["device"] = stat.st_dev
        data["hardlinks"] = stat.st_nlink
        data["blocks"] = stat.st_blocks
        data["blksize"] = stat.st_blksize
        data["permissions"] = oct(stat.st_mode)[-3:]
    except (OSError, PermissionError):
        pass

    try:
        import pwd, grp
        data["owner"] = pwd.getpwuid(stat.st_uid).pw_name
        data["group"] = grp.getgrgid(stat.st_gid).gr_name
    except (ImportError, KeyError, OSError):
        pass

    if p.is_symlink():
        try:
            data["symlink_target"] = str(p.readlink())
        except OSError:
            pass

    if p.is_file() and p.stat().st_size > 0:
        try:
            content = p.read_bytes()
            data["checksum_md5"] = _md5(content)
            data["checksum_sip32"] = _sip32(content)
            data["mime_type"] = _mime_type(content, data["extension"])

            if _is_text(data["extension"], content):
                text = content.decode("utf-8", errors="replace")
                lines = text.splitlines()
                data["line_count"] = len(lines)
                data["blank_lines"] = sum(1 for l in lines if not l.strip())
                data["comment_lines"] = _count_comments(lines, data["extension"])
                data["code_lines"] = data["line_count"] - data["blank_lines"] - data["comment_lines"]
                data["imports"] = _extract_imports(lines, data["extension"])
        except (OSError, PermissionError, UnicodeDecodeError):
            pass

    _gather_git_data(p, data)

    return data


def _detect_language(path: Path) -> str:
    ext_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript React",
        ".jsx": "JavaScript React", ".rs": "Rust", ".go": "Go", ".java": "Java",
        ".cpp": "C++", ".c": "C", ".h": "C/C++ Header", ".hpp": "C++ Header",
        ".rb": "Ruby", ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin",
        ".scala": "Scala", ".r": "R", ".m": "Objective-C", ".mm": "Objective-C++",
        ".sh": "Shell", ".bash": "Bash", ".zsh": "Zsh", ".fish": "Fish",
        ".pl": "Perl", ".pm": "Perl Module", ".lua": "Lua", ".ex": "Elixir",
        ".exs": "Elixir Script", ".clj": "Clojure", ".cljs": "ClojureScript",
        ".hs": "Haskell", ".ml": "OCaml", ".zig": "Zig", ".nim": "Nim",
        ".vue": "Vue", ".svelte": "Svelte", ".astro": "Astro",
        ".css": "CSS", ".scss": "SCSS", ".less": "Less", ".html": "HTML",
        ".xml": "XML", ".json": "JSON", ".yaml": "YAML", ".yml": "YAML",
        ".toml": "TOML", ".md": "Markdown", ".rst": "reStructuredText",
        ".tex": "LaTeX", ".sql": "SQL", ".dockerfile": "Dockerfile",
        ".makefile": "Makefile", ".cmake": "CMake",
    }
    return ext_map.get(path.suffix.lower(), "Unknown")


def _is_text(ext: str, content: bytes) -> bool:
    text_exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go", ".java",
                 ".cpp", ".c", ".h", ".hpp", ".rb", ".php", ".swift", ".kt",
                 ".sh", ".bash", ".zsh", ".pl", ".lua", ".md", ".rst", ".txt",
                 ".json", ".yaml", ".yml", ".toml", ".xml", ".html", ".css",
                 ".scss", ".less", ".sql", ".cfg", ".ini", ".conf", ".env",
                 ".gitignore", ".dockerfile", ".makefile", ".cmake"}
    if ext in text_exts:
        return True
    try:
        content.decode("utf-8")
        return True
    except (UnicodeDecodeError, UnicodeError):
        return False


def _count_comments(lines: list[str], ext: str) -> int:
    single = "#" if ext in {".py", ".rb", ".pl", ".sh", ".bash", ".zsh", ".fish", ".r", ".yaml", ".yml"} else "//"
    count = 0
    in_block = False
    for line in lines:
        stripped = line.strip()
        if in_block:
            count += 1
            if "*/" in stripped:
                in_block = False
            continue
        if stripped.startswith("/*"):
            count += 1
            if "*/" not in stripped:
                in_block = True
            continue
        if stripped.startswith(single):
            count += 1
    return count


def _extract_imports(lines: list[str], ext: str) -> list[str]:
    imports: list[str] = []
    if ext == ".py":
        for line in lines:
            s = line.strip()
            if s.startswith(("import ", "from ")):
                imports.append(s)
    elif ext in {".js", ".ts", ".tsx", ".jsx"}:
        for line in lines:
            s = line.strip()
            if s.startswith(("import ", "require(", "export ")):
                imports.append(s)
    elif ext in {".rs"}:
        for line in lines:
            s = line.strip()
            if s.startswith(("use ", "extern crate", "mod ")):
                imports.append(s)
    return imports


def _md5(data: bytes) -> str:
    import hashlib
    return hashlib.md5(data).hexdigest()


def _sip32(data: bytes) -> str:
    import hashlib
    return hashlib.sip24(data, key=b"aion_salt12345678").hex() if hasattr(hashlib, "sip24") else _md5(data)[:8]


def _mime_type(content: bytes, ext: str) -> str:
    import mimetypes
    t, _ = mimetypes.guess_type(f"x{ext}")
    return t or "application/octet-stream"


def _git_branch(path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(path) if path.is_dir() else str(path.parent),
             "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=3
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def _gather_git_data(path: Path, data: dict[str, Any]) -> None:
    repo_dir = _find_git_root(path)
    if not repo_dir:
        return

    rel = path.relative_to(repo_dir) if path != repo_dir else Path(".")
    cache_key = str(repo_dir)

    if cache_key not in GIT_CACHE:
        try:
            branch = subprocess.run(
                ["git", "-C", str(repo_dir), "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, timeout=3
            ).stdout.strip()
            GIT_CACHE[cache_key] = {"branch": branch}
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            GIT_CACHE[cache_key] = {"branch": ""}

    data["git_branch"] = GIT_CACHE[cache_key].get("branch", "")

    try:
        log = subprocess.run(
            ["git", "-C", str(repo_dir), "log", "--oneline", "--since=30.days",
             "--format=%H|%an|%s", "--", str(rel)],
            capture_output=True, text=True, timeout=5
        )
        lines = [l for l in log.stdout.splitlines() if l.strip()]
        data["git_commits_30d"] = len(lines)
        authors: set[str] = set()
        for l in lines:
            parts = l.split("|", 2)
            if len(parts) >= 2:
                authors.add(parts[1])
            if len(parts) >= 3 and not data.get("git_last_commit_msg"):
                data["git_last_commit_msg"] = parts[2]
        data["git_authors"] = sorted(authors)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass


def _find_git_root(path: Path) -> Path | None:
    for p in [path] + list(path.parents):
        if (p / ".git").exists():
            return p
    return None
