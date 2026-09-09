#!/usr/bin/env python3
"""
fnfn GUI - Folder Names From File Names
파일 이름을 기반으로 빈 폴더들을 자동으로 생성합니다. (GUI 버전)
"""

import os
import sys
import argparse
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext


# ─── 핵심 로직 ─────────────────────────────────────────────────────────────────

def create_folders_from_files(source_dir, output_dir=None, include_ext=False,
                               recursive=False, dry_run=False):
    source_dir = os.path.abspath(source_dir)
    if not os.path.isdir(source_dir):
        return [], [f"[오류] 폴더를 찾을 수 없습니다: {source_dir}"]

    if output_dir is None:
        output_dir = source_dir
    else:
        output_dir = os.path.abspath(output_dir)

    if recursive:
        file_names = []
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [
                d for d in dirs
                if os.path.abspath(os.path.join(root, d)) != output_dir
            ]
            for f in files:
                file_names.append(f)
    else:
        file_names = [
            f for f in os.listdir(source_dir)
            if os.path.isfile(os.path.join(source_dir, f))
        ]

    created, skipped, log = [], [], []

    for file_name in sorted(file_names):
        folder_name = file_name if include_ext else os.path.splitext(file_name)[0]
        if not folder_name:
            continue

        target = os.path.join(output_dir, folder_name)
        if os.path.exists(target):
            log.append(f"[건너뜀] {folder_name}")
            skipped.append(folder_name)
        else:
            if not dry_run:
                os.makedirs(target, exist_ok=True)
            created.append(target)
            prefix = "[미리보기]" if dry_run else "[생성]"
            log.append(f"{prefix} {folder_name}")

    return created, log


# ─── GUI ───────────────────────────────────────────────────────────────────────

class FnfnApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("fnfn - 파일 이름으로 폴더 만들기")
        self.resizable(False, False)
        self._center()
        self._build_ui()

    def _center(self):
        self.update_idletasks()
        w, h = 540, 520
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        PADX = 12

        # ── 원본 폴더 ──────────────────────────────
        frm_src = ttk.LabelFrame(self, text="  📂 원본 폴더 (파일이 있는 폴더)  ")
        frm_src.pack(fill="x", padx=PADX, pady=(14, 4))

        self.src_var = tk.StringVar()
        ttk.Entry(frm_src, textvariable=self.src_var, width=50).pack(
            side="left", padx=8, pady=8, fill="x", expand=True)
        ttk.Button(frm_src, text="찾아보기", command=self._browse_src).pack(
            side="left", padx=(0, 8), pady=8)

        # ── 출력 폴더 ──────────────────────────────
        frm_out = ttk.LabelFrame(self, text="  📁 폴더 생성 위치 (비워두면 원본과 동일)  ")
        frm_out.pack(fill="x", padx=PADX, pady=4)

        self.out_var = tk.StringVar()
        ttk.Entry(frm_out, textvariable=self.out_var, width=50).pack(
            side="left", padx=8, pady=8, fill="x", expand=True)
        ttk.Button(frm_out, text="찾아보기", command=self._browse_out).pack(
            side="left", padx=(0, 8), pady=8)

        # ── 옵션 ───────────────────────────────────
        frm_opt = ttk.LabelFrame(self, text="  ⚙️ 옵션  ")
        frm_opt.pack(fill="x", padx=PADX, pady=4)

        self.ext_var = tk.BooleanVar(value=False)
        self.rec_var = tk.BooleanVar(value=False)
        self.dry_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(frm_opt, text="확장자 포함  (예: image.jpg → 폴더명도 image.jpg)",
                        variable=self.ext_var).pack(anchor="w", padx=12, pady=(8, 2))
        ttk.Checkbutton(frm_opt, text="하위 폴더 파일까지 재귀 탐색",
                        variable=self.rec_var).pack(anchor="w", padx=12, pady=2)
        ttk.Checkbutton(frm_opt, text="미리보기 모드  (실제로 폴더를 만들지 않음)",
                        variable=self.dry_var).pack(anchor="w", padx=12, pady=(2, 8))

        # ── 버튼 ───────────────────────────────────
        frm_btn = ttk.Frame(self)
        frm_btn.pack(fill="x", padx=PADX, pady=6)

        ttk.Button(frm_btn, text="✅  폴더 생성 실행", command=self._run,
                   style="Accent.TButton").pack(side="left", ipadx=10, ipady=4)
        ttk.Button(frm_btn, text="🗑  로그 지우기", command=self._clear_log).pack(
            side="left", padx=8, ipadx=6, ipady=4)

        # ── 로그 ───────────────────────────────────
        frm_log = ttk.LabelFrame(self, text="  📋 실행 결과  ")
        frm_log.pack(fill="both", expand=True, **PAD, pady=(4, 14))

        self.log_box = scrolledtext.ScrolledText(
            frm_log, height=10, state="disabled",
            font=("Consolas", 10), bg="#1e1e1e", fg="#d4d4d4",
            insertbackground="white", relief="flat"
        )
        self.log_box.pack(fill="both", expand=True, padx=6, pady=6)

        # 색상 태그
        self.log_box.tag_config("create", foreground="#4ec9b0")
        self.log_box.tag_config("skip",   foreground="#808080")
        self.log_box.tag_config("info",   foreground="#9cdcfe")
        self.log_box.tag_config("error",  foreground="#f44747")
        self.log_box.tag_config("done",   foreground="#dcdcaa")

    # ── 이벤트 핸들러 ──────────────────────────────

    def _browse_src(self):
        path = filedialog.askdirectory(title="원본 폴더 선택")
        if path:
            self.src_var.set(path)

    def _browse_out(self):
        path = filedialog.askdirectory(title="폴더 생성 위치 선택")
        if path:
            self.out_var.set(path)

    def _clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")

    def _log(self, text, tag="info"):
        self.log_box.config(state="normal")
        self.log_box.insert("end", text + "\n", tag)
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _run(self):
        src = self.src_var.get().strip()
        if not src:
            messagebox.showwarning("경고", "원본 폴더를 선택해주세요.")
            return
        if not os.path.isdir(src):
            messagebox.showerror("오류", f"폴더를 찾을 수 없습니다:\n{src}")
            return

        out = self.out_var.get().strip() or None
        inc_ext = self.ext_var.get()
        recursive = self.rec_var.get()
        dry_run = self.dry_var.get()

        self._log("─" * 48, "info")
        self._log(f"원본 폴더 : {src}", "info")
        self._log(f"생성 위치 : {out or '(원본과 동일)'}", "info")
        self._log(f"이름 모드 : {'확장자 포함' if inc_ext else '확장자 제거'}", "info")
        if dry_run:
            self._log("[미리보기 모드] 실제 폴더를 생성하지 않습니다.", "skip")
        self._log("", "info")

        created, log = create_folders_from_files(
            source_dir=src,
            output_dir=out,
            include_ext=inc_ext,
            recursive=recursive,
            dry_run=dry_run,
        )

        for line in log:
            if line.startswith("[생성]"):
                self._log(line, "create")
            elif line.startswith("[미리보기]"):
                self._log(line, "create")
            elif line.startswith("[건너뜀]"):
                self._log(line, "skip")
            elif line.startswith("[오류]"):
                self._log(line, "error")
            else:
                self._log(line, "info")

        self._log("", "info")
        verb = "생성될 예정" if dry_run else "생성됨"
        self._log(f"✅ 총 {len(created)}개 폴더 {verb}", "done")
        self._log("─" * 48, "info")


# ─── CLI fallback ──────────────────────────────────────────────────────────────

def cli_main():
    parser = argparse.ArgumentParser(prog="fnfn", description="파일 이름으로 빈 폴더를 자동 생성")
    parser.add_argument("source", help="파일을 읽어올 폴더 경로")
    parser.add_argument("--output", "-o", default=None, metavar="OUTPUT_DIR")
    parser.add_argument("--ext", "-e", action="store_true", default=False)
    parser.add_argument("--recursive", "-r", action="store_true", default=False)
    parser.add_argument("--dry-run", "-n", action="store_true", default=False)
    args = parser.parse_args()

    created, log = create_folders_from_files(
        source_dir=args.source,
        output_dir=args.output,
        include_ext=args.ext,
        recursive=args.recursive,
        dry_run=args.dry_run,
    )
    for line in log:
        print(" ", line)
    print(f"\n총 {len(created)}개 폴더를 {'생성할 예정입니다' if args.dry_run else '생성했습니다'}.")


# ─── 엔트리포인트 ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 인자가 있으면 CLI, 없으면 GUI
    if len(sys.argv) > 1:
        cli_main()
    else:
        app = FnfnApp()
        app.mainloop()
