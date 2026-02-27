# src/gui.py
import os
import sys
import subprocess
import time
import threading
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageTk  # Pillow

from graph import build_graph
from search_algorithms import bfs_path, dfs_path, astar_path
from clustering import kmeans_clusters
from metrics import path_cost
from visualization import draw_graph, draw_clusters, draw_route

PICO_MIN_PEDIDOS = 8
K_ENTREGADORES = 2

# Pasta raiz do projeto (independe de onde você roda)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def p(*parts):
    return os.path.join(BASE_DIR, *parts)

def open_path(path: str):
    """Abre arquivo ou pasta no Windows/macOS/Linux."""
    path = os.path.abspath(path)
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
    except Exception as e:
        messagebox.showerror("Erro", f"Não consegui abrir:\n{e}")

def safe_read_csv(path: str):
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        raise ValueError(
            "O arquivo data/deliveries.csv está sem colunas (vazio ou só com linhas em branco).\n"
            "Abra data/deliveries.csv, cole o CSV com cabeçalho e pedidos, e salve (Ctrl+S)."
        )

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sabor Express — Rota Inteligente (IA)")
        self.geometry("1080x680")
        self.minsize(1000, 620)

        self.last_run_dir = None
        self.last_report_path = None
        self.last_route_path = None
        self.last_graph_path = None
        self.last_clusters_path = None

        # refs para imagens (evitar GC)
        self._img_graph = None
        self._img_route = None
        self._img_clusters = None

        self._build_ui()
        self._load_nodes()

    # ---------------- UI ----------------
    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except:
            pass

        # Top bar
        top = ttk.Frame(self, padding=12)
        top.pack(fill="x")

        title = ttk.Label(top, text="Rota Inteligente — Sabor Express", font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 8))

        ttk.Label(top, text="Origem:").grid(row=1, column=0, sticky="w", padx=(0, 6))
        self.cmb_start = ttk.Combobox(top, state="readonly", width=22)
        self.cmb_start.grid(row=1, column=1, sticky="w", padx=(0, 16))

        ttk.Label(top, text="Destino:").grid(row=1, column=2, sticky="w", padx=(0, 6))
        self.cmb_goal = ttk.Combobox(top, state="readonly", width=22)
        self.cmb_goal.grid(row=1, column=3, sticky="w", padx=(0, 16))

        self.btn_run = ttk.Button(top, text="Rodar Otimização", command=self.run_all_async)
        self.btn_run.grid(row=1, column=4, sticky="w")

        self.btn_open_run = ttk.Button(top, text="Abrir pasta do run", command=self.open_last_run)
        self.btn_open_run.grid(row=1, column=5, sticky="w", padx=(8, 0))

        # Progress + status
        bar = ttk.Frame(self, padding=(12, 0, 12, 8))
        bar.pack(fill="x")

        self.lbl_status = ttk.Label(bar, text="Status: pronto.")
        self.lbl_status.pack(side="left")

        self.progress = ttk.Progressbar(bar, mode="indeterminate", length=220)
        self.progress.pack(side="right")

        # Main content: left (log + table) / right (previews)
        main = ttk.Frame(self, padding=12)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)

        right = ttk.Frame(main)
        right.pack(side="right", fill="y", padx=(12, 0))

        # Results table (A)
        table_card = ttk.LabelFrame(left, text="Resultados (Comparação)", padding=10)
        table_card.pack(fill="x")

        cols = ("algoritmo", "tempo_min", "nos", "ms")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings", height=4)
        self.tree.heading("algoritmo", text="Algoritmo")
        self.tree.heading("tempo_min", text="Tempo (min)")
        self.tree.heading("nos", text="Nós expandidos")
        self.tree.heading("ms", text="Execução (ms)")

        self.tree.column("algoritmo", width=120, anchor="w")
        self.tree.column("tempo_min", width=120, anchor="center")
        self.tree.column("nos", width=140, anchor="center")
        self.tree.column("ms", width=120, anchor="center")

        self.tree.pack(fill="x")

        # Buttons (B)
        btns = ttk.Frame(left, padding=(0, 8, 0, 0))
        btns.pack(fill="x")

        self.btn_open_report = ttk.Button(btns, text="Abrir report.txt", command=self.open_last_report, state="disabled")
        self.btn_open_report.pack(side="left")

        self.btn_open_route = ttk.Button(btns, text="Abrir imagem da rota", command=self.open_last_route, state="disabled")
        self.btn_open_route.pack(side="left", padx=(8, 0))

        self.btn_copy_summary = ttk.Button(btns, text="Copiar resumo", command=self.copy_summary, state="disabled")
        self.btn_copy_summary.pack(side="left", padx=(8, 0))

        # Log
        log_card = ttk.LabelFrame(left, text="Log", padding=10)
        log_card.pack(fill="both", expand=True, pady=(10, 0))

        self.txt = tk.Text(log_card, height=16, wrap="word")
        self.txt.pack(fill="both", expand=True)

        # Previews (C)
        preview_title = ttk.Label(right, text="Pré-visualização", font=("Segoe UI", 12, "bold"))
        preview_title.pack(anchor="w")

        self.preview_info = ttk.Label(right, text="Rode uma otimização para ver as imagens.", foreground="#666")
        self.preview_info.pack(anchor="w", pady=(0, 8))

        self.lbl_prev_graph = ttk.LabelFrame(right, text="Grafo", padding=8)
        self.lbl_prev_graph.pack(fill="x", pady=(0, 8))
        self.canvas_graph = ttk.Label(self.lbl_prev_graph)
        self.canvas_graph.pack()

        self.lbl_prev_route = ttk.LabelFrame(right, text="Rota (A*)", padding=8)
        self.lbl_prev_route.pack(fill="x", pady=(0, 8))
        self.canvas_route = ttk.Label(self.lbl_prev_route)
        self.canvas_route.pack()

        self.lbl_prev_clusters = ttk.LabelFrame(right, text="Clusters (K-Means)", padding=8)
        self.lbl_prev_clusters.pack(fill="x")
        self.canvas_clusters = ttk.Label(self.lbl_prev_clusters)
        self.canvas_clusters.pack()

    def _load_nodes(self):
        try:
            nodes = pd.read_csv(p("data", "nodes.csv"))
            node_list = nodes["node"].tolist()
            self.cmb_start["values"] = node_list
            self.cmb_goal["values"] = node_list

            if "Centro" in node_list:
                self.cmb_start.set("Centro")
            else:
                self.cmb_start.current(0)

            if "Paraiso" in node_list:
                self.cmb_goal.set("Paraiso")
            else:
                self.cmb_goal.current(min(1, len(node_list) - 1))
        except Exception as e:
            messagebox.showerror("Erro", f"Não consegui carregar data/nodes.csv\n{e}")

    # ---------------- helpers ----------------
    def log(self, msg: str):
        self.txt.insert("end", msg + "\n")
        self.txt.see("end")
        self.update_idletasks()

    def set_status(self, msg: str):
        self.lbl_status.config(text=f"Status: {msg}")
        self.update_idletasks()

    def set_running(self, running: bool):
        if running:
            self.btn_run.config(state="disabled")
            self.progress.start(10)
        else:
            self.progress.stop()
            self.btn_run.config(state="normal")

    def open_last_run(self):
        if self.last_run_dir and os.path.exists(self.last_run_dir):
            open_path(self.last_run_dir)
        else:
            open_path(p("outputs"))

    def open_last_report(self):
        if self.last_report_path and os.path.exists(self.last_report_path):
            open_path(self.last_report_path)

    def open_last_route(self):
        if self.last_route_path and os.path.exists(self.last_route_path):
            open_path(self.last_route_path)

    def copy_summary(self):
        # Copia o conteúdo da tabela de resultados (bom pro README/vídeo)
        rows = []
        for iid in self.tree.get_children():
            vals = self.tree.item(iid, "values")
            rows.append(f"{vals[0]} | tempo(min)={vals[1]} | nós={vals[2]} | ms={vals[3]}")
        text = "\n".join(rows) if rows else "Sem resultados."
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copiado", "Resumo copiado para a área de transferência!")

    def _set_table(self, bfs, dfs, astar):
        # limpa
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        def fmt(x):
            if x is None:
                return "-"
            if isinstance(x, float):
                return f"{x:.2f}"
            return str(x)

        self.tree.insert("", "end", values=("BFS", fmt(bfs["tempo"]), fmt(bfs["nos"]), fmt(bfs["ms"])))
        self.tree.insert("", "end", values=("DFS", fmt(dfs["tempo"]), fmt(dfs["nos"]), fmt(dfs["ms"])))
        self.tree.insert("", "end", values=("A*",  fmt(astar["tempo"]), fmt(astar["nos"]), fmt(astar["ms"])))

        self.btn_open_report.config(state="normal")
        self.btn_open_route.config(state="normal")
        self.btn_copy_summary.config(state="normal")

    def _load_preview(self, img_path: str, target: str, max_size=(310, 210)):
        """Carrega uma imagem, redimensiona e coloca no label correto."""
        if not img_path or not os.path.exists(img_path):
            return

        img = Image.open(img_path)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        tkimg = ImageTk.PhotoImage(img)

        if target == "graph":
            self._img_graph = tkimg
            self.canvas_graph.config(image=tkimg)
        elif target == "route":
            self._img_route = tkimg
            self.canvas_route.config(image=tkimg)
        elif target == "clusters":
            self._img_clusters = tkimg
            self.canvas_clusters.config(image=tkimg)

    # ---------------- RUN (async) ----------------
    def run_all_async(self):
        # roda em thread pra não travar a interface
        t = threading.Thread(target=self.run_all, daemon=True)
        t.start()

    def run_all(self):
        # UI reset
        self.txt.delete("1.0", "end")
        self.preview_info.config(text="Gerando… (as imagens vão aparecer aqui)")
        self.set_status("executando…")
        self.set_running(True)

        try:
            start = self.cmb_start.get().strip()
            goal = self.cmb_goal.get().strip()

            if not start or not goal:
                raise ValueError("Selecione origem e destino.")

            if start == goal:
                raise ValueError("Origem e destino não podem ser iguais.")

            # cria pasta do run
            ts = time.strftime("%Y%m%d_%H%M%S")
            run_dir = p("outputs", f"run_{ts}")
            os.makedirs(run_dir, exist_ok=True)

            self.last_run_dir = run_dir
            self.log(f"Run criado: {run_dir}")

            # 1) Grafo
            self.log("1) Carregando grafo…")
            G = build_graph(p("data", "nodes.csv"), p("data", "edges.csv"))

            graph_path = os.path.join(run_dir, "graph.png")
            draw_graph(G, graph_path)
            self.last_graph_path = graph_path
            self.log("   - Gerado: graph.png")

            # 2) Pedidos
            self.log("2) Lendo pedidos…")
            deliveries_path = p("data", "deliveries.csv")
            self.log(f"   - Arquivo: {deliveries_path}")

            if not os.path.exists(deliveries_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {deliveries_path}")

            deliveries = safe_read_csv(deliveries_path)
            n_pedidos = len(deliveries)
            if n_pedidos <= 0:
                raise ValueError("deliveries.csv não tem pedidos (0 linhas).")

            self.log(f"   - Pedidos: {n_pedidos}")

            # 3) Pico + clustering
            clustered_csv_path = os.path.join(run_dir, "deliveries_with_clusters.csv")
            clusters_path = os.path.join(run_dir, "clusters.png")
            self.last_clusters_path = None  # reset

            if n_pedidos >= PICO_MIN_PEDIDOS:
                self.log(f"3) PICO: {n_pedidos} >= {PICO_MIN_PEDIDOS} → K-Means (k={K_ENTREGADORES})")
                deliveries_clustered = kmeans_clusters(
                    deliveries_csv=deliveries_path,
                    k=K_ENTREGADORES,
                    out_csv=clustered_csv_path
                )
                draw_clusters(deliveries_clustered, clusters_path)
                self.last_clusters_path = clusters_path
                self.log("   - Gerado: clusters.png")
            else:
                self.log(f"3) NORMAL: {n_pedidos} < {PICO_MIN_PEDIDOS} → sem clustering")
                deliveries.to_csv(clustered_csv_path, index=False)

            # 4) Rotas BFS/DFS/A*
            self.log("4) Calculando rotas (BFS / DFS / A*)…")

            # BFS
            t0 = time.time()
            p_bfs, ex_bfs = bfs_path(G, start, goal)
            ms_bfs = (time.time() - t0) * 1000
            cost_bfs = path_cost(G, p_bfs, "time_min") if p_bfs else None

            # DFS
            t0 = time.time()
            p_dfs, ex_dfs = dfs_path(G, start, goal)
            ms_dfs = (time.time() - t0) * 1000
            cost_dfs = path_cost(G, p_dfs, "time_min") if p_dfs else None

            # A*
            t0 = time.time()
            p_astar, ex_astar, cost_astar = astar_path(G, start, goal, weight="time_min")
            ms_astar = (time.time() - t0) * 1000

            # 5) Rota (A*) imagem
            route_path = os.path.join(run_dir, "route_result.png")
            draw_route(G, p_astar, route_path)
            self.last_route_path = route_path
            self.log("   - Gerado: route_result.png")

            # 6) Report
            report_path = os.path.join(run_dir, "report.txt")
            self.last_report_path = report_path

            report_lines = []
            report_lines.append("RELATÓRIO - Sabor Express (Rota Inteligente)\n\n")
            report_lines.append(f"Run: run_{ts}\n")
            report_lines.append(f"Pedidos carregados: {n_pedidos}\n")
            report_lines.append(f"Regra de pico: >= {PICO_MIN_PEDIDOS} ativa clustering\n\n")
            report_lines.append(f"Rota escolhida na interface: {start} -> {goal}\n\n")
            report_lines.append(f"BFS: caminho={p_bfs} | tempo_min={cost_bfs} | expandidos={ex_bfs} | ms={ms_bfs:.2f}\n")
            report_lines.append(f"DFS: caminho={p_dfs} | tempo_min={cost_dfs} | expandidos={ex_dfs} | ms={ms_dfs:.2f}\n")
            report_lines.append(f"A*:  caminho={p_astar} | tempo_min={cost_astar} | expandidos={ex_astar} | ms={ms_astar:.2f}\n")

            with open(report_path, "w", encoding="utf-8") as f:
                f.writelines(report_lines)

            # 7) Atualiza tabela (A)
            bfs = {"tempo": cost_bfs, "nos": ex_bfs, "ms": ms_bfs}
            dfs = {"tempo": cost_dfs, "nos": ex_dfs, "ms": ms_dfs}
            ast = {"tempo": cost_astar, "nos": ex_astar, "ms": ms_astar}
            self._set_table(bfs, dfs, ast)

            # 8) Preview (C)
            self._load_preview(graph_path, "graph")
            self._load_preview(route_path, "route")
            if self.last_clusters_path:
                self._load_preview(self.last_clusters_path, "clusters")
                self.preview_info.config(text=f"PICO ativado: clusters gerados ✅ (run_{ts})")
            else:
                self.canvas_clusters.config(image="")
                self._img_clusters = None
                self.preview_info.config(text=f"Modo NORMAL: sem clustering (run_{ts})")

            # final
            self.log("\n✅ Finalizado.")
            self.log(f"Arquivos do run em: {run_dir}")
            self.set_status("finalizado ✅")
            messagebox.showinfo("Pronto", f"Execução finalizada!\n\nPasta do run:\n{run_dir}")

        except Exception as e:
            self.set_status("erro ❌")
            messagebox.showerror("Erro", str(e))
        finally:
            self.set_running(False)

if __name__ == "__main__":
    app = App()
    app.mainloop()
