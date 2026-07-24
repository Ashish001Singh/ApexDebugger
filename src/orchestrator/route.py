from pathlib import Path
from dataclasses import dataclass, field



@dataclass
class LwcBundle:
    js: Path
    html: Path | None

@dataclass
class RoutedFiles:
    lwc_bundles: list[LwcBundle] = field(default_factory=list)
    apex_files: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)

def route(paths: list[Path]) -> RoutedFiles:
    result = RoutedFiles()
    for path in paths:
        if path.suffix in {".cls", ".trigger"}:
            result.apex_files.append(path)
        elif path.suffix == ".js":
            html = path.with_suffix(".html")
            result.lwc_bundles.append(LwcBundle(js=path, html=html if html.exists() else None))
        else:
            result.skipped.append(path)
    return result