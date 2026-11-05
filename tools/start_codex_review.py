#!/usr/bin/env python3
"""初回レビューを履歴なしのCodex execで起動し、出力を保存します。"""

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--request-file", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        project = args.project.resolve(strict=True)
        if not project.is_dir():
            raise ValueError("projectには対象プロジェクトのフォルダーを指定してください")
        request = args.request_file.read_text(encoding="utf-8")
        if not request.strip():
            raise ValueError("依頼文が空です")
        spec = importlib.util.spec_from_file_location(
            "review_record", Path(__file__).with_name("render_review_record.py"))
        rr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rr)
        # BIAS-1: 依頼文に残った作成ツールの署名行を、reviewerへ渡す前に除きます。
        prov_spec = importlib.util.spec_from_file_location(
            "review_provenance", Path(__file__).with_name("review_provenance.py"))
        provenance = importlib.util.module_from_spec(prov_spec)
        prov_spec.loader.exec_module(provenance)
        cleaned, stripped = provenance.strip_author_signatures(request)
        if stripped:
            request = cleaned + "\n"
            print(f"provenance: 依頼文から作成ツールの署名行を{stripped}行除きました", file=sys.stderr)
        if not request.strip():
            raise ValueError("署名行を除くと依頼文が空です")
        rr.ensure_safe_output(args.out_dir / "stream.jsonl")
        if args.out_dir.exists() or args.out_dir.is_symlink():
            raise ValueError("出力先には未使用のフォルダーを指定してください")
        output = args.out_dir.resolve()
        output.mkdir(parents=True, mode=0o700)
        rr.write_atomic(output / "request.txt", request.encode("utf-8"))
        command = ["codex", "exec", "--cd", str(project), "--sandbox", "read-only", "--json",
                   "--output-last-message", str(output / "result.md"), "-"]
        with (output / "stream.jsonl").open("x", encoding="utf-8") as stream:
            (output / "stream.jsonl").chmod(0o600)
            result = subprocess.run(command, input=request, stdout=stream,
                                    text=True, cwd=project, check=False)
        rr.write_atomic(output / "execution.json", (json.dumps(
            {"command": command, "exit_code": result.returncode}, ensure_ascii=False) + "\n").encode())
        if (output / "result.md").is_file():
            (output / "result.md").chmod(0o600)
        print(f"Codex終了コード: {result.returncode}; 記録: {output}")
        return result.returncode
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
