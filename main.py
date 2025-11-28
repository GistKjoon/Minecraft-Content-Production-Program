# -*- coding: utf-8 -*-
import datetime
import json
import math
import os
import platform
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import random
from mc_checklists import RELEASE_CHECKLIST, RECORDING_CHECKLIST
from mc_docs import DOCS
from mc_batch import find_occurrences, replace_in_workspace
from mc_diff import DiffResult, compare_dirs, sync_dirs
from mc_langcheck import check_lang_pack
from mc_log import parse_log
from mc_item import build_give_command, parse_enchants
from mc_lint import lint_workspace
from mc_migration import GUIDE_LINES, apply_migration, backup_before_migrate
from mc_namespace import rename_namespace
from mc_modelcheck import check_models
from mc_presets import PROFILES
from mc_particles import generate_circle_commands, generate_line_commands
from mc_packmeta import bulk_update
from mc_callgraph import build_call_graph, reachable_from, list_functions
from mc_release import generate_changelog, generate_readme, list_packs
from mc_recipe import build_shapeless, shaped_from_grid
from mc_sounds import build_sound_event, parse_sound_list, update_sounds_file
from mc_serverprops import ServerProps, load_properties, save_properties, TARGET_KEYS
from mc_schema import scan_workspace_json, validate_file
from mc_report import build_pack_report
from mc_stats import collect_stats, summarize
from mc_scanner import scan_workspace
from mc_structure import read_nbt
from mc_templates import (
    ADVANCEMENT_SAMPLE,
    CHALLENGE_POOL,
    FUNCTION_SNIPPETS,
    PACK_FORMATS,
    PREDICATE_SAMPLE,
)
from mc_tags import SUPPORTED_CATEGORIES, build_tag_json, save_tag
from mc_schedules import ScheduledCommand, build_schedule
from mc_text import gradient_text_payload


CONFIG_FILE = os.path.join(os.path.dirname(__file__), "mc_helper_settings.json")


class MinecraftToolApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Minecraft 제작 도우미")
        self.root.geometry("1100x740")
        self.root.minsize(1000, 680)

        self.settings = self.load_settings()
        self.workspace_var = tk.StringVar(value=self.settings.get("workspace", ""))
        self.tab_filter_var = tk.StringVar(value="")
        self.language_var = tk.StringVar(value="ko")
        self.tab_label_map: dict[str, dict[str, str]] = {}

        # Builder state
        self.dp_namespace_var = tk.StringVar(value="example")
        self.dp_desc_var = tk.StringVar(value="커스텀 데이터 팩")
        self.dp_format_var = tk.IntVar(value=48)  # 1.21.x 권장
        self.include_load_var = tk.BooleanVar(value=True)
        self.include_tick_var = tk.BooleanVar(value=True)

        self.rp_namespace_var = tk.StringVar(value="example")
        self.rp_desc_var = tk.StringVar(value="커스텀 리소스 팩")
        self.rp_format_var = tk.IntVar(value=34)

        self.loot_item_var = tk.StringVar(value="minecraft:diamond")
        self.loot_weight_var = tk.IntVar(value=1)
        self.loot_min_var = tk.IntVar(value=1)
        self.loot_max_var = tk.IntVar(value=1)
        self.loot_name_var = tk.StringVar(value="my_loot")
        self.loot_namespace_var = tk.StringVar(value="example")

        self.command_output = None
        self.log_widget = None

        # 플래너/타이머/백업
        self.plan_title_var = tk.StringVar(value="새 플랜")
        self.plan_path_var = tk.StringVar(value="")
        self.timer_seconds_var = tk.IntVar(value=300)
        self.timer_running = False
        self.timer_remaining = 0
        self.timer_job = None
        self.world_path_var = tk.StringVar(value="")
        self.challenge_output = None

        # 고급 명령어 빌더
        self.sb_objective_var = tk.StringVar(value="game")
        self.sb_criteria_var = tk.StringVar(value="dummy")
        self.sb_display_slot_var = tk.StringVar(value="sidebar")
        self.sb_player_var = tk.StringVar(value="@a")
        self.sb_value_var = tk.IntVar(value=0)
        self.tag_target_var = tk.StringVar(value="@a")
        self.tag_name_var = tk.StringVar(value="challenge")
        self.gamerule_name_var = tk.StringVar(value="keepInventory")
        self.gamerule_value_var = tk.StringVar(value="true")
        self.title_target_var = tk.StringVar(value="@a")
        self.title_text_var = tk.StringVar(value="시작!")
        self.title_color_var = tk.StringVar(value="yellow")
        self.actionbar_text_var = tk.StringVar(value="액션바 메시지")
        self.effect_id_var = tk.StringVar(value="speed")
        self.effect_dur_var = tk.IntVar(value=30)
        self.effect_amp_var = tk.IntVar(value=1)
        self.effect_hide_var = tk.BooleanVar(value=False)
        self.advanced_output = None

        # 데이터/리소스 고급 도구
        self.snippet_choice = tk.StringVar(value="welcome")
        self.snippet_namespace = tk.StringVar(value="example")
        self.snippet_name = tk.StringVar(value="welcome")
        self.adv_namespace = tk.StringVar(value="example")
        self.adv_name = tk.StringVar(value="first_diamond")
        self.pred_namespace = tk.StringVar(value="example")
        self.pred_name = tk.StringVar(value="holding_diamond_sword")
        self.pack_format_choice = tk.StringVar(value="1.21.x 데이터팩")
        self.validation_output = None
        self.quality_output = None
        self.record_vars = []
        self.release_vars = []
        self.profile_choice = tk.StringVar(value="녹화 기본")
        self.pack_list_dp = None
        self.pack_list_rp = None
        self.lint_output = None
        self.find_text = tk.StringVar(value="execute")
        self.replace_text = tk.StringVar(value="function")
        self.find_output = None
        self.doc_choice = tk.StringVar(value="점수판 설계")
        self.doc_view = None
        self.release_kind_var = tk.StringVar(value="datapacks")
        self.release_pack_var = tk.StringVar(value="")
        self.release_version_var = tk.StringVar(value="v1.0.0")
        self.release_output = None
        self.stats_output = None
        self.server_props_path = tk.StringVar(value="")
        self.server_prop_vars = {k: tk.StringVar(value="") for k in TARGET_KEYS}
        # 레시피 생성
        self.recipe_namespace = tk.StringVar(value="example")
        self.recipe_name = tk.StringVar(value="my_recipe")
        self.recipe_result = tk.StringVar(value="minecraft:diamond")
        self.recipe_count = tk.IntVar(value=1)
        self.recipe_grid = [tk.StringVar(value="") for _ in range(9)]
        self.shapeless_items = tk.StringVar(value="minecraft:stick, minecraft:coal")
        self.recipe_output = None
        # 파티클 생성
        self.particle_id = tk.StringVar(value="minecraft:happy_villager")
        self.particle_count = tk.IntVar(value=1)
        self.particle_speed = tk.DoubleVar(value=0.01)
        self.line_start = [tk.StringVar(value="0"), tk.StringVar(value="64"), tk.StringVar(value="0")]
        self.line_end = [tk.StringVar(value="5"), tk.StringVar(value="64"), tk.StringVar(value="5")]
        self.line_steps = tk.IntVar(value=10)
        self.circle_center = [tk.StringVar(value="0"), tk.StringVar(value="64"), tk.StringVar(value="0")]
        self.circle_radius = tk.DoubleVar(value=3.0)
        self.circle_points = tk.IntVar(value=24)
        self.particle_output = None
        # 텍스트/그라디언트
        self.grad_text_var = tk.StringVar(value="그라디언트 텍스트")
        self.grad_color1_var = tk.StringVar(value="#ff0000")
        self.grad_color2_var = tk.StringVar(value="#00ffcc")
        self.grad_bold_var = tk.BooleanVar(value=True)
        self.grad_italic_var = tk.BooleanVar(value=False)
        self.text_target_var = tk.StringVar(value="@a")
        self.text_output = None
        # 태그/pack.mcmeta
        self.tag_namespace = tk.StringVar(value="example")
        self.tag_category = tk.StringVar(value="blocks")
        self.tag_name = tk.StringVar(value="custom_tag")
        self.tag_replace = tk.BooleanVar(value=False)
        self.tag_entries = tk.StringVar(value="minecraft:stone, minecraft:dirt")
        self.tag_output = None
        self.meta_format_var = tk.IntVar(value=48)
        self.meta_desc_var = tk.StringVar(value="업데이트된 팩")
        self.meta_output = None
        # 비교/동기화
        self.diff_src = tk.StringVar(value="")
        self.diff_dst = tk.StringVar(value="")
        self.diff_output = None
        self.diff_last: DiffResult | None = None
        # 마이그레이션/예약 실행
        self.migrate_kind = tk.StringVar(value="datapacks")
        self.migrate_output = None
        self.schedule_namespace = tk.StringVar(value="example")
        self.schedule_name = tk.StringVar(value="timers")
        self.schedule_entries = tk.StringVar(value="tick:20, tick:200")
        self.schedule_output = None
        # 아이템/NBT
        self.item_target = tk.StringVar(value="@p")
        self.item_id = tk.StringVar(value="minecraft:netherite_sword")
        self.item_count = tk.IntVar(value=1)
        self.item_name = tk.StringVar(value="전설의 검")
        self.item_color = tk.StringVar(value="#00ffff")
        self.item_italic = tk.BooleanVar(value=False)
        self.item_lore = tk.StringVar(value="강력한 힘,광휘를 내뿜는다")
        self.item_enchants = tk.StringVar(value="sharpness:5, unbreaking:3")
        self.item_output = None
        # 사운드/sounds.json
        self.sound_namespace = tk.StringVar(value="example")
        self.sound_event = tk.StringVar(value="custom.boop")
        self.sound_files = tk.StringVar(value="sounds/boop1, sounds/boop2")
        self.sound_subtitle = tk.StringVar(value="커스텀 소리")
        self.sound_replace = tk.BooleanVar(value=False)
        self.sound_output = None
        # 로그/언어
        self.log_path_var = tk.StringVar(value="")
        self.log_output = None
        self.lang_pack_var = tk.StringVar(value="")
        self.lang_output = None
        # JSON/모델 검사
        self.schema_file_var = tk.StringVar(value="")
        self.schema_output = None
        self.model_pack_var = tk.StringVar(value="")
        self.model_output = None
        # 네임스페이스/리포트
        self.ns_old = tk.StringVar(value="example")
        self.ns_new = tk.StringVar(value="mynewpack")
        self.ns_output = None
        self.report_output = None
        # 구조 NBT
        self.nbt_path_var = tk.StringVar(value="")
        self.nbt_output = None
        # 함수 그래프
        self.graph_start = tk.StringVar(value="")
        self.graph_depth = tk.IntVar(value=5)
        self.graph_output = None

        self.build_ui()
        self.log("도구가 준비되었습니다. 워크스페이스를 지정하면 생성/백업/플랜 저장이 편해집니다.")

    # --- 기본 설정 ---
    def load_settings(self):
        if not os.path.exists(CONFIG_FILE):
            return {}
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_settings(self):
        data = {"workspace": self.workspace_var.get().strip()}
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            messagebox.showerror("저장 실패", f"설정 파일을 저장하지 못했습니다: {exc}")

    def log(self, message: str):
        stamp = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {message}"
        if self.log_widget:
            self.log_widget.insert(tk.END, line + "\n")
            self.log_widget.see(tk.END)
        print(line)

    # --- UI 구성 ---
    def build_ui(self):
        style = ttk.Style(self.root)
        style.layout("Hidden.TNotebook.Tab", [])
        style.configure("Hidden.TNotebook", tabmargins=(0, 0, 0, 0))
        style.configure("TabButton.TButton", padding=(6, 4))
        style.configure("TabButtonActive.TButton", padding=(6, 4), relief="sunken")

        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        # 상단: 탭 검색 + 버튼 줄
        top_bar = ttk.Frame(container)
        top_bar.pack(fill="x", padx=10, pady=(10, 0))
        ttk.Label(top_bar, text="탭 검색").pack(side="left")
        search_entry = ttk.Entry(top_bar, textvariable=self.tab_filter_var, width=24)
        search_entry.pack(side="left", padx=6)
        search_entry.bind("<KeyRelease>", lambda e: self.rebuild_tab_bar())

        lang_frame = ttk.Frame(top_bar)
        lang_frame.pack(side="right")
        ttk.Label(lang_frame, text="언어").pack(side="left", padx=(0, 4))
        lang_box = ttk.Combobox(lang_frame, state="readonly", width=10, values=["한국어", "English"])
        lang_box.pack(side="left")
        lang_box.set("한국어")
        lang_box.bind("<<ComboboxSelected>>", lambda e: self.change_language(lang_box.get()))

        self.tab_bar = ttk.Frame(container)
        self.tab_bar.pack(fill="x", padx=10, pady=(10, 0))

        self.notebook = ttk.Notebook(container, style="Hidden.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.highlight_tab_buttons())

        # 탭 생성
        self.create_project_tab(self.notebook)
        self.create_creator_tab(self.notebook)
        self.create_calc_tab(self.notebook)
        self.create_command_tab(self.notebook)
        self.create_advanced_tab(self.notebook)
        self.create_pack_tab(self.notebook)
        self.create_dev_tools_tab(self.notebook)
        self.create_quality_tab(self.notebook)
        self.create_automation_tab(self.notebook)
        self.create_maintenance_tab(self.notebook)
        self.create_release_tab(self.notebook)
        self.create_stats_tab(self.notebook)
        self.create_server_tab(self.notebook)
        self.create_recipe_tab(self.notebook)
        self.create_particle_tab(self.notebook)
        self.create_text_tab(self.notebook)
        self.create_tag_meta_tab(self.notebook)
        self.create_diff_tab(self.notebook)
        self.create_migration_tab(self.notebook)
        self.create_item_tab(self.notebook)
        self.create_sound_tab(self.notebook)
        self.create_log_lang_tab(self.notebook)
        self.create_schema_model_tab(self.notebook)
        self.create_namespace_report_tab(self.notebook)
        self.create_structure_tab(self.notebook)
        self.create_callgraph_tab(self.notebook)

        self.setup_tab_labels()
        self.rebuild_tab_bar()

    # --- 탭: 프로젝트 허브 ---
    def create_project_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="프로젝트 허브")

        # 워크스페이스 선택
        ws_box = ttk.LabelFrame(frame, text="워크스페이스 (루트 경로를 지정하면 저장/생성이 편해집니다)")
        ws_box.pack(fill="x", pady=5)

        ws_row = ttk.Frame(ws_box)
        ws_row.pack(fill="x", pady=4)
        ttk.Label(ws_row, text="경로:").pack(side="left")
        ws_entry = ttk.Entry(ws_row, textvariable=self.workspace_var)
        ws_entry.pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(ws_row, text="폴더 선택", command=self.select_workspace).pack(side="left", padx=4)
        ttk.Button(ws_row, text="저장", command=self.save_settings).pack(side="left")

        btn_row = ttk.Frame(ws_box)
        btn_row.pack(fill="x", pady=4)
        ttk.Button(btn_row, text="데이터 팩 폴더 열기", command=self.open_datapacks_dir).pack(side="left", padx=2)
        ttk.Button(btn_row, text="리소스 팩 폴더 열기", command=self.open_resourcepacks_dir).pack(side="left", padx=2)
        ttk.Button(btn_row, text="터미널에서 열기", command=self.open_in_terminal).pack(side="left", padx=2)

        # 로그 & 안내
        lower = ttk.Frame(frame)
        lower.pack(fill="both", expand=True, pady=10)

        log_box = ttk.LabelFrame(lower, text="작업 로그")
        log_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.log_widget = tk.Text(log_box, height=10, wrap="word")
        self.log_widget.pack(fill="both", expand=True, padx=6, pady=6)

        tips = ttk.LabelFrame(lower, text="빠른 아이디어")
        tips.pack(side="left", fill="both", expand=True)
        tip_text = (
            "- 워크스페이스를 설정해 두면 모든 생성기가 해당 경로로 저장됩니다.\n"
            "- 데이터 팩 템플릿을 만든 뒤 functions 폴더 안에 mcfunction을 추가하세요.\n"
            "- 좌표 변환기로 네더/오버월드 이동 거리를 즉시 계산할 수 있습니다.\n"
            "- 명령어 탭에서 자주 쓰는 summon/give/tellraw를 빠르게 생성해 복사하세요.\n"
            "- Loot Table 빌더로 샘플 드롭 JSON을 만든 뒤 data/<namespace>/loot_tables에 두세요."
        )
        tk.Label(tips, text=tip_text, justify="left", anchor="nw").pack(fill="both", expand=True, padx=6, pady=6)

    def select_workspace(self):
        path = filedialog.askdirectory(title="워크스페이스 선택")
        if path:
            self.workspace_var.set(path)
            self.save_settings()
            self.log(f"워크스페이스 설정: {path}")

    def open_datapacks_dir(self):
        base = self.ensure_workspace()
        if not base:
            return
        target = os.path.join(base, "datapacks")
        os.makedirs(target, exist_ok=True)
        self.open_folder(target)

    def open_resourcepacks_dir(self):
        base = self.ensure_workspace()
        if not base:
            return
        target = os.path.join(base, "resourcepacks")
        os.makedirs(target, exist_ok=True)
        self.open_folder(target)

    def open_in_terminal(self):
        base = self.ensure_workspace()
        if not base:
            return
        if platform.system() == "Darwin":
            subprocess.call(["open", "-a", "Terminal", base])
        elif platform.system() == "Windows":
            os.startfile(base)  # type: ignore[attr-defined]
        else:
            subprocess.call(["xdg-open", base])
        self.log(f"터미널/탐색기에서 열기: {base}")

    def open_folder(self, path: str):
        if platform.system() == "Darwin":
            subprocess.call(["open", path])
        elif platform.system() == "Windows":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.call(["xdg-open", path])
        self.log(f"폴더 열기: {path}")

    def ensure_workspace(self) -> str | None:
        path = self.workspace_var.get().strip()
        if not path:
            messagebox.showwarning("워크스페이스 필요", "먼저 워크스페이스(루트 경로)를 지정해주세요.")
            return None
        return path

    # --- 탭: 크리에이터 유틸 (플랜/랜덤 챌린지/타이머/백업) ---
    def create_creator_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="크리에이터 유틸")

        # 콘텐츠 플랜
        plan_box = ttk.LabelFrame(frame, text="콘텐츠 플랜 (아이디어/할일 메모)")
        plan_box.pack(fill="both", expand=True, pady=6)
        plan_top = ttk.Frame(plan_box)
        plan_top.pack(fill="x", pady=4)
        ttk.Label(plan_top, text="제목").pack(side="left")
        ttk.Entry(plan_top, textvariable=self.plan_title_var, width=24).pack(side="left", padx=4)
        ttk.Button(plan_top, text="저장", command=self.save_plan).pack(side="left", padx=2)
        ttk.Button(plan_top, text="불러오기", command=self.load_plan).pack(side="left", padx=2)
        ttk.Button(plan_top, text="샘플 문구 추가", command=self.insert_sample_prompt).pack(side="left", padx=2)

        self.plan_text = tk.Text(plan_box, height=12, wrap="word")
        self.plan_text.pack(fill="both", expand=True, padx=6, pady=4)

        # 랜덤 챌린지/아이디어
        idea_box = ttk.LabelFrame(frame, text="랜덤 챌린지/아이디어")
        idea_box.pack(fill="x", pady=6)
        ttk.Button(idea_box, text="챌린지 3개 뽑기", command=self.roll_challenges).pack(side="left", padx=4, pady=4)
        self.challenge_output = tk.Text(idea_box, height=5, wrap="word")
        self.challenge_output.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        # 타이머/카운트다운
        timer_box = ttk.LabelFrame(frame, text="촬영용 카운트다운/세그먼트 타이머")
        timer_box.pack(fill="x", pady=6)
        t_row = ttk.Frame(timer_box)
        t_row.pack(fill="x", pady=4)
        ttk.Label(t_row, text="초").pack(side="left")
        ttk.Entry(t_row, textvariable=self.timer_seconds_var, width=8).pack(side="left", padx=4)
        ttk.Button(t_row, text="시작", command=self.start_timer).pack(side="left", padx=2)
        ttk.Button(t_row, text="정지", command=self.stop_timer).pack(side="left", padx=2)
        ttk.Button(t_row, text="리셋", command=self.reset_timer).pack(side="left", padx=2)
        self.timer_label = ttk.Label(t_row, text="남은 시간: 00:00")
        self.timer_label.pack(side="left", padx=10)

        # 월드 백업/압축
        backup_box = ttk.LabelFrame(frame, text="월드 백업 (zip)")
        backup_box.pack(fill="x", pady=6)
        b_row1 = ttk.Frame(backup_box)
        b_row1.pack(fill="x", pady=3)
        ttk.Label(b_row1, text="월드 폴더").pack(side="left")
        ttk.Entry(b_row1, textvariable=self.world_path_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(b_row1, text="폴더 선택", command=self.select_world_folder).pack(side="left", padx=2)
        b_row2 = ttk.Frame(backup_box)
        b_row2.pack(fill="x", pady=3)
        ttk.Button(b_row2, text="백업(zip) 만들기", command=self.create_world_backup).pack(side="left", padx=4)
        ttk.Button(b_row2, text="저장 위치 열기", command=self.open_world_parent).pack(side="left", padx=4)

    def save_plan(self):
        title = self.plan_title_var.get().strip() or "plan"
        content = self.plan_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("내용 없음", "플랜 내용을 입력하세요.")
            return
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.safe_filename(title)}_{timestamp}.json"
        base = self.workspace_var.get().strip()
        if base:
            plan_dir = os.path.join(base, "creator_plans")
            os.makedirs(plan_dir, exist_ok=True)
            path = os.path.join(plan_dir, filename)
        else:
            path = filedialog.asksaveasfilename(
                title="플랜 저장",
                defaultextension=".json",
                initialfile=filename,
                filetypes=[("JSON", "*.json"), ("All", "*.*")],
            )
            if not path:
                return
        data = {"title": title, "content": content, "saved_at": timestamp}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.plan_path_var.set(path)
        self.log(f"플랜 저장: {path}")
        messagebox.showinfo("저장 완료", f"플랜이 저장되었습니다:\n{path}")

    def load_plan(self):
        path = filedialog.askopenfilename(
            title="플랜 불러오기",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.plan_title_var.set(data.get("title", "플랜"))
            self.plan_text.delete("1.0", tk.END)
            self.plan_text.insert(tk.END, data.get("content", ""))
            self.plan_path_var.set(path)
            self.log(f"플랜 불러오기: {path}")
        except Exception as exc:
            messagebox.showerror("불러오기 실패", str(exc))

    def insert_sample_prompt(self):
        samples = [
            "인트로: 훅 10초 / 메인: 목표 설명 / 엔딩: 다음화 예고",
            "필수 컷: 보스 격파 리액션, 인벤토리 공개, 시드 공개 여부 체크",
            "미션: 시청자 댓글 3개 반영, 채널 멤버 이름 NPC로 소환",
            "사전 셋업: keepInventory, 난이도 확인, seed 기록, 백업 완료",
        ]
        pick = random.choice(samples)
        self.plan_text.insert(tk.END, "\n- " + pick)

    def roll_challenges(self):
        pool = CHALLENGE_POOL
        picks = random.sample(pool, k=min(3, len(pool)))
        self.challenge_output.delete("1.0", tk.END)
        for idx, ch in enumerate(picks, start=1):
            self.challenge_output.insert(tk.END, f"{idx}. {ch}\n")
        self.log(f"랜덤 챌린지: {', '.join(picks)}")

    def start_timer(self):
        if self.timer_running:
            return
        self.timer_remaining = max(0, self.timer_seconds_var.get())
        self.timer_running = True
        self.update_timer_label()
        self.tick_timer()

    def tick_timer(self):
        if not self.timer_running:
            return
        mins, secs = divmod(self.timer_remaining, 60)
        self.timer_label.config(text=f"남은 시간: {mins:02d}:{secs:02d}")
        if self.timer_remaining <= 0:
            self.root.bell()
            self.timer_running = False
            self.log("타이머 종료")
            return
        self.timer_remaining -= 1
        self.timer_job = self.root.after(1000, self.tick_timer)

    def stop_timer(self):
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
        self.timer_running = False
        self.log("타이머 정지")

    def reset_timer(self):
        self.stop_timer()
        total = max(0, self.timer_seconds_var.get())
        mins, secs = divmod(total, 60)
        self.timer_label.config(text=f"남은 시간: {mins:02d}:{secs:02d}")
        self.log("타이머 리셋")

    def select_world_folder(self):
        path = filedialog.askdirectory(title="월드 폴더 선택")
        if path:
            self.world_path_var.set(path)
            self.log(f"월드 경로 선택: {path}")

    def open_world_parent(self):
        world = self.world_path_var.get().strip()
        if not world:
            return
        parent = os.path.dirname(world)
        if os.path.isdir(parent):
            self.open_folder(parent)

    def create_world_backup(self):
        world = self.world_path_var.get().strip()
        if not world or not os.path.isdir(world):
            messagebox.showwarning("경로 확인", "유효한 월드 폴더를 선택하세요.")
            return
        parent = os.path.dirname(world)
        base_name = os.path.basename(world.rstrip(os.sep))
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_base = os.path.join(parent, f"{base_name}_backup_{stamp}")
        zip_path = shutil.make_archive(out_base, "zip", root_dir=world)
        self.log(f"백업 생성: {zip_path}")
        messagebox.showinfo("백업 완료", f"백업 파일이 생성되었습니다:\n{zip_path}")
        self.open_folder(parent)

    def safe_filename(self, name: str) -> str:
        return "".join(c for c in name if c.isalnum() or c in ("-", "_")) or "untitled"

    # --- 탭: 좌표/시간 계산 ---
    def create_calc_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="좌표/시간 계산기")

        convert_box = ttk.LabelFrame(frame, text="네더 ↔ 오버월드 변환 (x,z만 8배 스케일)")
        convert_box.pack(fill="x", pady=5)
        c_row1 = ttk.Frame(convert_box)
        c_row1.pack(fill="x", pady=3)
        self.over_x = tk.StringVar(value="0")
        self.over_z = tk.StringVar(value="0")
        ttk.Label(c_row1, text="오버월드 X").pack(side="left")
        ttk.Entry(c_row1, textvariable=self.over_x, width=10).pack(side="left", padx=3)
        ttk.Label(c_row1, text="Z").pack(side="left")
        ttk.Entry(c_row1, textvariable=self.over_z, width=10).pack(side="left", padx=3)
        ttk.Button(c_row1, text="→ 네더 변환", command=self.convert_over_to_nether).pack(side="left", padx=6)
        self.nether_result = tk.StringVar(value="네더 좌표: -")
        ttk.Label(c_row1, textvariable=self.nether_result).pack(side="left", padx=6)

        c_row2 = ttk.Frame(convert_box)
        c_row2.pack(fill="x", pady=3)
        self.nether_x = tk.StringVar(value="0")
        self.nether_z = tk.StringVar(value="0")
        ttk.Label(c_row2, text="네더 X").pack(side="left")
        ttk.Entry(c_row2, textvariable=self.nether_x, width=10).pack(side="left", padx=3)
        ttk.Label(c_row2, text="Z").pack(side="left")
        ttk.Entry(c_row2, textvariable=self.nether_z, width=10).pack(side="left", padx=3)
        ttk.Button(c_row2, text="→ 오버월드 변환", command=self.convert_nether_to_over).pack(side="left", padx=6)
        self.over_result = tk.StringVar(value="오버월드 좌표: -")
        ttk.Label(c_row2, textvariable=self.over_result).pack(side="left", padx=6)

        dist_box = ttk.LabelFrame(frame, text="거리/시간 계산")
        dist_box.pack(fill="x", pady=8)
        d_row = ttk.Frame(dist_box)
        d_row.pack(fill="x", pady=3)
        self.x1 = tk.StringVar(value="0")
        self.y1 = tk.StringVar(value="64")
        self.z1 = tk.StringVar(value="0")
        self.x2 = tk.StringVar(value="0")
        self.y2 = tk.StringVar(value="64")
        self.z2 = tk.StringVar(value="0")
        for label, var in [("X1", self.x1), ("Y1", self.y1), ("Z1", self.z1), ("X2", self.x2), ("Y2", self.y2), ("Z2", self.z2)]:
            ttk.Label(d_row, text=label).pack(side="left")
            ttk.Entry(d_row, textvariable=var, width=8).pack(side="left", padx=2)
        ttk.Button(d_row, text="거리 계산", command=self.calculate_distance).pack(side="left", padx=6)
        self.distance_result = tk.StringVar(value="결과: -")
        ttk.Label(d_row, textvariable=self.distance_result).pack(side="left", padx=6)

        tick_box = ttk.LabelFrame(frame, text="틱/시간 변환")
        tick_box.pack(fill="x", pady=8)
        t_row = ttk.Frame(tick_box)
        t_row.pack(fill="x", pady=3)
        self.ticks_var = tk.StringVar(value="20")
        self.seconds_var = tk.StringVar(value="1")
        ttk.Label(t_row, text="틱 → 초").pack(side="left")
        ttk.Entry(t_row, textvariable=self.ticks_var, width=10).pack(side="left", padx=2)
        ttk.Button(t_row, text="계산", command=self.ticks_to_seconds).pack(side="left", padx=4)
        ttk.Label(t_row, text="초 → 틱").pack(side="left", padx=(12, 2))
        ttk.Entry(t_row, textvariable=self.seconds_var, width=10).pack(side="left", padx=2)
        ttk.Button(t_row, text="계산", command=self.seconds_to_ticks).pack(side="left", padx=4)
        self.tick_result = tk.StringVar(value="20틱 = 1초")
        ttk.Label(t_row, textvariable=self.tick_result).pack(side="left", padx=8)

    def convert_over_to_nether(self):
        try:
            x = float(self.over_x.get())
            z = float(self.over_z.get())
            nx = round(x / 8, 3)
            nz = round(z / 8, 3)
            self.nether_result.set(f"네더 좌표: {nx}, {nz}")
            self.log(f"오버월드({x}, {z}) → 네더({nx}, {nz})")
        except ValueError:
            messagebox.showerror("입력 오류", "숫자를 정확히 입력해주세요.")

    def convert_nether_to_over(self):
        try:
            x = float(self.nether_x.get())
            z = float(self.nether_z.get())
            ox = round(x * 8, 3)
            oz = round(z * 8, 3)
            self.over_result.set(f"오버월드 좌표: {ox}, {oz}")
            self.log(f"네더({x}, {z}) → 오버월드({ox}, {oz})")
        except ValueError:
            messagebox.showerror("입력 오류", "숫자를 정확히 입력해주세요.")

    def calculate_distance(self):
        try:
            p1 = (float(self.x1.get()), float(self.y1.get()), float(self.z1.get()))
            p2 = (float(self.x2.get()), float(self.y2.get()), float(self.z2.get()))
            dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))
            self.distance_result.set(f"결과: {dist:.2f} 블록")
            self.log(f"거리 계산: {p1} → {p2} = {dist:.2f}")
        except ValueError:
            messagebox.showerror("입력 오류", "숫자를 정확히 입력해주세요.")

    def ticks_to_seconds(self):
        try:
            ticks = float(self.ticks_var.get())
            seconds = ticks / 20
            self.tick_result.set(f"{ticks}틱 ≈ {seconds:.2f}초")
        except ValueError:
            messagebox.showerror("입력 오류", "숫자를 정확히 입력해주세요.")

    def seconds_to_ticks(self):
        try:
            seconds = float(self.seconds_var.get())
            ticks = seconds * 20
            self.tick_result.set(f"{seconds}초 ≈ {ticks:.0f}틱")
        except ValueError:
            messagebox.showerror("입력 오류", "숫자를 정확히 입력해주세요.")

    # --- 탭: 명령어/JSON 생성 ---
    def create_command_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="명령어 & JSON 생성")

        left = ttk.Frame(frame)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Summon
        summon_box = ttk.LabelFrame(left, text="/summon 빌더")
        summon_box.pack(fill="x", pady=4)
        self.summon_entity = tk.StringVar(value="minecraft:zombie")
        self.summon_x = tk.StringVar(value="~")
        self.summon_y = tk.StringVar(value="~")
        self.summon_z = tk.StringVar(value="~")
        self.summon_nbt = tk.StringVar(value="")
        s_row1 = ttk.Frame(summon_box)
        s_row1.pack(fill="x", pady=3)
        ttk.Label(s_row1, text="엔티티 ID").pack(side="left")
        ttk.Entry(s_row1, textvariable=self.summon_entity, width=20).pack(side="left", padx=4)
        ttk.Label(s_row1, text="좌표 x y z").pack(side="left", padx=(6, 2))
        for var in [self.summon_x, self.summon_y, self.summon_z]:
            ttk.Entry(s_row1, textvariable=var, width=8).pack(side="left", padx=2)
        s_row2 = ttk.Frame(summon_box)
        s_row2.pack(fill="x", pady=3)
        ttk.Label(s_row2, text="NBT (선택)").pack(side="left")
        ttk.Entry(s_row2, textvariable=self.summon_nbt, width=60).pack(side="left", padx=4)
        ttk.Button(s_row2, text="명령어 생성", command=self.build_summon).pack(side="left", padx=4)

        # Give
        give_box = ttk.LabelFrame(left, text="/give 빌더")
        give_box.pack(fill="x", pady=4)
        self.give_player = tk.StringVar(value="@p")
        self.give_item = tk.StringVar(value="minecraft:stick")
        self.give_count = tk.IntVar(value=1)
        self.give_nbt = tk.StringVar(value="")
        g_row1 = ttk.Frame(give_box)
        g_row1.pack(fill="x", pady=3)
        ttk.Label(g_row1, text="대상").pack(side="left")
        ttk.Entry(g_row1, textvariable=self.give_player, width=10).pack(side="left", padx=4)
        ttk.Label(g_row1, text="아이템 ID").pack(side="left")
        ttk.Entry(g_row1, textvariable=self.give_item, width=22).pack(side="left", padx=4)
        ttk.Label(g_row1, text="수량").pack(side="left")
        ttk.Entry(g_row1, textvariable=self.give_count, width=6).pack(side="left", padx=4)
        g_row2 = ttk.Frame(give_box)
        g_row2.pack(fill="x", pady=3)
        ttk.Label(g_row2, text="NBT (선택)").pack(side="left")
        ttk.Entry(g_row2, textvariable=self.give_nbt, width=60).pack(side="left", padx=4)
        ttk.Button(g_row2, text="명령어 생성", command=self.build_give).pack(side="left", padx=4)

        # Tellraw
        tell_box = ttk.LabelFrame(left, text="/tellraw 빌더")
        tell_box.pack(fill="x", pady=4)
        self.tell_target = tk.StringVar(value="@a")
        self.tell_message = tk.StringVar(value="메시지를 입력하세요")
        self.tell_color = tk.StringVar(value="gold")
        tr_row1 = ttk.Frame(tell_box)
        tr_row1.pack(fill="x", pady=3)
        ttk.Label(tr_row1, text="대상").pack(side="left")
        ttk.Entry(tr_row1, textvariable=self.tell_target, width=10).pack(side="left", padx=4)
        ttk.Label(tr_row1, text="색상").pack(side="left")
        ttk.Entry(tr_row1, textvariable=self.tell_color, width=10).pack(side="left", padx=4)
        tr_row2 = ttk.Frame(tell_box)
        tr_row2.pack(fill="x", pady=3)
        ttk.Label(tr_row2, text="메시지").pack(side="left")
        ttk.Entry(tr_row2, textvariable=self.tell_message, width=60).pack(side="left", padx=4)
        ttk.Button(tr_row2, text="명령어 생성", command=self.build_tellraw).pack(side="left", padx=4)

        # 출력
        out_box = ttk.LabelFrame(frame, text="미리보기 / 복사")
        out_box.pack(side="left", fill="both", expand=True)
        self.command_output = tk.Text(out_box, height=20, wrap="word")
        self.command_output.pack(fill="both", expand=True, padx=6, pady=6)
        out_btns = ttk.Frame(out_box)
        out_btns.pack(fill="x", pady=(0, 6))
        ttk.Button(out_btns, text="클립보드 복사", command=self.copy_output).pack(side="left", padx=4)
        ttk.Button(out_btns, text="모두 지우기", command=lambda: self.command_output.delete("1.0", tk.END)).pack(side="left", padx=4)

    def build_summon(self):
        entity = self.summon_entity.get().strip()
        coords = f"{self.summon_x.get()} {self.summon_y.get()} {self.summon_z.get()}"
        nbt = self.summon_nbt.get().strip()
        cmd = f"summon {entity} {coords}"
        if nbt:
            cmd += f" {nbt}"
        self.set_output(cmd)
        self.log(f"/summon 생성: {cmd}")

    def build_give(self):
        target = self.give_player.get().strip()
        item = self.give_item.get().strip()
        count = self.give_count.get()
        nbt = self.give_nbt.get().strip()
        item_full = f"{item}{nbt if nbt else ''}"
        cmd = f"give {target} {item_full} {count}"
        self.set_output(cmd)
        self.log(f"/give 생성: {cmd}")

    def build_tellraw(self):
        target = self.tell_target.get().strip()
        text = self.tell_message.get().strip()
        color = self.tell_color.get().strip()
        payload = {"text": text}
        if color:
            payload["color"] = color
        cmd = f"tellraw {target} {json.dumps(payload, ensure_ascii=False)}"
        self.set_output(cmd)
        self.log(f"/tellraw 생성: {cmd}")

    def set_output(self, content: str):
        self.command_output.delete("1.0", tk.END)
        self.command_output.insert(tk.END, content)

    def copy_output(self):
        text = self.command_output.get("1.0", tk.END).strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("복사 완료", "클립보드에 복사되었습니다.")

    # --- 탭: 고급 명령어/매크로 ---
    def create_advanced_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="고급 명령어")

        left = ttk.Frame(frame)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        sb_box = ttk.LabelFrame(left, text="스코어보드/태그/게임룰")
        sb_box.pack(fill="x", pady=4)
        sb_row1 = ttk.Frame(sb_box)
        sb_row1.pack(fill="x", pady=2)
        ttk.Label(sb_row1, text="objective").pack(side="left")
        ttk.Entry(sb_row1, textvariable=self.sb_objective_var, width=12).pack(side="left", padx=3)
        ttk.Label(sb_row1, text="criteria").pack(side="left")
        ttk.Entry(sb_row1, textvariable=self.sb_criteria_var, width=12).pack(side="left", padx=3)
        ttk.Button(sb_row1, text="생성", command=self.build_scoreboard_add).pack(side="left", padx=3)

        sb_row2 = ttk.Frame(sb_box)
        sb_row2.pack(fill="x", pady=2)
        ttk.Label(sb_row2, text="표시 슬롯").pack(side="left")
        ttk.Entry(sb_row2, textvariable=self.sb_display_slot_var, width=10).pack(side="left", padx=3)
        ttk.Button(sb_row2, text="표시 설정", command=self.build_scoreboard_display).pack(side="left", padx=3)

        sb_row3 = ttk.Frame(sb_box)
        sb_row3.pack(fill="x", pady=2)
        ttk.Label(sb_row3, text="플레이어/값").pack(side="left")
        ttk.Entry(sb_row3, textvariable=self.sb_player_var, width=12).pack(side="left", padx=3)
        ttk.Entry(sb_row3, textvariable=self.sb_value_var, width=8).pack(side="left", padx=3)
        ttk.Button(sb_row3, text="set/add", command=self.build_scoreboard_value).pack(side="left", padx=3)

        tag_row = ttk.Frame(sb_box)
        tag_row.pack(fill="x", pady=2)
        ttk.Label(tag_row, text="tag 대상/이름").pack(side="left")
        ttk.Entry(tag_row, textvariable=self.tag_target_var, width=12).pack(side="left", padx=3)
        ttk.Entry(tag_row, textvariable=self.tag_name_var, width=12).pack(side="left", padx=3)
        ttk.Button(tag_row, text="추가", command=lambda: self.build_tag(True)).pack(side="left", padx=2)
        ttk.Button(tag_row, text="제거", command=lambda: self.build_tag(False)).pack(side="left", padx=2)

        gr_row = ttk.Frame(sb_box)
        gr_row.pack(fill="x", pady=2)
        ttk.Label(gr_row, text="gamerule").pack(side="left")
        ttk.Entry(gr_row, textvariable=self.gamerule_name_var, width=16).pack(side="left", padx=3)
        ttk.Entry(gr_row, textvariable=self.gamerule_value_var, width=10).pack(side="left", padx=3)
        ttk.Button(gr_row, text="설정", command=self.build_gamerule).pack(side="left", padx=3)

        msg_box = ttk.LabelFrame(left, text="타이틀/액션바/이펙트")
        msg_box.pack(fill="x", pady=4)
        title_row = ttk.Frame(msg_box)
        title_row.pack(fill="x", pady=2)
        ttk.Label(title_row, text="대상").pack(side="left")
        ttk.Entry(title_row, textvariable=self.title_target_var, width=10).pack(side="left", padx=3)
        ttk.Label(title_row, text="텍스트").pack(side="left")
        ttk.Entry(title_row, textvariable=self.title_text_var, width=28).pack(side="left", padx=3)
        ttk.Label(title_row, text="색").pack(side="left")
        ttk.Entry(title_row, textvariable=self.title_color_var, width=8).pack(side="left", padx=3)
        ttk.Button(title_row, text="title", command=self.build_title).pack(side="left", padx=2)
        ttk.Button(title_row, text="actionbar", command=self.build_actionbar).pack(side="left", padx=2)

        eff_row = ttk.Frame(msg_box)
        eff_row.pack(fill="x", pady=2)
        ttk.Label(eff_row, text="effect").pack(side="left")
        ttk.Entry(eff_row, textvariable=self.effect_id_var, width=14).pack(side="left", padx=3)
        ttk.Label(eff_row, text="초").pack(side="left")
        ttk.Entry(eff_row, textvariable=self.effect_dur_var, width=6).pack(side="left", padx=3)
        ttk.Label(eff_row, text="증폭").pack(side="left")
        ttk.Entry(eff_row, textvariable=self.effect_amp_var, width=6).pack(side="left", padx=3)
        ttk.Checkbutton(eff_row, text="입자 숨김", variable=self.effect_hide_var).pack(side="left", padx=3)
        ttk.Button(eff_row, text="부여", command=self.build_effect).pack(side="left", padx=2)

        macro_box = ttk.LabelFrame(left, text="매크로 프리셋 (방송/녹화 세트)")
        macro_box.pack(fill="x", pady=4)
        ttk.Button(macro_box, text="기본 세션 세트 생성", command=self.build_macro_session).pack(side="left", padx=3, pady=4)
        ttk.Button(macro_box, text="하드코어 도전 세트", command=self.build_macro_hardcore).pack(side="left", padx=3, pady=4)

        out_box = ttk.LabelFrame(frame, text="미리보기 / 복사")
        out_box.pack(side="left", fill="both", expand=True)
        self.advanced_output = tk.Text(out_box, height=20, wrap="word")
        self.advanced_output.pack(fill="both", expand=True, padx=6, pady=6)
        adv_btns = ttk.Frame(out_box)
        adv_btns.pack(fill="x", pady=(0, 6))
        ttk.Button(adv_btns, text="클립보드 복사", command=self.copy_advanced_output).pack(side="left", padx=4)
        ttk.Button(adv_btns, text="모두 지우기", command=lambda: self.advanced_output.delete("1.0", tk.END)).pack(side="left", padx=4)

    def build_scoreboard_add(self):
        obj = self.sb_objective_var.get().strip()
        crit = self.sb_criteria_var.get().strip()
        if not obj or not crit:
            messagebox.showwarning("입력 필요", "objective와 criteria를 입력하세요.")
            return
        cmd = f"scoreboard objectives add {obj} {crit}"
        self.set_advanced_output(cmd)
        self.log(f"scoreboard add: {cmd}")

    def build_scoreboard_display(self):
        obj = self.sb_objective_var.get().strip()
        slot = self.sb_display_slot_var.get().strip() or "sidebar"
        cmd = f"scoreboard objectives setdisplay {slot} {obj}"
        self.set_advanced_output(cmd)
        self.log(f"scoreboard display: {cmd}")

    def build_scoreboard_value(self):
        obj = self.sb_objective_var.get().strip()
        player = self.sb_player_var.get().strip()
        val = self.sb_value_var.get()
        cmds = [
            f"scoreboard players set {player} {obj} {val}",
            f"scoreboard players add {player} {obj} {val}",
        ]
        self.set_advanced_output("\n".join(cmds))
        self.log(f"scoreboard value set/add for {player} {obj} {val}")

    def build_tag(self, add: bool):
        target = self.tag_target_var.get().strip()
        name = self.tag_name_var.get().strip()
        op = "add" if add else "remove"
        cmd = f"tag {target} {op} {name}"
        self.set_advanced_output(cmd)
        self.log(f"tag {op}: {cmd}")

    def build_gamerule(self):
        rule = self.gamerule_name_var.get().strip()
        val = self.gamerule_value_var.get().strip()
        if not rule or not val:
            messagebox.showwarning("입력 필요", "gamerule과 값을 입력하세요.")
            return
        cmd = f"gamerule {rule} {val}"
        self.set_advanced_output(cmd)
        self.log(f"gamerule: {cmd}")

    def build_title(self):
        target = self.title_target_var.get().strip()
        text = self.title_text_var.get().strip()
        color = self.title_color_var.get().strip()
        payload = {"text": text}
        if color:
            payload["color"] = color
        cmd = f"title {target} title {json.dumps(payload, ensure_ascii=False)}"
        self.set_advanced_output(cmd)
        self.log(f"title: {cmd}")

    def build_actionbar(self):
        target = self.title_target_var.get().strip()
        text = self.actionbar_text_var.get().strip()
        payload = {"text": text}
        cmd = f"title {target} actionbar {json.dumps(payload, ensure_ascii=False)}"
        self.set_advanced_output(cmd)
        self.log(f"actionbar: {cmd}")

    def build_effect(self):
        target = self.title_target_var.get().strip()
        eff = self.effect_id_var.get().strip()
        dur = max(1, self.effect_dur_var.get())
        amp = max(0, self.effect_amp_var.get())
        hide = self.effect_hide_var.get()
        cmd = f"effect give {target} {eff} {dur} {amp} {'true' if hide else 'false'}"
        self.set_advanced_output(cmd)
        self.log(f"effect: {cmd}")

    def build_macro_session(self):
        obj = self.sb_objective_var.get().strip() or "session"
        cmds = [
            f"gamerule keepInventory true",
            f"gamerule sendCommandFeedback false",
            f"scoreboard objectives add {obj} dummy",
            f"scoreboard objectives setdisplay sidebar {obj}",
            f"title @a title {json.dumps({'text': '세션 시작!', 'color': 'gold'}, ensure_ascii=False)}",
            f"effect give @a night_vision 999999 0 true",
        ]
        self.set_advanced_output("\n".join(cmds))
        self.log("매크로: 기본 세션 세트")

    def build_macro_hardcore(self):
        cmds = [
            "gamerule keepInventory false",
            "difficulty hard",
            "gamerule naturalRegeneration false",
            "effect clear @a",
            "title @a title {\"text\":\"하드코어 시작!\",\"color\":\"red\"}",
        ]
        self.set_advanced_output("\n".join(cmds))
        self.log("매크로: 하드코어 세트")

    def set_advanced_output(self, content: str):
        self.advanced_output.delete("1.0", tk.END)
        self.advanced_output.insert(tk.END, content)

    def copy_advanced_output(self):
        text = self.advanced_output.get("1.0", tk.END).strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("복사 완료", "클립보드에 복사되었습니다.")

    # --- 탭: 개발 고급 도구 (스니펫/어드밴스먼트/검증) ---
    def create_dev_tools_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="개발 고급 도구")

        top = ttk.Frame(frame)
        top.pack(fill="x")

        # 함수 스니펫
        sn_box = ttk.LabelFrame(top, text="함수 스니펫 생성 (mcfunction)")
        sn_box.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=4)
        sn_row1 = ttk.Frame(sn_box)
        sn_row1.pack(fill="x", pady=3)
        ttk.Label(sn_row1, text="스니펫").pack(side="left")
        sn_combo = ttk.Combobox(sn_row1, textvariable=self.snippet_choice, values=list(FUNCTION_SNIPPETS.keys()), state="readonly", width=18)
        sn_combo.pack(side="left", padx=4)
        ttk.Label(sn_row1, text="네임스페이스").pack(side="left", padx=(8, 2))
        ttk.Entry(sn_row1, textvariable=self.snippet_namespace, width=14).pack(side="left", padx=2)
        ttk.Label(sn_row1, text="파일명").pack(side="left", padx=(8, 2))
        ttk.Entry(sn_row1, textvariable=self.snippet_name, width=14).pack(side="left", padx=2)
        ttk.Button(sn_row1, text="저장", command=self.generate_snippet).pack(side="left", padx=4)
        sn_row2 = ttk.Frame(sn_box)
        sn_row2.pack(fill="x", pady=3)
        ttk.Label(sn_row2, text="설명: 자주 쓰는 mcfunction 스니펫을 바로 파일로 만듭니다.").pack(side="left")

        # 어드밴스먼트/프레디케이트
        mid = ttk.Frame(top)
        mid.pack(side="left", fill="both", expand=True, pady=4)

        adv_box = ttk.LabelFrame(mid, text="어드밴스먼트 템플릿 저장")
        adv_box.pack(fill="x", pady=4)
        adv_row = ttk.Frame(adv_box)
        adv_row.pack(fill="x", pady=3)
        ttk.Label(adv_row, text="네임스페이스").pack(side="left")
        ttk.Entry(adv_row, textvariable=self.adv_namespace, width=14).pack(side="left", padx=3)
        ttk.Label(adv_row, text="파일명").pack(side="left")
        ttk.Entry(adv_row, textvariable=self.adv_name, width=14).pack(side="left", padx=3)
        ttk.Button(adv_row, text="저장", command=self.save_advancement).pack(side="left", padx=4)

        pred_box = ttk.LabelFrame(mid, text="프레디케이트 템플릿 저장")
        pred_box.pack(fill="x", pady=4)
        pr_row = ttk.Frame(pred_box)
        pr_row.pack(fill="x", pady=3)
        ttk.Label(pr_row, text="네임스페이스").pack(side="left")
        ttk.Entry(pr_row, textvariable=self.pred_namespace, width=14).pack(side="left", padx=3)
        ttk.Label(pr_row, text="파일명").pack(side="left")
        ttk.Entry(pr_row, textvariable=self.pred_name, width=18).pack(side="left", padx=3)
        ttk.Button(pr_row, text="저장", command=self.save_predicate).pack(side="left", padx=4)

        # 검증/pack_format 추천
        right = ttk.LabelFrame(top, text="팩 검증 & pack_format 추천")
        right.pack(side="left", fill="both", expand=True, pady=4)
        ttk.Label(right, text="버전별 권장 pack_format").pack(anchor="w", padx=6, pady=2)
        for name, fmt in PACK_FORMATS.items():
            ttk.Label(right, text=f"- {name}: {fmt}").pack(anchor="w", padx=12)
        ttk.Button(right, text="워크스페이스 검사", command=self.validate_packs).pack(pady=6, padx=6, anchor="w")

        val_box = ttk.LabelFrame(frame, text="검사 결과 / 로그")
        val_box.pack(fill="both", expand=True, pady=8)
        self.validation_output = tk.Text(val_box, height=12, wrap="word")
        self.validation_output.pack(fill="both", expand=True, padx=6, pady=6)

    def generate_snippet(self):
        base = self.ensure_workspace()
        if not base:
            return
        ns = self.snippet_namespace.get().strip() or "example"
        name = self.safe_filename(self.snippet_name.get().strip() or "snippet")
        snippet_key = self.snippet_choice.get()
        content = FUNCTION_SNIPPETS.get(snippet_key, "")
        if not content:
            messagebox.showerror("스니펫 없음", "해당 스니펫이 정의되지 않았습니다.")
            return
        target_dir = os.path.join(base, "datapacks", ns, "data", ns, "functions")
        os.makedirs(target_dir, exist_ok=True)
        path = os.path.join(target_dir, f"{name}.mcfunction")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        self.log(f"스니펫 생성: {path}")
        messagebox.showinfo("완료", f"mcfunction 스니펫이 저장되었습니다:\n{path}")

    def save_advancement(self):
        base = self.ensure_workspace()
        if not base:
            return
        ns = self.adv_namespace.get().strip() or "example"
        name = self.safe_filename(self.adv_name.get().strip() or "advancement")
        target_dir = os.path.join(base, "datapacks", ns, "data", ns, "advancements")
        os.makedirs(target_dir, exist_ok=True)
        path = os.path.join(target_dir, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ADVANCEMENT_SAMPLE, f, ensure_ascii=False, indent=2)
        self.log(f"어드밴스먼트 템플릿 저장: {path}")
        messagebox.showinfo("완료", f"어드밴스먼트 템플릿이 저장되었습니다:\n{path}")

    def save_predicate(self):
        base = self.ensure_workspace()
        if not base:
            return
        ns = self.pred_namespace.get().strip() or "example"
        name = self.safe_filename(self.pred_name.get().strip() or "predicate")
        target_dir = os.path.join(base, "datapacks", ns, "data", ns, "predicates")
        os.makedirs(target_dir, exist_ok=True)
        path = os.path.join(target_dir, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(PREDICATE_SAMPLE, f, ensure_ascii=False, indent=2)
        self.log(f"프레디케이트 템플릿 저장: {path}")
        messagebox.showinfo("완료", f"프레디케이트 템플릿이 저장되었습니다:\n{path}")

    def validate_packs(self):
        base = self.ensure_workspace()
        if not base:
            return
        lines = []
        for kind in ("datapacks", "resourcepacks"):
            root_dir = os.path.join(base, kind)
            if not os.path.isdir(root_dir):
                lines.append(f"[{kind}] 폴더 없음: {root_dir}")
                continue
            for entry in sorted(os.listdir(root_dir)):
                pack_path = os.path.join(root_dir, entry)
                if not os.path.isdir(pack_path):
                    continue
                meta_path = os.path.join(pack_path, "pack.mcmeta")
                if not os.path.exists(meta_path):
                    lines.append(f"[{kind}] pack.mcmeta 없음: {entry}")
                    continue
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    pf = meta.get("pack", {}).get("pack_format")
                    desc = meta.get("pack", {}).get("description", "")
                    ok = "OK" if pf else "pack_format 없음"
                    lines.append(f"[{kind}] {entry}: pack_format={pf}, desc={desc} ({ok})")
                except Exception as exc:
                    lines.append(f"[{kind}] {entry}: pack.mcmeta 파싱 실패: {exc}")
        if not lines:
            lines.append("검사할 팩이 없습니다.")
        self.validation_output.delete("1.0", tk.END)
        self.validation_output.insert(tk.END, "\n".join(lines))
        self.validation_output.see(tk.END)
        self.log("팩 검증 완료")

    # --- 탭: 품질/체크리스트 ---
    def create_quality_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="품질/체크리스트")

        top = ttk.Frame(frame)
        top.pack(fill="x")

        rec_box = ttk.LabelFrame(top, text="녹화 전 점검")
        rec_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.record_vars = []
        for item in RECORDING_CHECKLIST:
            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(rec_box, text=item, variable=var)
            chk.pack(anchor="w", padx=6, pady=2)
            self.record_vars.append(var)
        ttk.Button(rec_box, text="모두 해제", command=lambda: self.reset_checks(self.record_vars)).pack(pady=4, padx=6, anchor="w")

        rel_box = ttk.LabelFrame(top, text="배포/업로드 점검")
        rel_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.release_vars = []
        for item in RELEASE_CHECKLIST:
            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(rel_box, text=item, variable=var)
            chk.pack(anchor="w", padx=6, pady=2)
            self.release_vars.append(var)
        ttk.Button(rel_box, text="모두 해제", command=lambda: self.reset_checks(self.release_vars)).pack(pady=4, padx=6, anchor="w")

        scan_box = ttk.LabelFrame(top, text="팩 구조 스캐너")
        scan_box.pack(side="left", fill="both", expand=True)
        ttk.Label(scan_box, text="워크스페이스 내 datapacks/resourcepacks 구조를 빠르게 점검합니다.").pack(anchor="w", padx=6, pady=4)
        ttk.Button(scan_box, text="스캔 실행", command=self.run_workspace_scan).pack(padx=6, pady=4, anchor="w")

        out_box = ttk.LabelFrame(frame, text="결과/노트")
        out_box.pack(fill="both", expand=True, pady=8)
        self.quality_output = tk.Text(out_box, height=12, wrap="word")
        self.quality_output.pack(fill="both", expand=True, padx=6, pady=6)

    def reset_checks(self, vars_list):
        for var in vars_list:
            var.set(False)

    def run_workspace_scan(self):
        base = self.ensure_workspace()
        if not base:
            return
        results = scan_workspace(base)
        self.quality_output.delete("1.0", tk.END)
        self.quality_output.insert(tk.END, "\n".join(results))
        self.quality_output.see(tk.END)
        self.log("워크스페이스 스캔 완료")

    # --- 탭: 배포/자동화 ---
    def create_automation_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="배포/자동화")

        upper = ttk.Frame(frame)
        upper.pack(fill="x")

        # 패키징
        pack_box = ttk.LabelFrame(upper, text="팩 압축 (zip)")
        pack_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        ttk.Label(pack_box, text="데이터 팩 선택 후 '압축'으로 zip 생성").pack(anchor="w", padx=6, pady=(4, 2))
        self.pack_list_dp = tk.Listbox(pack_box, height=6, exportselection=False)
        self.pack_list_dp.pack(fill="x", padx=6, pady=2)
        ttk.Button(pack_box, text="새로고침", command=self.refresh_packs).pack(anchor="w", padx=6, pady=2)
        ttk.Button(pack_box, text="데이터 팩 압축", command=lambda: self.zip_selected("datapacks")).pack(anchor="w", padx=6, pady=2)

        rp_box = ttk.LabelFrame(upper, text="리소스 팩 압축 (zip)")
        rp_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        ttk.Label(rp_box, text="리소스 팩 선택 후 '압축'으로 zip 생성").pack(anchor="w", padx=6, pady=(4, 2))
        self.pack_list_rp = tk.Listbox(rp_box, height=6, exportselection=False)
        self.pack_list_rp.pack(fill="x", padx=6, pady=2)
        ttk.Button(rp_box, text="새로고침", command=self.refresh_packs).pack(anchor="w", padx=6, pady=2)
        ttk.Button(rp_box, text="리소스 팩 압축", command=lambda: self.zip_selected("resourcepacks")).pack(anchor="w", padx=6, pady=2)

        # 프로파일 명령어
        prof_box = ttk.LabelFrame(upper, text="명령어 프로파일 (방송/녹화 세트)")
        prof_box.pack(side="left", fill="both", expand=True)
        ttk.Label(prof_box, text="프로파일을 선택하면 명령어 리스트를 출력합니다.").pack(anchor="w", padx=6, pady=4)
        ttk.Combobox(prof_box, textvariable=self.profile_choice, values=list(PROFILES.keys()), state="readonly").pack(fill="x", padx=6, pady=2)
        ttk.Button(prof_box, text="출력", command=self.render_profile_commands).pack(anchor="w", padx=6, pady=4)

        # 린트/검사
        lint_box = ttk.LabelFrame(frame, text="mcfunction 린트/검사")
        lint_box.pack(fill="both", expand=True, pady=8)
        ttk.Button(lint_box, text="린트 실행", command=self.run_lint).pack(anchor="w", padx=6, pady=4)
        self.lint_output = tk.Text(lint_box, height=12, wrap="word")
        self.lint_output.pack(fill="both", expand=True, padx=6, pady=6)

        self.refresh_packs()

    def refresh_packs(self):
        base = self.workspace_var.get().strip()
        for lb in (self.pack_list_dp, self.pack_list_rp):
            if lb:
                lb.delete(0, tk.END)
        if not base:
            return
        for kind, lb in (("datapacks", self.pack_list_dp), ("resourcepacks", self.pack_list_rp)):
            root = os.path.join(base, kind)
            if not (lb and os.path.isdir(root)):
                continue
            for entry in sorted(os.listdir(root)):
                if os.path.isdir(os.path.join(root, entry)):
                    lb.insert(tk.END, entry)

    def zip_selected(self, kind: str):
        base = self.ensure_workspace()
        if not base:
            return
        lb = self.pack_list_dp if kind == "datapacks" else self.pack_list_rp
        if not lb:
            return
        sel = lb.curselection()
        if not sel:
            messagebox.showwarning("선택 없음", "압축할 팩을 선택하세요.")
            return
        name = lb.get(sel[0])
        target_dir = os.path.join(base, kind, name)
        if not os.path.isdir(target_dir):
            messagebox.showerror("경로 오류", f"폴더를 찾을 수 없습니다: {target_dir}")
            return
        out_base = os.path.join(base, f"{name}")
        zip_path = shutil.make_archive(out_base, "zip", root_dir=target_dir)
        self.log(f"{kind} 압축 생성: {zip_path}")
        messagebox.showinfo("완료", f"압축 파일이 생성되었습니다:\n{zip_path}")

    def render_profile_commands(self):
        profile = self.profile_choice.get()
        cmds = PROFILES.get(profile, [])
        if not cmds:
            messagebox.showwarning("프로파일 없음", "명령어가 정의되지 않은 프로파일입니다.")
            return
        text = "\n".join(cmds)
        if self.advanced_output:
            self.advanced_output.delete("1.0", tk.END)
            self.advanced_output.insert(tk.END, text)
        messagebox.showinfo("출력 완료", f"'{profile}' 프로파일 명령어가 출력되었습니다. 고급 명령어 탭에서 복사할 수 있습니다.")
        self.log(f"프로파일 출력: {profile}")

    def run_lint(self):
        base = self.ensure_workspace()
        if not base:
            return
        results = lint_workspace(base)
        self.lint_output.delete("1.0", tk.END)
        self.lint_output.insert(tk.END, "\n".join(results))
        self.lint_output.see(tk.END)
        self.log("mcfunction 린트 완료")

    # --- 탭: 편집/유지보수 (검색/치환, 오프라인 가이드) ---
    def create_maintenance_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="편집/유지보수")

        top = ttk.Frame(frame)
        top.pack(fill="x")

        find_box = ttk.LabelFrame(top, text="mcfunction 일괄 검색/치환")
        find_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        f_row1 = ttk.Frame(find_box)
        f_row1.pack(fill="x", pady=3)
        ttk.Label(f_row1, text="검색").pack(side="left")
        ttk.Entry(f_row1, textvariable=self.find_text, width=20).pack(side="left", padx=4)
        ttk.Button(f_row1, text="검색 실행", command=self.run_find).pack(side="left", padx=4)
        f_row2 = ttk.Frame(find_box)
        f_row2.pack(fill="x", pady=3)
        ttk.Label(f_row2, text="치환 →").pack(side="left")
        ttk.Entry(f_row2, textvariable=self.replace_text, width=20).pack(side="left", padx=4)
        ttk.Button(f_row2, text="치환 실행", command=self.run_replace).pack(side="left", padx=4)
        ttk.Label(find_box, text="※ 워크스페이스의 모든 mcfunction에서 문자열 기준으로 동작합니다.").pack(anchor="w", padx=6, pady=4)

        doc_box = ttk.LabelFrame(top, text="오프라인 베스트 프랙티스/FAQ")
        doc_box.pack(side="left", fill="both", expand=True)
        ttk.Combobox(doc_box, textvariable=self.doc_choice, values=list(DOCS.keys()), state="readonly").pack(fill="x", padx=6, pady=4)
        ttk.Button(doc_box, text="보기", command=self.show_doc).pack(anchor="w", padx=6, pady=2)

        out_box = ttk.LabelFrame(frame, text="결과/노트")
        out_box.pack(fill="both", expand=True, pady=8)
        self.find_output = tk.Text(out_box, height=10, wrap="word")
        self.find_output.pack(fill="both", expand=True, padx=6, pady=6)
        self.doc_view = tk.Text(out_box, height=8, wrap="word")
        self.doc_view.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    def run_find(self):
        base = self.ensure_workspace()
        if not base:
            return
        needle = self.find_text.get()
        if not needle:
            messagebox.showwarning("입력 필요", "검색할 문자열을 입력하세요.")
            return
        matches = find_occurrences(base, needle)
        lines = []
        for rel, rows in matches.items():
            lines.append(f"{rel}: {', '.join(map(str, rows))}행")
        if not lines:
            lines.append("검색 결과 없음")
        self.find_output.delete("1.0", tk.END)
        self.find_output.insert(tk.END, "\n".join(lines))
        self.find_output.see(tk.END)
        self.log(f"검색 완료: '{needle}'")

    def run_replace(self):
        base = self.ensure_workspace()
        if not base:
            return
        needle = self.find_text.get()
        replacement = self.replace_text.get()
        if not needle:
            messagebox.showwarning("입력 필요", "치환할 검색 문자열을 입력하세요.")
            return
        changed = replace_in_workspace(base, needle, replacement)
        self.find_output.delete("1.0", tk.END)
        self.find_output.insert(tk.END, f"치환 완료: 변경된 파일 {changed}개")
        self.find_output.see(tk.END)
        self.log(f"치환 완료: '{needle}' -> '{replacement}', 파일 {changed}개")

    def show_doc(self):
        key = self.doc_choice.get()
        text = DOCS.get(key, "내용을 찾을 수 없습니다.")
        self.doc_view.delete("1.0", tk.END)
        self.doc_view.insert(tk.END, f"[{key}]\n{text}")
        self.doc_view.see(tk.END)

    # --- 탭: 출시 문서 (README/변경 로그) ---
    def create_release_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="출시 문서")

        top = ttk.Frame(frame)
        top.pack(fill="x")

        kind_row = ttk.Frame(top)
        kind_row.pack(fill="x", pady=4)
        ttk.Radiobutton(kind_row, text="데이터 팩", variable=self.release_kind_var, value="datapacks", command=self.refresh_release_packs).pack(side="left")
        ttk.Radiobutton(kind_row, text="리소스 팩", variable=self.release_kind_var, value="resourcepacks", command=self.refresh_release_packs).pack(side="left", padx=4)
        ttk.Button(kind_row, text="목록 새로고침", command=self.refresh_release_packs).pack(side="left", padx=6)

        sel_row = ttk.Frame(top)
        sel_row.pack(fill="x", pady=4)
        ttk.Label(sel_row, text="팩 선택").pack(side="left")
        self.release_pack_combo = ttk.Combobox(sel_row, textvariable=self.release_pack_var, state="readonly")
        self.release_pack_combo.pack(side="left", padx=6)
        ttk.Label(sel_row, text="버전").pack(side="left", padx=(10, 2))
        ttk.Entry(sel_row, textvariable=self.release_version_var, width=10).pack(side="left", padx=4)
        ttk.Button(sel_row, text="README 생성", command=self.generate_readme_doc).pack(side="left", padx=4)
        ttk.Button(sel_row, text="변경 로그 생성", command=self.generate_changelog_doc).pack(side="left", padx=4)

        out_box = ttk.LabelFrame(frame, text="문서 미리보기")
        out_box.pack(fill="both", expand=True, pady=8)
        self.release_output = tk.Text(out_box, height=20, wrap="word")
        self.release_output.pack(fill="both", expand=True, padx=6, pady=6)

        self.refresh_release_packs()

    def refresh_release_packs(self):
        base = self.workspace_var.get().strip()
        if not base:
            return
        kind = self.release_kind_var.get()
        packs = list_packs(base, kind)
        self.release_pack_combo["values"] = packs
        if packs:
            self.release_pack_combo.current(0)

    def generate_readme_doc(self):
        base = self.ensure_workspace()
        if not base:
            return
        pack = self.release_pack_var.get()
        if not pack:
            messagebox.showwarning("선택 필요", "팩을 선택하세요.")
            return
        version = self.release_version_var.get().strip() or "v1.0.0"
        kind = self.release_kind_var.get()
        text = generate_readme(base, kind, pack, version)
        self.release_output.delete("1.0", tk.END)
        self.release_output.insert(tk.END, text)
        self.log(f"README 미리보기 생성: {pack} {version}")

    def generate_changelog_doc(self):
        pack = self.release_pack_var.get()
        if not pack:
            messagebox.showwarning("선택 필요", "팩을 선택하세요.")
            return
        version = self.release_version_var.get().strip() or "v1.0.0"
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        text = generate_changelog(pack, version, today)
        self.release_output.delete("1.0", tk.END)
        self.release_output.insert(tk.END, text)
        self.log(f"변경 로그 미리보기 생성: {pack} {version}")

    # --- 탭: 통계/인벤토리 ---
    def create_stats_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="통계/인벤토리")

        ttk.Label(frame, text="워크스페이스 내 팩 개수, mcfunction/텍스처 수, 용량을 요약합니다.").pack(anchor="w", padx=6, pady=4)
        ttk.Button(frame, text="통계 새로고침", command=self.refresh_stats).pack(anchor="w", padx=6, pady=4)

        self.stats_output = tk.Text(frame, height=16, wrap="word")
        self.stats_output.pack(fill="both", expand=True, padx=6, pady=6)

    def refresh_stats(self):
        base = self.ensure_workspace()
        if not base:
            return
        stats = collect_stats(base)
        text = summarize(stats)
        self.stats_output.delete("1.0", tk.END)
        self.stats_output.insert(tk.END, text)
        self.stats_output.see(tk.END)
        self.log("통계 새로고침 완료")

    # --- 탭: 서버 설정 (server.properties 간단 편집) ---
    def create_server_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="서버 설정")

        ttk.Label(frame, text="server.properties 경로를 선택해 주요 옵션을 편집합니다.").pack(anchor="w", padx=6, pady=4)
        path_row = ttk.Frame(frame)
        path_row.pack(fill="x", pady=4)
        ttk.Entry(path_row, textvariable=self.server_props_path).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(path_row, text="파일 선택", command=self.browse_server_props).pack(side="left", padx=4)
        ttk.Button(path_row, text="불러오기", command=self.load_server_props).pack(side="left", padx=4)
        ttk.Button(path_row, text="저장", command=self.save_server_props).pack(side="left", padx=4)

        grid = ttk.Frame(frame)
        grid.pack(fill="x", pady=8)
        for idx, key in enumerate(TARGET_KEYS):
            row = ttk.Frame(grid)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=key, width=22).pack(side="left")
            ttk.Entry(row, textvariable=self.server_prop_vars[key], width=30).pack(side="left", padx=4)

    def browse_server_props(self):
        path = filedialog.askopenfilename(title="server.properties 선택", filetypes=[("properties", "*.properties"), ("All", "*.*")])
        if path:
            self.server_props_path.set(path)

    def load_server_props(self):
        path = self.server_props_path.get().strip()
        if not path:
            messagebox.showwarning("경로 없음", "server.properties 파일을 선택하세요.")
            return
        try:
            props = load_properties(path)
            for k, var in self.server_prop_vars.items():
                var.set(props.values.get(k, ""))
            self.log(f"server.properties 로드: {path}")
        except Exception as exc:
            messagebox.showerror("불러오기 실패", str(exc))

    def save_server_props(self):
        path = self.server_props_path.get().strip()
        if not path:
            messagebox.showwarning("경로 없음", "server.properties 파일을 선택하세요.")
            return
        props = ServerProps(values={k: v.get() for k, v in self.server_prop_vars.items() if v.get() != ""})
        try:
            save_properties(path, props)
            self.log(f"server.properties 저장: {path}")
            messagebox.showinfo("저장 완료", "server.properties가 업데이트되었습니다.")
        except Exception as exc:
            messagebox.showerror("저장 실패", str(exc))

    # --- 탭: 레시피 생성 (shaped/shapeless) ---
    def create_recipe_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="레시피 생성")

        top = ttk.Frame(frame)
        top.pack(fill="x")
        ttk.Label(top, text="네임스페이스").pack(side="left")
        ttk.Entry(top, textvariable=self.recipe_namespace, width=14).pack(side="left", padx=4)
        ttk.Label(top, text="파일명").pack(side="left")
        ttk.Entry(top, textvariable=self.recipe_name, width=14).pack(side="left", padx=4)
        ttk.Label(top, text="결과 아이템").pack(side="left")
        ttk.Entry(top, textvariable=self.recipe_result, width=18).pack(side="left", padx=4)
        ttk.Label(top, text="수량").pack(side="left")
        ttk.Entry(top, textvariable=self.recipe_count, width=6).pack(side="left", padx=4)

        body = ttk.Frame(frame)
        body.pack(fill="both", expand=True, pady=8)

        shaped_box = ttk.LabelFrame(body, text="Shaped (3x3)")
        shaped_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        grid_frame = ttk.Frame(shaped_box)
        grid_frame.pack(pady=6)
        for i in range(3):
            row = ttk.Frame(grid_frame)
            row.pack()
            for j in range(3):
                idx = i * 3 + j
                ttk.Entry(row, textvariable=self.recipe_grid[idx], width=18).pack(side="left", padx=2, pady=2)
        ttk.Button(shaped_box, text="Shaped 생성", command=self.build_shaped_recipe).pack(pady=4)

        shapeless_box = ttk.LabelFrame(body, text="Shapeless (재료 콤마 구분)")
        shapeless_box.pack(side="left", fill="both", expand=True)
        ttk.Entry(shapeless_box, textvariable=self.shapeless_items).pack(fill="x", padx=6, pady=6)
        ttk.Button(shapeless_box, text="Shapeless 생성", command=self.build_shapeless_recipe).pack(pady=4, padx=6, anchor="w")

        out_box = ttk.LabelFrame(frame, text="미리보기 / 저장")
        out_box.pack(fill="both", expand=True)
        self.recipe_output = tk.Text(out_box, height=16, wrap="word")
        self.recipe_output.pack(fill="both", expand=True, padx=6, pady=6)
        btns = ttk.Frame(out_box)
        btns.pack(fill="x", pady=(0, 6))
        ttk.Button(btns, text="파일로 저장", command=self.save_recipe).pack(side="left", padx=4)
        ttk.Button(btns, text="클립보드 복사", command=self.copy_recipe_output).pack(side="left", padx=4)
        ttk.Button(btns, text="지우기", command=lambda: self.recipe_output.delete("1.0", tk.END)).pack(side="left", padx=4)

    def build_shaped_recipe(self):
        try:
            grid_values = [v.get().strip() for v in self.recipe_grid]
            recipe = shaped_from_grid(grid_values, self.recipe_result.get().strip(), self.recipe_count.get())
            data = recipe.to_json()
        except Exception as exc:
            messagebox.showerror("생성 실패", str(exc))
            return
        self.recipe_output.delete("1.0", tk.END)
        self.recipe_output.insert(tk.END, json.dumps(data, ensure_ascii=False, indent=2))
        self.log("Shaped 레시피 생성")

    def build_shapeless_recipe(self):
        try:
            items = [x.strip() for x in self.shapeless_items.get().split(",")]
            data = build_shapeless(items, self.recipe_result.get().strip(), self.recipe_count.get())
        except Exception as exc:
            messagebox.showerror("생성 실패", str(exc))
            return
        self.recipe_output.delete("1.0", tk.END)
        self.recipe_output.insert(tk.END, json.dumps(data, ensure_ascii=False, indent=2))
        self.log("Shapeless 레시피 생성")

    def save_recipe(self):
        base = self.ensure_workspace()
        if not base:
            return
        ns = self.recipe_namespace.get().strip() or "example"
        name = self.safe_filename(self.recipe_name.get().strip() or "recipe")
        target_dir = os.path.join(base, "datapacks", ns, "data", ns, "recipes")
        os.makedirs(target_dir, exist_ok=True)
        path = os.path.join(target_dir, f"{name}.json")
        content = self.recipe_output.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("내용 없음", "먼저 레시피를 생성하세요.")
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content + "\n")
            self.log(f"레시피 저장: {path}")
            messagebox.showinfo("저장 완료", f"레시피가 저장되었습니다:\n{path}")
        except Exception as exc:
            messagebox.showerror("저장 실패", str(exc))

    def copy_recipe_output(self):
        text = self.recipe_output.get("1.0", tk.END).strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("복사 완료", "클립보드에 복사되었습니다.")

    # --- 탭: 파티클/이펙트 경로 생성 ---
    def create_particle_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="파티클/이펙트")

        top = ttk.Frame(frame)
        top.pack(fill="x")
        ttk.Label(top, text="파티클 ID").pack(side="left")
        ttk.Entry(top, textvariable=self.particle_id, width=22).pack(side="left", padx=4)
        ttk.Label(top, text="count").pack(side="left")
        ttk.Entry(top, textvariable=self.particle_count, width=6).pack(side="left", padx=4)
        ttk.Label(top, text="speed").pack(side="left")
        ttk.Entry(top, textvariable=self.particle_speed, width=8).pack(side="left", padx=4)

        body = ttk.Frame(frame)
        body.pack(fill="both", expand=True, pady=8)

        line_box = ttk.LabelFrame(body, text="라인 경로")
        line_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        l_row1 = ttk.Frame(line_box)
        l_row1.pack(fill="x", pady=3)
        ttk.Label(l_row1, text="시작 x y z").pack(side="left")
        for var in self.line_start:
            ttk.Entry(l_row1, textvariable=var, width=8).pack(side="left", padx=2)
        l_row2 = ttk.Frame(line_box)
        l_row2.pack(fill="x", pady=3)
        ttk.Label(l_row2, text="끝 x y z").pack(side="left")
        for var in self.line_end:
            ttk.Entry(l_row2, textvariable=var, width=8).pack(side="left", padx=2)
        l_row3 = ttk.Frame(line_box)
        l_row3.pack(fill="x", pady=3)
        ttk.Label(l_row3, text="steps").pack(side="left")
        ttk.Entry(l_row3, textvariable=self.line_steps, width=8).pack(side="left", padx=4)
        ttk.Button(l_row3, text="라인 생성", command=self.build_particle_line).pack(side="left", padx=4)

        circle_box = ttk.LabelFrame(body, text="원형 경로 (XZ 평면)")
        circle_box.pack(side="left", fill="both", expand=True)
        c_row1 = ttk.Frame(circle_box)
        c_row1.pack(fill="x", pady=3)
        ttk.Label(c_row1, text="센터 x y z").pack(side="left")
        for var in self.circle_center:
            ttk.Entry(c_row1, textvariable=var, width=8).pack(side="left", padx=2)
        c_row2 = ttk.Frame(circle_box)
        c_row2.pack(fill="x", pady=3)
        ttk.Label(c_row2, text="반지름").pack(side="left")
        ttk.Entry(c_row2, textvariable=self.circle_radius, width=8).pack(side="left", padx=4)
        ttk.Label(c_row2, text="points").pack(side="left")
        ttk.Entry(c_row2, textvariable=self.circle_points, width=8).pack(side="left", padx=4)
        ttk.Button(c_row2, text="원형 생성", command=self.build_particle_circle).pack(side="left", padx=4)

        out_box = ttk.LabelFrame(frame, text="미리보기 / 저장")
        out_box.pack(fill="both", expand=True)
        self.particle_output = tk.Text(out_box, height=14, wrap="word")
        self.particle_output.pack(fill="both", expand=True, padx=6, pady=6)
        p_btns = ttk.Frame(out_box)
        p_btns.pack(fill="x", pady=(0, 6))
        ttk.Button(p_btns, text="클립보드 복사", command=self.copy_particle_output).pack(side="left", padx=4)
        ttk.Button(p_btns, text="mcfunction 저장", command=self.save_particle_function).pack(side="left", padx=4)
        ttk.Button(p_btns, text="지우기", command=lambda: self.particle_output.delete("1.0", tk.END)).pack(side="left", padx=4)

    def build_particle_line(self):
        try:
            cmds = generate_line_commands(
                self.particle_id.get().strip(),
                (self.line_start[0].get(), self.line_start[1].get(), self.line_start[2].get()),
                (self.line_end[0].get(), self.line_end[1].get(), self.line_end[2].get()),
                self.line_steps.get(),
                self.particle_count.get(),
                float(self.particle_speed.get()),
            )
        except Exception as exc:
            messagebox.showerror("생성 실패", str(exc))
            return
        self.particle_output.delete("1.0", tk.END)
        self.particle_output.insert(tk.END, "\n".join(cmds))
        self.log("파티클 라인 생성")

    def build_particle_circle(self):
        try:
            cmds = generate_circle_commands(
                self.particle_id.get().strip(),
                (self.circle_center[0].get(), self.circle_center[1].get(), self.circle_center[2].get()),
                float(self.circle_radius.get()),
                self.circle_points.get(),
                self.particle_count.get(),
                float(self.particle_speed.get()),
            )
        except Exception as exc:
            messagebox.showerror("생성 실패", str(exc))
            return
        self.particle_output.delete("1.0", tk.END)
        self.particle_output.insert(tk.END, "\n".join(cmds))
        self.log("파티클 원형 생성")

    def copy_particle_output(self):
        text = self.particle_output.get("1.0", tk.END).strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("복사 완료", "클립보드에 복사되었습니다.")

    def save_particle_function(self):
        base = self.ensure_workspace()
        if not base:
            return
        ns = self.dp_namespace_var.get().strip() or "example"
        name = "particle_path"
        target_dir = os.path.join(base, "datapacks", ns, "data", ns, "functions")
        os.makedirs(target_dir, exist_ok=True)
        path = os.path.join(target_dir, f"{name}.mcfunction")
        content = self.particle_output.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("내용 없음", "먼저 파티클 명령을 생성하세요.")
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(content + "\n")
        self.log(f"파티클 함수 저장: {path}")
        messagebox.showinfo("저장 완료", f"mcfunction이 저장되었습니다:\n{path}")

    # --- 탭: 텍스트/채팅 (그라디언트) ---
    def create_text_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="텍스트/채팅")

        top = ttk.Frame(frame)
        top.pack(fill="x")
        ttk.Label(top, text="대상").pack(side="left")
        ttk.Entry(top, textvariable=self.text_target_var, width=8).pack(side="left", padx=4)
        ttk.Label(top, text="텍스트").pack(side="left")
        ttk.Entry(top, textvariable=self.grad_text_var, width=30).pack(side="left", padx=4)
        ttk.Label(top, text="색상1").pack(side="left")
        ttk.Entry(top, textvariable=self.grad_color1_var, width=10).pack(side="left", padx=2)
        ttk.Label(top, text="색상2").pack(side="left")
        ttk.Entry(top, textvariable=self.grad_color2_var, width=10).pack(side="left", padx=2)
        ttk.Checkbutton(top, text="Bold", variable=self.grad_bold_var).pack(side="left", padx=4)
        ttk.Checkbutton(top, text="Italic", variable=self.grad_italic_var).pack(side="left", padx=4)

        btns = ttk.Frame(frame)
        btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="tellraw 생성", command=self.build_gradient_tellraw).pack(side="left", padx=4)
        ttk.Button(btns, text="title 생성", command=self.build_gradient_title).pack(side="left", padx=4)

        out_box = ttk.LabelFrame(frame, text="미리보기 / 복사")
        out_box.pack(fill="both", expand=True, pady=6)
        self.text_output = tk.Text(out_box, height=14, wrap="word")
        self.text_output.pack(fill="both", expand=True, padx=6, pady=6)
        t_btns = ttk.Frame(out_box)
        t_btns.pack(fill="x", pady=(0, 6))
        ttk.Button(t_btns, text="클립보드 복사", command=self.copy_text_output).pack(side="left", padx=4)
        ttk.Button(t_btns, text="지우기", command=lambda: self.text_output.delete("1.0", tk.END)).pack(side="left", padx=4)

        hint = (
            "힌트: 색상은 #RRGGBB 형식. tellraw/title 모두 RGB를 지원합니다(1.16+). "
            "글자마다 색상이 적용된 JSON 배열을 생성합니다."
        )
        ttk.Label(frame, text=hint).pack(anchor="w", padx=6, pady=4)

    def build_gradient_tellraw(self):
        try:
            payload = gradient_text_payload(
                self.grad_text_var.get(),
                self.grad_color1_var.get(),
                self.grad_color2_var.get(),
                bold=self.grad_bold_var.get(),
                italic=self.grad_italic_var.get(),
            )
        except Exception as exc:
            messagebox.showerror("생성 실패", str(exc))
            return
        cmd = f"tellraw {self.text_target_var.get().strip()} {json.dumps({'text': '', 'extra': payload}, ensure_ascii=False)}"
        self.text_output.delete("1.0", tk.END)
        self.text_output.insert(tk.END, cmd)
        self.log("그라디언트 tellraw 생성")

    def build_gradient_title(self):
        try:
            payload = gradient_text_payload(
                self.grad_text_var.get(),
                self.grad_color1_var.get(),
                self.grad_color2_var.get(),
                bold=self.grad_bold_var.get(),
                italic=self.grad_italic_var.get(),
            )
        except Exception as exc:
            messagebox.showerror("생성 실패", str(exc))
            return
        cmd = f"title {self.text_target_var.get().strip()} title {json.dumps({'text': '', 'extra': payload}, ensure_ascii=False)}"
        self.text_output.delete("1.0", tk.END)
        self.text_output.insert(tk.END, cmd)
        self.log("그라디언트 title 생성")

    def copy_text_output(self):
        text = self.text_output.get("1.0", tk.END).strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("복사 완료", "클립보드에 복사되었습니다.")

    # --- 탭: 태그/pack.mcmeta ---
    def create_tag_meta_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="태그/메타")

        top = ttk.Frame(frame)
        top.pack(fill="x")

        # Tag 생성
        tag_box = ttk.LabelFrame(top, text="Tag 생성")
        tag_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        t_row1 = ttk.Frame(tag_box)
        t_row1.pack(fill="x", pady=3)
        ttk.Label(t_row1, text="네임스페이스").pack(side="left")
        ttk.Entry(t_row1, textvariable=self.tag_namespace, width=14).pack(side="left", padx=4)
        ttk.Label(t_row1, text="카테고리").pack(side="left")
        ttk.Combobox(t_row1, textvariable=self.tag_category, values=SUPPORTED_CATEGORIES, state="readonly", width=14).pack(side="left", padx=4)
        t_row2 = ttk.Frame(tag_box)
        t_row2.pack(fill="x", pady=3)
        ttk.Label(t_row2, text="이름(확장자 제외)").pack(side="left")
        ttk.Entry(t_row2, textvariable=self.tag_name, width=18).pack(side="left", padx=4)
        ttk.Checkbutton(t_row2, text="replace=true", variable=self.tag_replace).pack(side="left", padx=4)
        t_row3 = ttk.Frame(tag_box)
        t_row3.pack(fill="x", pady=3)
        ttk.Label(t_row3, text="values (콤마 구분)").pack(side="left")
        ttk.Entry(t_row3, textvariable=self.tag_entries).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(tag_box, text="Tag 생성/저장", command=self.create_tag_file).pack(pady=4, padx=4, anchor="w")

        # pack.mcmeta 업데이트
        meta_box = ttk.LabelFrame(top, text="pack.mcmeta 일괄 업데이트")
        meta_box.pack(side="left", fill="both", expand=True)
        m_row1 = ttk.Frame(meta_box)
        m_row1.pack(fill="x", pady=3)
        ttk.Label(m_row1, text="pack_format").pack(side="left")
        ttk.Entry(m_row1, textvariable=self.meta_format_var, width=8).pack(side="left", padx=4)
        ttk.Label(m_row1, text="description").pack(side="left")
        ttk.Entry(m_row1, textvariable=self.meta_desc_var, width=26).pack(side="left", padx=4)
        m_row2 = ttk.Frame(meta_box)
        m_row2.pack(fill="x", pady=3)
        ttk.Button(m_row2, text="데이터 팩 전체 적용", command=lambda: self.update_packmeta("datapacks")).pack(side="left", padx=4)
        ttk.Button(m_row2, text="리소스 팩 전체 적용", command=lambda: self.update_packmeta("resourcepacks")).pack(side="left", padx=4)

        out_box = ttk.LabelFrame(frame, text="결과/로그")
        out_box.pack(fill="both", expand=True, pady=8)
        self.tag_output = tk.Text(out_box, height=10, wrap="word")
        self.tag_output.pack(fill="both", expand=True, padx=6, pady=6)
        self.meta_output = self.tag_output

    def create_tag_file(self):
        base = self.ensure_workspace()
        if not base:
            return
        entries = [x.strip() for x in self.tag_entries.get().split(",")]
        try:
            data = build_tag_json(entries, replace=self.tag_replace.get())
        except Exception as exc:
            messagebox.showerror("생성 실패", str(exc))
            return
        ns = self.tag_namespace.get().strip() or "example"
        name = self.safe_filename(self.tag_name.get().strip() or "custom_tag")
        cat = self.tag_category.get().strip() or "blocks"
        try:
            path = save_tag(base, ns, cat, name, data)
        except Exception as exc:
            messagebox.showerror("저장 실패", str(exc))
            return
        self.tag_output.delete("1.0", tk.END)
        self.tag_output.insert(tk.END, json.dumps(data, ensure_ascii=False, indent=2) + f"\n\n저장: {path}")
        self.log(f"Tag 생성: {path}")
        messagebox.showinfo("저장 완료", f"Tag 파일이 저장되었습니다:\n{path}")

    def update_packmeta(self, kind: str):
        base = self.ensure_workspace()
        if not base:
            return
        pf = self.meta_format_var.get()
        desc = self.meta_desc_var.get().strip() or None
        updated = bulk_update(base, kind, pf, description=desc)
        msg = f"{kind}: 업데이트된 팩 {updated}개"
        self.tag_output.delete("1.0", tk.END)
        self.tag_output.insert(tk.END, msg)
        self.log(msg)

    # --- 탭: 비교/동기화 ---
    def create_diff_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="비교/동기화")

        ttk.Label(frame, text="두 개의 팩 또는 폴더를 비교해 추가/수정/삭제 파일을 보여주고, src→dst로 동기화합니다.").pack(anchor="w", padx=6, pady=4)
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=3)
        ttk.Label(row1, text="소스(src)").pack(side="left")
        ttk.Entry(row1, textvariable=self.diff_src).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(row1, text="폴더 선택", command=lambda: self.select_diff_path(self.diff_src)).pack(side="left", padx=4)

        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=3)
        ttk.Label(row2, text="대상(dst)").pack(side="left")
        ttk.Entry(row2, textvariable=self.diff_dst).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(row2, text="폴더 선택", command=lambda: self.select_diff_path(self.diff_dst)).pack(side="left", padx=4)

        btns = ttk.Frame(frame)
        btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="비교 실행", command=self.run_diff_compare).pack(side="left", padx=4)
        ttk.Button(btns, text="src→dst 동기화(추가/수정)", command=self.run_diff_sync).pack(side="left", padx=4)

        out_box = ttk.LabelFrame(frame, text="결과")
        out_box.pack(fill="both", expand=True, pady=6)
        self.diff_output = tk.Text(out_box, height=14, wrap="word")
        self.diff_output.pack(fill="both", expand=True, padx=6, pady=6)

    def select_diff_path(self, var: tk.StringVar):
        path = filedialog.askdirectory(title="폴더 선택")
        if path:
            var.set(path)

    def run_diff_compare(self):
        src = self.diff_src.get().strip()
        dst = self.diff_dst.get().strip()
        if not (src and dst):
            messagebox.showwarning("경로 필요", "src와 dst 폴더를 모두 지정하세요.")
            return
        if not (os.path.isdir(src) and os.path.isdir(dst)):
            messagebox.showwarning("경로 확인", "유효한 폴더를 입력하세요.")
            return
        diff = compare_dirs(src, dst)
        self.diff_last = diff
        lines = diff.summary_lines()
        self.diff_output.delete("1.0", tk.END)
        self.diff_output.insert(tk.END, "\n".join(lines))
        self.log("비교 완료")

    def run_diff_sync(self):
        if not self.diff_last:
            messagebox.showwarning("먼저 비교", "비교를 먼저 실행하세요.")
            return
        src = self.diff_src.get().strip()
        dst = self.diff_dst.get().strip()
        if not (src and dst):
            messagebox.showwarning("경로 필요", "src와 dst 폴더를 모두 지정하세요.")
            return
        copied = sync_dirs(src, dst, self.diff_last)
        self.diff_output.insert(tk.END, f"\n동기화 완료: 복사 {copied}개\n")
        self.diff_output.see(tk.END)
        self.log(f"동기화 완료: {copied}개 복사")

    # --- 탭: 마이그레이션/예약 실행 ---
    def create_migration_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="마이그레이션/스케줄")

        top = ttk.Frame(frame)
        top.pack(fill="x")

        mig_box = ttk.LabelFrame(top, text="팩 버전 마이그레이션 (치환 규칙)")
        mig_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        ttk.Radiobutton(mig_box, text="데이터 팩", variable=self.migrate_kind, value="datapacks").pack(anchor="w", padx=6, pady=2)
        ttk.Radiobutton(mig_box, text="리소스 팩", variable=self.migrate_kind, value="resourcepacks").pack(anchor="w", padx=6, pady=2)
        ttk.Button(mig_box, text="드라이 런 (미리보기)", command=lambda: self.run_migration(dry_run=True)).pack(anchor="w", padx=6, pady=4)
        ttk.Button(mig_box, text="실제 적용 (치환)", command=lambda: self.run_migration(dry_run=False)).pack(anchor="w", padx=6, pady=2)
        ttk.Label(mig_box, text="가이드:").pack(anchor="w", padx=6, pady=(6, 2))
        for line in GUIDE_LINES:
            ttk.Label(mig_box, text="- " + line).pack(anchor="w", padx=10)

        sched_box = ttk.LabelFrame(top, text="/schedule 예약 실행")
        sched_box.pack(side="left", fill="both", expand=True)
        s_row1 = ttk.Frame(sched_box)
        s_row1.pack(fill="x", pady=3)
        ttk.Label(s_row1, text="네임스페이스").pack(side="left")
        ttk.Entry(s_row1, textvariable=self.schedule_namespace, width=14).pack(side="left", padx=4)
        ttk.Label(s_row1, text="파일명").pack(side="left")
        ttk.Entry(s_row1, textvariable=self.schedule_name, width=14).pack(side="left", padx=4)
        s_row2 = ttk.Frame(sched_box)
        s_row2.pack(fill="x", pady=3)
        ttk.Label(s_row2, text="명령 리스트 (command:틱)").pack(side="left")
        ttk.Entry(s_row2, textvariable=self.schedule_entries).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(sched_box, text="스케줄 생성", command=self.build_schedule_file).pack(anchor="w", padx=6, pady=4)

        out_box = ttk.LabelFrame(frame, text="결과")
        out_box.pack(fill="both", expand=True, pady=8)
        self.migrate_output = tk.Text(out_box, height=14, wrap="word")
        self.migrate_output.pack(fill="both", expand=True, padx=6, pady=6)
        self.schedule_output = self.migrate_output

    def run_migration(self, dry_run: bool):
        base = self.ensure_workspace()
        if not base:
            return
        kind = self.migrate_kind.get()
        if not dry_run:
            try:
                backup = backup_before_migrate(base, kind)
                self.log(f"백업 생성: {backup}")
            except Exception as exc:
                messagebox.showerror("백업 실패", str(exc))
                return
        results = apply_migration(base, kind, dry_run=dry_run)
        self.migrate_output.delete("1.0", tk.END)
        self.migrate_output.insert(tk.END, "\n".join(results))
        suffix = "(드라이 런)" if dry_run else "(적용됨)"
        self.log(f"마이그레이션 완료 {suffix}")

    def build_schedule_file(self):
        base = self.ensure_workspace()
        if not base:
            return
        ns = self.schedule_namespace.get().strip() or "example"
        name = self.safe_filename(self.schedule_name.get().strip() or "timers")
        entries_raw = [x.strip() for x in self.schedule_entries.get().split(",") if x.strip()]
        entries: list[ScheduledCommand] = []
        for item in entries_raw:
            if ":" not in item:
                messagebox.showerror("형식 오류", "command:틱 형식으로 입력하세요.")
                return
            cmd, tick = item.split(":", 1)
            try:
                t = int(tick)
            except ValueError:
                messagebox.showerror("형식 오류", f"숫자 틱이 필요합니다: {tick}")
                return
            entries.append(ScheduledCommand(ticks=t, command=cmd))
        content = build_schedule(ns, name, entries)
        target_dir = os.path.join(base, "datapacks", ns, "data", ns, "functions")
        os.makedirs(target_dir, exist_ok=True)
        path = os.path.join(target_dir, f"{name}.mcfunction")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content + "\n")
        self.migrate_output.delete("1.0", tk.END)
        self.migrate_output.insert(tk.END, f"스케줄 함수 저장: {path}\n\n{content}")
        self.log(f"스케줄 함수 저장: {path}")

    # --- 탭: 아이템/NBT 빌더 ---
    def create_item_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="아이템/NBT")

        top = ttk.Frame(frame)
        top.pack(fill="x")
        ttk.Label(top, text="대상").pack(side="left")
        ttk.Entry(top, textvariable=self.item_target, width=8).pack(side="left", padx=4)
        ttk.Label(top, text="아이템 ID").pack(side="left")
        ttk.Entry(top, textvariable=self.item_id, width=22).pack(side="left", padx=4)
        ttk.Label(top, text="수량").pack(side="left")
        ttk.Entry(top, textvariable=self.item_count, width=6).pack(side="left", padx=4)

        name_row = ttk.Frame(frame)
        name_row.pack(fill="x", pady=4)
        ttk.Label(name_row, text="이름").pack(side="left")
        ttk.Entry(name_row, textvariable=self.item_name, width=26).pack(side="left", padx=4)
        ttk.Label(name_row, text="색상").pack(side="left")
        ttk.Entry(name_row, textvariable=self.item_color, width=10).pack(side="left", padx=4)
        ttk.Checkbutton(name_row, text="Italic", variable=self.item_italic).pack(side="left", padx=4)

        lore_row = ttk.Frame(frame)
        lore_row.pack(fill="x", pady=4)
        ttk.Label(lore_row, text="로어 (쉼표 구분)").pack(side="left")
        ttk.Entry(lore_row, textvariable=self.item_lore).pack(side="left", fill="x", expand=True, padx=4)

        ench_row = ttk.Frame(frame)
        ench_row.pack(fill="x", pady=4)
        ttk.Label(ench_row, text="인챈트 (id:레벨, 쉼표)").pack(side="left")
        ttk.Entry(ench_row, textvariable=self.item_enchants).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(ench_row, text="/give 생성", command=self.build_item_command).pack(side="left", padx=4)

        out_box = ttk.LabelFrame(frame, text="미리보기 / 복사")
        out_box.pack(fill="both", expand=True, pady=6)
        self.item_output = tk.Text(out_box, height=12, wrap="word")
        self.item_output.pack(fill="both", expand=True, padx=6, pady=6)
        i_btns = ttk.Frame(out_box)
        i_btns.pack(fill="x", pady=(0, 6))
        ttk.Button(i_btns, text="복사", command=self.copy_item_output).pack(side="left", padx=4)
        ttk.Button(i_btns, text="지우기", command=lambda: self.item_output.delete("1.0", tk.END)).pack(side="left", padx=4)

    def build_item_command(self):
        try:
            lore_list = [x.strip() for x in self.item_lore.get().split(",") if x.strip()]
            ench = parse_enchants(self.item_enchants.get())
            cmd = build_give_command(
                self.item_target.get().strip(),
                self.item_id.get().strip(),
                self.item_count.get(),
                name=self.item_name.get().strip(),
                color=self.item_color.get().strip(),
                italic=self.item_italic.get(),
                lore=lore_list,
                enchants=ench,
            )
        except Exception as exc:
            messagebox.showerror("생성 실패", str(exc))
            return
        self.item_output.delete("1.0", tk.END)
        self.item_output.insert(tk.END, cmd)
        self.log("/give 아이템 생성")

    def copy_item_output(self):
        text = self.item_output.get("1.0", tk.END).strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("복사 완료", "클립보드에 복사되었습니다.")

    # --- 탭: 사운드 (sounds.json) ---
    def create_sound_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="사운드")

        top = ttk.Frame(frame)
        top.pack(fill="x")
        ttk.Label(top, text="네임스페이스").pack(side="left")
        ttk.Entry(top, textvariable=self.sound_namespace, width=14).pack(side="left", padx=4)
        ttk.Label(top, text="이벤트").pack(side="left")
        ttk.Entry(top, textvariable=self.sound_event, width=18).pack(side="left", padx=4)
        ttk.Label(top, text="사운드 파일(콤마)").pack(side="left")
        ttk.Entry(top, textvariable=self.sound_files, width=28).pack(side="left", padx=4)

        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="자막(subtitle)").pack(side="left")
        ttk.Entry(row2, textvariable=self.sound_subtitle, width=26).pack(side="left", padx=4)
        ttk.Checkbutton(row2, text="replace=true", variable=self.sound_replace).pack(side="left", padx=4)
        ttk.Button(row2, text="생성/저장", command=self.save_sound_event).pack(side="left", padx=4)

        out_box = ttk.LabelFrame(frame, text="미리보기 / 로그")
        out_box.pack(fill="both", expand=True, pady=8)
        self.sound_output = tk.Text(out_box, height=12, wrap="word")
        self.sound_output.pack(fill="both", expand=True, padx=6, pady=6)
        s_btns = ttk.Frame(out_box)
        s_btns.pack(fill="x", pady=(0, 6))
        ttk.Button(s_btns, text="복사", command=self.copy_sound_output).pack(side="left", padx=4)
        ttk.Button(s_btns, text="지우기", command=lambda: self.sound_output.delete("1.0", tk.END)).pack(side="left", padx=4)

        hint = "사운드 경로는 assets/<ns>/sounds/<path>.ogg 위치 기준(확장자 없이). 기존 sounds.json이 있으면 병합됩니다."
        ttk.Label(frame, text=hint).pack(anchor="w", padx=6, pady=4)

    def save_sound_event(self):
        base = self.ensure_workspace()
        if not base:
            return
        ns = self.sound_namespace.get().strip() or "example"
        event = self.sound_event.get().strip() or "custom.sound"
        try:
            sounds = parse_sound_list(self.sound_files.get())
            data = build_sound_event(sounds, subtitle=self.sound_subtitle.get().strip() or None, replace=self.sound_replace.get())
            path = update_sounds_file(base, ns, event, data)
        except Exception as exc:
            messagebox.showerror("저장 실패", str(exc))
            return
        self.sound_output.delete("1.0", tk.END)
        self.sound_output.insert(tk.END, json.dumps({event: data}, ensure_ascii=False, indent=2) + f"\n\n저장: {path}")
        self.log(f"sounds.json 업데이트: {event}")

    def copy_sound_output(self):
        text = self.sound_output.get("1.0", tk.END).strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("복사 완료", "클립보드에 복사되었습니다.")

    # --- 탭: 로그/언어 검사 ---
    def create_log_lang_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="로그/언어")

        top = ttk.Frame(frame)
        top.pack(fill="x")

        log_box = ttk.LabelFrame(top, text="latest.log 오류 추출")
        log_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        l_row = ttk.Frame(log_box)
        l_row.pack(fill="x", pady=3)
        ttk.Entry(l_row, textvariable=self.log_path_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(l_row, text="파일 선택", command=self.browse_log_file).pack(side="left", padx=4)
        ttk.Button(l_row, text="파싱", command=self.parse_log_file).pack(side="left", padx=4)
        ttk.Label(log_box, text="ERROR/Exception/Caused by 등을 포함한 최근 로그를 뽑아 보여줍니다.").pack(anchor="w", padx=6, pady=2)

        lang_box = ttk.LabelFrame(top, text="lang 누락 키 검사(en_us ↔ ko_kr)")
        lang_box.pack(side="left", fill="both", expand=True)
        ttk.Label(lang_box, text="리소스 팩 선택").pack(anchor="w", padx=6, pady=2)
        self.lang_combo = ttk.Combobox(lang_box, textvariable=self.lang_pack_var, values=list_packs(self.workspace_var.get() or "", "resourcepacks"), state="readonly")
        self.lang_combo.pack(fill="x", padx=6, pady=2)
        ttk.Button(lang_box, text="목록 새로고침", command=self.refresh_lang_packs).pack(anchor="w", padx=6, pady=2)
        ttk.Button(lang_box, text="검사 실행", command=self.run_lang_check).pack(anchor="w", padx=6, pady=2)

        out_box = ttk.LabelFrame(frame, text="결과")
        out_box.pack(fill="both", expand=True, pady=8)
        self.log_output = tk.Text(out_box, height=10, wrap="word")
        self.log_output.pack(fill="both", expand=True, padx=6, pady=4)
        self.lang_output = tk.Text(out_box, height=8, wrap="word")
        self.lang_output.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    def browse_log_file(self):
        path = filedialog.askopenfilename(title="latest.log 선택", filetypes=[("log", "*.log"), ("All", "*.*")])
        if path:
            self.log_path_var.set(path)

    def parse_log_file(self):
        path = self.log_path_var.get().strip()
        if not path:
            messagebox.showwarning("파일 필요", "latest.log 파일을 선택하세요.")
            return
        try:
            lines = parse_log(path)
        except Exception as exc:
            messagebox.showerror("파싱 실패", str(exc))
            return
        self.log_output.delete("1.0", tk.END)
        self.log_output.insert(tk.END, "\n".join(lines))
        self.log_output.see(tk.END)
        self.log(f"로그 파싱: {path}")

    def refresh_lang_packs(self):
        base = self.workspace_var.get().strip()
        if not base:
            return
        packs = list_packs(base, "resourcepacks")
        self.lang_combo["values"] = packs
        if packs:
            self.lang_combo.current(0)

    def run_lang_check(self):
        base = self.ensure_workspace()
        if not base:
            return
        pack = self.lang_pack_var.get().strip()
        if not pack:
            messagebox.showwarning("선택 필요", "리소스 팩을 선택하세요.")
            return
        try:
            missing, extra = check_lang_pack(base, pack)
        except Exception as exc:
            messagebox.showerror("검사 실패", str(exc))
            return
        lines = [f"미번역(en_us에만 존재) {len(missing)}개", *missing[:50]]
        if len(missing) > 50:
            lines.append("... (더 있음)")
        lines.append(f"\n추가(ko_kr에만 존재) {len(extra)}개")
        lines.extend(extra[:50])
        if len(extra) > 50:
            lines.append("... (더 있음)")
        self.lang_output.delete("1.0", tk.END)
        self.lang_output.insert(tk.END, "\n".join(lines))
        self.lang_output.see(tk.END)
        self.log(f"lang 검사: {pack}")

    # --- 탭: JSON/모델 검사 ---
    def create_schema_model_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="JSON/모델 검사")

        top = ttk.Frame(frame)
        top.pack(fill="x")

        schema_box = ttk.LabelFrame(top, text="단일 JSON 검사 (recipe/loot/adv/predicate/tag)")
        schema_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        s_row = ttk.Frame(schema_box)
        s_row.pack(fill="x", pady=3)
        ttk.Entry(s_row, textvariable=self.schema_file_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(s_row, text="파일 선택", command=self.browse_schema_file).pack(side="left", padx=4)
        ttk.Button(s_row, text="검사", command=self.run_schema_file).pack(side="left", padx=4)
        ttk.Button(schema_box, text="워크스페이스 전체 스캔", command=self.scan_workspace_schema).pack(anchor="w", padx=6, pady=4)

        model_box = ttk.LabelFrame(top, text="모델 텍스처 누락 검사")
        model_box.pack(side="left", fill="both", expand=True)
        ttk.Label(model_box, text="리소스 팩 선택").pack(anchor="w", padx=6, pady=2)
        self.model_combo = ttk.Combobox(model_box, textvariable=self.model_pack_var, values=list_packs(self.workspace_var.get() or "", "resourcepacks"), state="readonly")
        self.model_combo.pack(fill="x", padx=6, pady=2)
        ttk.Button(model_box, text="목록 새로고침", command=self.refresh_model_packs).pack(anchor="w", padx=6, pady=2)
        ttk.Button(model_box, text="검사 실행", command=self.run_model_check).pack(anchor="w", padx=6, pady=2)

        out_box = ttk.LabelFrame(frame, text="결과")
        out_box.pack(fill="both", expand=True, pady=8)
        self.schema_output = tk.Text(out_box, height=10, wrap="word")
        self.schema_output.pack(fill="both", expand=True, padx=6, pady=4)
        self.model_output = tk.Text(out_box, height=8, wrap="word")
        self.model_output.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    def browse_schema_file(self):
        path = filedialog.askopenfilename(title="JSON 파일 선택", filetypes=[("json", "*.json"), ("All", "*.*")])
        if path:
            self.schema_file_var.set(path)

    def run_schema_file(self):
        path = self.schema_file_var.get().strip()
        if not path:
            messagebox.showwarning("파일 필요", "검사할 JSON 파일을 선택하세요.")
            return
        try:
            issues = validate_file(path)
        except Exception as exc:
            messagebox.showerror("검사 실패", str(exc))
            return
        self.schema_output.delete("1.0", tk.END)
        self.schema_output.insert(tk.END, "\n".join(issues))
        self.schema_output.see(tk.END)
        self.log(f"JSON 검사: {path}")

    def scan_workspace_schema(self):
        base = self.ensure_workspace()
        if not base:
            return
        try:
            results = scan_workspace_json(base)
        except Exception as exc:
            messagebox.showerror("스캔 실패", str(exc))
            return
        self.schema_output.delete("1.0", tk.END)
        self.schema_output.insert(tk.END, "\n".join(results))
        self.schema_output.see(tk.END)
        self.log("워크스페이스 JSON 스캔 완료")

    def refresh_model_packs(self):
        base = self.workspace_var.get().strip()
        if not base:
            return
        packs = list_packs(base, "resourcepacks")
        self.model_combo["values"] = packs
        if packs:
            self.model_combo.current(0)

    def run_model_check(self):
        base = self.ensure_workspace()
        if not base:
            return
        pack = self.model_pack_var.get().strip()
        if not pack:
            messagebox.showwarning("선택 필요", "리소스 팩을 선택하세요.")
            return
        try:
            results = check_models(base, pack)
        except Exception as exc:
            messagebox.showerror("검사 실패", str(exc))
            return
        self.model_output.delete("1.0", tk.END)
        self.model_output.insert(tk.END, "\n".join(results))
        self.model_output.see(tk.END)
        self.log(f"모델 검사: {pack}")

    # --- 탭: 네임스페이스/리포트 ---
    def create_namespace_report_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="네임스페이스/리포트")

        ns_box = ttk.LabelFrame(frame, text="네임스페이스 변경 (데이터팩)")
        ns_box.pack(fill="x", pady=4)
        ns_row = ttk.Frame(ns_box)
        ns_row.pack(fill="x", pady=3)
        ttk.Label(ns_row, text="old").pack(side="left")
        ttk.Entry(ns_row, textvariable=self.ns_old, width=14).pack(side="left", padx=4)
        ttk.Label(ns_row, text="new").pack(side="left")
        ttk.Entry(ns_row, textvariable=self.ns_new, width=14).pack(side="left", padx=4)
        ttk.Button(ns_row, text="리네임 실행", command=self.run_namespace_rename).pack(side="left", padx=4)
        ttk.Label(ns_box, text="폴더명 및 파일 내 old: 참조를 new:로 치환합니다. 백업 후 사용을 권장합니다.").pack(anchor="w", padx=6, pady=2)

        rep_box = ttk.LabelFrame(frame, text="워크스페이스 리포트 (Markdown)")
        rep_box.pack(fill="x", pady=4)
        ttk.Button(rep_box, text="리포트 생성", command=self.build_report).pack(anchor="w", padx=6, pady=4)

        out_box = ttk.LabelFrame(frame, text="결과/로그")
        out_box.pack(fill="both", expand=True, pady=6)
        self.ns_output = tk.Text(out_box, height=10, wrap="word")
        self.ns_output.pack(fill="both", expand=True, padx=6, pady=4)
        self.report_output = self.ns_output

    def run_namespace_rename(self):
        base = self.ensure_workspace()
        if not base:
            return
        old = self.ns_old.get().strip()
        new = self.ns_new.get().strip()
        if not (old and new):
            messagebox.showwarning("입력 필요", "old와 new 네임스페이스를 입력하세요.")
            return
        try:
            logs = rename_namespace(base, old, new)
        except Exception as exc:
            messagebox.showerror("리네임 실패", str(exc))
            return
        self.ns_output.delete("1.0", tk.END)
        self.ns_output.insert(tk.END, "\n".join(logs))
        self.ns_output.see(tk.END)
        self.log(f"네임스페이스 변경: {old} -> {new}")

    def build_report(self):
        base = self.ensure_workspace()
        if not base:
            return
        report = build_pack_report(base)
        self.ns_output.delete("1.0", tk.END)
        self.ns_output.insert(tk.END, report)
        self.ns_output.see(tk.END)
        self.log("워크스페이스 리포트 생성")

    # --- 탭: 구조 블록 NBT 확인 ---
    def create_structure_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="구조/NBT")

        ttk.Label(frame, text=".nbt 구조 파일을 열어 크기/메타를 확인합니다. nbtlib이 있으면 더 자세한 정보를 보여줄 수 있습니다.").pack(anchor="w", padx=6, pady=4)
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=4)
        ttk.Entry(row, textvariable=self.nbt_path_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(row, text="파일 선택", command=self.browse_nbt_file).pack(side="left", padx=4)
        ttk.Button(row, text="읽기", command=self.read_nbt_file).pack(side="left", padx=4)

        out_box = ttk.LabelFrame(frame, text="결과")
        out_box.pack(fill="both", expand=True, pady=8)
        self.nbt_output = tk.Text(out_box, height=14, wrap="word")
        self.nbt_output.pack(fill="both", expand=True, padx=6, pady=6)

    def browse_nbt_file(self):
        path = filedialog.askopenfilename(title="구조 NBT 파일 선택", filetypes=[("nbt", "*.nbt"), ("All", "*.*")])
        if path:
            self.nbt_path_var.set(path)

    def read_nbt_file(self):
        path = self.nbt_path_var.get().strip()
        if not path:
            messagebox.showwarning("파일 필요", ".nbt 파일을 선택하세요.")
            return
        try:
            data = read_nbt(path)
        except Exception as exc:
            messagebox.showerror("읽기 실패", str(exc))
            return
        self.nbt_output.delete("1.0", tk.END)
        self.nbt_output.insert(tk.END, json.dumps(data, ensure_ascii=False, indent=2))
        self.nbt_output.see(tk.END)
        self.log(f"NBT 읽기: {path}")

    # --- 탭: 함수 참조 그래프 ---
    def create_callgraph_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="함수 그래프")

        top = ttk.Frame(frame)
        top.pack(fill="x")
        ttk.Label(top, text="시작 함수(콤마)").pack(side="left")
        ttk.Entry(top, textvariable=self.graph_start, width=40).pack(side="left", padx=4)
        ttk.Label(top, text="깊이").pack(side="left")
        ttk.Entry(top, textvariable=self.graph_depth, width=6).pack(side="left", padx=4)
        ttk.Button(top, text="그래프 생성", command=self.run_callgraph).pack(side="left", padx=4)

        out_box = ttk.LabelFrame(frame, text="결과")
        out_box.pack(fill="both", expand=True, pady=8)
        self.graph_output = tk.Text(out_box, height=14, wrap="word")
        self.graph_output.pack(fill="both", expand=True, padx=6, pady=6)

        hint = "함수 이름 예: example:load. 시작 함수가 비어있으면 load/tick 등을 자동 탐색합니다."
        ttk.Label(frame, text=hint).pack(anchor="w", padx=6, pady=4)

    def run_callgraph(self):
        base = self.ensure_workspace()
        if not base:
            return
        graph, id_to_path = build_call_graph(base)
        starts_text = self.graph_start.get().strip()
        if starts_text:
            starts = [s.strip() for s in starts_text.split(",") if s.strip()]
        else:
            # 기본 시작점: load/tick
            starts = [fid for fid in id_to_path if fid.endswith("load") or fid.endswith("tick")]
        if not starts:
            messagebox.showwarning("시작점 없음", "시작 함수를 지정하거나 load/tick이 존재하는지 확인하세요.")
            return
        reach = reachable_from(graph, starts, depth=max(0, self.graph_depth.get()))
        lines = [f"시작: {', '.join(starts)}", f"도달 함수 {len(reach)}개:"]
        for fid in sorted(reach):
            lines.append(f"- {fid}")
        self.graph_output.delete("1.0", tk.END)
        self.graph_output.insert(tk.END, "\n".join(lines))
        self.graph_output.see(tk.END)
        self.log("함수 그래프 생성 완료")

    # --- 탭 버튼(3줄) ---
    def rebuild_tab_bar(self):
        for child in self.tab_bar.winfo_children():
            child.destroy()
        tabs = self.notebook.tabs()
        titles = [self.notebook.tab(t, "text") for t in tabs]
        rows = 3
        if not tabs:
            return
        # 필터 적용
        keyword = self.tab_filter_var.get().strip().lower()
        filtered = [(t, title) for t, title in zip(tabs, titles) if keyword in title.lower()]
        if not filtered:
            filtered = list(zip(tabs, titles))
        # 균등 배치
        per_row = max(4, math.ceil(len(filtered) / rows))
        self.tab_buttons = {}
        for idx, (tab, title) in enumerate(filtered):
            r = idx // per_row
            c = idx % per_row
            btn = ttk.Button(self.tab_bar, text=title, command=lambda t=tab: self.notebook.select(t), style="TabButton.TButton")
            btn.grid(row=r, column=c, padx=2, pady=2, sticky="ew")
            self.tab_bar.grid_columnconfigure(c, weight=1)
            self.tab_buttons[tab] = btn
        self.highlight_tab_buttons()

    def highlight_tab_buttons(self):
        if not hasattr(self, "tab_buttons"):
            return
        current = self.notebook.select()
        for tab, btn in self.tab_buttons.items():
            if tab == current:
                btn.configure(style="TabButtonActive.TButton")
            else:
                btn.configure(style="TabButton.TButton")

    # --- 탭 라벨 관리 / 언어 ---
    def setup_tab_labels(self):
        tabs = self.notebook.tabs()
        labels = [
            ("프로젝트 허브", "Project Hub"),
            ("크리에이터 유틸", "Creator Tools"),
            ("좌표/시간 계산기", "Coords/Time"),
            ("명령어 & JSON 생성", "Commands & JSON"),
            ("고급 명령어", "Advanced Cmd"),
            ("팩 스캐폴딩 & JSON", "Pack Scaffolding"),
            ("개발 고급 도구", "Dev Tools"),
            ("품질/체크리스트", "Quality/Checklist"),
            ("배포/자동화", "Deploy/Automation"),
            ("편집/유지보수", "Edit/Maintenance"),
            ("출시 문서", "Release Docs"),
            ("통계/인벤토리", "Stats/Inventory"),
            ("서버 설정", "Server Settings"),
            ("레시피 생성", "Recipes"),
            ("파티클/이펙트", "Particles/Effects"),
            ("텍스트/채팅", "Text/Chat"),
            ("태그/메타", "Tags/Meta"),
            ("비교/동기화", "Diff/Sync"),
            ("마이그레이션/스케줄", "Migration/Schedule"),
            ("아이템/NBT", "Item/NBT"),
            ("사운드", "Sound"),
            ("로그/언어", "Log/Lang"),
            ("JSON/모델 검사", "JSON/Model Check"),
            ("네임스페이스/리포트", "Namespace/Report"),
            ("구조/NBT", "Structure/NBT"),
            ("함수 그래프", "Call Graph"),
        ]
        self.tab_label_map = {}
        for tab, (ko, en) in zip(tabs, labels):
            self.tab_label_map[tab] = {"ko": ko, "en": en}
        self.apply_language(trigger_rebuild=False)

    def apply_language(self, trigger_rebuild: bool):
        code = self.language_var.get()
        for tab, label in self.tab_label_map.items():
            text = label.get(code, label.get("ko", ""))
            self.notebook.tab(tab, text=text)
        if trigger_rebuild:
            self.rebuild_tab_bar()

    def change_language(self, label: str):
        code = "ko" if label.startswith("한국") else "en"
        self.language_var.set(code)
        self.apply_language(trigger_rebuild=True)

    # --- 탭: 팩 스캐폴딩/JSON 생성 ---
    def create_pack_tab(self, notebook: ttk.Notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="팩 스캐폴딩 & JSON")

        upper = ttk.Frame(frame)
        upper.pack(fill="x")

        dp_box = ttk.LabelFrame(upper, text="데이터 팩 생성")
        dp_box.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=4)
        dp_row1 = ttk.Frame(dp_box)
        dp_row1.pack(fill="x", pady=3)
        ttk.Label(dp_row1, text="네임스페이스").pack(side="left")
        ttk.Entry(dp_row1, textvariable=self.dp_namespace_var, width=14).pack(side="left", padx=4)
        ttk.Label(dp_row1, text="pack_format").pack(side="left")
        ttk.Entry(dp_row1, textvariable=self.dp_format_var, width=6).pack(side="left", padx=4)
        dp_row2 = ttk.Frame(dp_box)
        dp_row2.pack(fill="x", pady=3)
        ttk.Label(dp_row2, text="설명").pack(side="left")
        ttk.Entry(dp_row2, textvariable=self.dp_desc_var, width=50).pack(side="left", padx=4)
        dp_row3 = ttk.Frame(dp_box)
        dp_row3.pack(fill="x", pady=3)
        ttk.Checkbutton(dp_row3, text="load/tick 자동 태그 생성", variable=self.include_load_var).pack(side="left")
        ttk.Checkbutton(dp_row3, text="예제 함수 생성", variable=self.include_tick_var).pack(side="left", padx=6)
        ttk.Button(dp_row3, text="데이터 팩 만들기", command=self.create_datapack).pack(side="left", padx=8)

        rp_box = ttk.LabelFrame(upper, text="리소스 팩 생성")
        rp_box.pack(side="left", fill="both", expand=True, pady=4)
        rp_row1 = ttk.Frame(rp_box)
        rp_row1.pack(fill="x", pady=3)
        ttk.Label(rp_row1, text="네임스페이스").pack(side="left")
        ttk.Entry(rp_row1, textvariable=self.rp_namespace_var, width=14).pack(side="left", padx=4)
        ttk.Label(rp_row1, text="pack_format").pack(side="left")
        ttk.Entry(rp_row1, textvariable=self.rp_format_var, width=6).pack(side="left", padx=4)
        rp_row2 = ttk.Frame(rp_box)
        rp_row2.pack(fill="x", pady=3)
        ttk.Label(rp_row2, text="설명").pack(side="left")
        ttk.Entry(rp_row2, textvariable=self.rp_desc_var, width=50).pack(side="left", padx=4)
        ttk.Button(rp_row2, text="리소스 팩 만들기", command=self.create_resourcepack).pack(side="left", padx=8)

        lower = ttk.Frame(frame)
        lower.pack(fill="both", expand=True, pady=8)

        loot_box = ttk.LabelFrame(lower, text="간단한 Loot Table 생성")
        loot_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        l_row1 = ttk.Frame(loot_box)
        l_row1.pack(fill="x", pady=3)
        ttk.Label(l_row1, text="네임스페이스").pack(side="left")
        ttk.Entry(l_row1, textvariable=self.loot_namespace_var, width=12).pack(side="left", padx=3)
        ttk.Label(l_row1, text="파일 이름").pack(side="left")
        ttk.Entry(l_row1, textvariable=self.loot_name_var, width=14).pack(side="left", padx=3)
        l_row2 = ttk.Frame(loot_box)
        l_row2.pack(fill="x", pady=3)
        ttk.Label(l_row2, text="아이템").pack(side="left")
        ttk.Entry(l_row2, textvariable=self.loot_item_var, width=22).pack(side="left", padx=3)
        ttk.Label(l_row2, text="가중치").pack(side="left")
        ttk.Entry(l_row2, textvariable=self.loot_weight_var, width=6).pack(side="left", padx=3)
        l_row3 = ttk.Frame(loot_box)
        l_row3.pack(fill="x", pady=3)
        ttk.Label(l_row3, text="최소 수량").pack(side="left")
        ttk.Entry(l_row3, textvariable=self.loot_min_var, width=6).pack(side="left", padx=3)
        ttk.Label(l_row3, text="최대 수량").pack(side="left")
        ttk.Entry(l_row3, textvariable=self.loot_max_var, width=6).pack(side="left", padx=3)
        ttk.Button(l_row3, text="JSON 미리보기", command=self.preview_loot_table).pack(side="left", padx=8)
        ttk.Button(l_row3, text="파일로 저장", command=self.save_loot_table).pack(side="left", padx=4)

        preview_box = ttk.LabelFrame(lower, text="미리보기 / JSON 출력")
        preview_box.pack(side="left", fill="both", expand=True)
        self.json_preview = tk.Text(preview_box, wrap="word")
        self.json_preview.pack(fill="both", expand=True, padx=6, pady=6)

    def create_datapack(self):
        base = self.ensure_workspace()
        if not base:
            return
        namespace = self.dp_namespace_var.get().strip()
        if not namespace:
            messagebox.showwarning("네임스페이스 필요", "네임스페이스를 입력해주세요.")
            return
        target = os.path.join(base, "datapacks", namespace)
        data_ns = os.path.join(target, "data", namespace)
        os.makedirs(os.path.join(data_ns, "functions"), exist_ok=True)
        pack_meta = {
            "pack": {
                "pack_format": self.dp_format_var.get(),
                "description": self.dp_desc_var.get().strip() or "새 데이터 팩",
            }
        }
        with open(os.path.join(target, "pack.mcmeta"), "w", encoding="utf-8") as f:
            json.dump(pack_meta, f, ensure_ascii=False, indent=2)

        if self.include_load_var.get():
            load_tag_dir = os.path.join(target, "data", "minecraft", "tags", "functions")
            os.makedirs(load_tag_dir, exist_ok=True)
            load_tag = {"values": [f"{namespace}:load"]}
            tick_tag = {"values": [f"{namespace}:tick"]}
            with open(os.path.join(load_tag_dir, "load.json"), "w", encoding="utf-8") as f:
                json.dump(load_tag, f, ensure_ascii=False, indent=2)
            with open(os.path.join(load_tag_dir, "tick.json"), "w", encoding="utf-8") as f:
                json.dump(tick_tag, f, ensure_ascii=False, indent=2)

        if self.include_tick_var.get():
            load_fn = os.path.join(data_ns, "functions", "load.mcfunction")
            tick_fn = os.path.join(data_ns, "functions", "tick.mcfunction")
            if not os.path.exists(load_fn):
                with open(load_fn, "w", encoding="utf-8") as f:
                    f.write("# 최초 로드 시 실행\nsay 데이터 팩 로드 완료\n")
            if not os.path.exists(tick_fn):
                with open(tick_fn, "w", encoding="utf-8") as f:
                    f.write("# 매 틱마다 실행\n")

        self.log(f"데이터 팩 생성 완료: {target}")
        messagebox.showinfo("완료", f"데이터 팩이 생성되었습니다:\n{target}")
        self.open_folder(target)

    def create_resourcepack(self):
        base = self.ensure_workspace()
        if not base:
            return
        namespace = self.rp_namespace_var.get().strip()
        if not namespace:
            messagebox.showwarning("네임스페이스 필요", "네임스페이스를 입력해주세요.")
            return
        target = os.path.join(base, "resourcepacks", namespace)
        assets_ns = os.path.join(target, "assets", namespace)
        os.makedirs(os.path.join(assets_ns, "lang"), exist_ok=True)
        os.makedirs(os.path.join(assets_ns, "textures"), exist_ok=True)
        pack_meta = {
            "pack": {
                "pack_format": self.rp_format_var.get(),
                "description": self.rp_desc_var.get().strip() or "새 리소스 팩",
            }
        }
        with open(os.path.join(target, "pack.mcmeta"), "w", encoding="utf-8") as f:
            json.dump(pack_meta, f, ensure_ascii=False, indent=2)
        lang_path = os.path.join(assets_ns, "lang", "ko_kr.json")
        if not os.path.exists(lang_path):
            with open(lang_path, "w", encoding="utf-8") as f:
                json.dump({"item.namespace.example": "예시 항목"}, f, ensure_ascii=False, indent=2)
        self.log(f"리소스 팩 생성 완료: {target}")
        messagebox.showinfo("완료", f"리소스 팩이 생성되었습니다:\n{target}")
        self.open_folder(target)

    def preview_loot_table(self):
        try:
            data = self.build_loot_json()
        except ValueError as exc:
            messagebox.showerror("입력 오류", str(exc))
            return
        self.json_preview.delete("1.0", tk.END)
        self.json_preview.insert(tk.END, json.dumps(data, ensure_ascii=False, indent=2))

    def save_loot_table(self):
        base = self.ensure_workspace()
        if not base:
            return
        try:
            data = self.build_loot_json()
        except ValueError as exc:
            messagebox.showerror("입력 오류", str(exc))
            return
        namespace = self.loot_namespace_var.get().strip() or "example"
        name = self.loot_name_var.get().strip() or "loot"
        target_dir = os.path.join(base, "datapacks", namespace, "data", namespace, "loot_tables")
        os.makedirs(target_dir, exist_ok=True)
        path = os.path.join(target_dir, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.log(f"Loot Table 저장: {path}")
        messagebox.showinfo("저장 완료", f"Loot Table이 저장되었습니다:\n{path}")
        self.json_preview.delete("1.0", tk.END)
        self.json_preview.insert(tk.END, json.dumps(data, ensure_ascii=False, indent=2))

    def build_loot_json(self):
        item = self.loot_item_var.get().strip()
        if not item:
            raise ValueError("아이템 ID를 입력하세요.")
        weight = int(self.loot_weight_var.get())
        cmin = int(self.loot_min_var.get())
        cmax = int(self.loot_max_var.get())
        entry = {"type": "minecraft:item", "name": item}
        if weight > 1:
            entry["weight"] = weight
        if cmin != 1 or cmax != 1:
            entry["functions"] = [
                {"function": "minecraft:set_count", "count": {"min": cmin, "max": cmax}}
            ]
        loot = {"pools": [{"rolls": 1, "entries": [entry]}]}
        return loot


def main():
    root = tk.Tk()
    app = MinecraftToolApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
