import os
import sys
import subprocess
import time
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox

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
    """Monta caminhos absolutos dentro do projeto."""
    return os.path.join(BASE_DIR, *parts)

def open_folder(path: str):
    """Abre a pasta no explorador do Windows / macOS / Linux."""
    path = os.path.abspath(path)
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
    except Exception as e:
        messagebox.showerror("Erro", f"Não consegui abrir a pasta:\n{e}")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rota Inteligente - Sabor Express (IA)")
        self.geometry("920x600")

        # Guarda a pasta do último run (pra abrir no botão)
        self.last_run_dir = None

        # --- Topo: seleções
        frame_top = ttk.Frame(self, padding=10)
        frame_top.pack(fill="x")

        ttk.Label(frame_top, text="Origem:").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.cmb_start = ttk.Combobox(frame_top, state="readonly", width=25)
        self.cmb_start.grid(row=0, column=1, sticky="w", padx=(0, 18))

        ttk.Label(frame_top, text="Destino:").grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.cmb_goal = ttk.Combobox(frame_top, state="readonly", width=25)
        self.cmb_goal.grid(row=0, column=3, sticky="w", padx=(0, 18))

        self.btn_run = ttk.Button(frame_top, text="Rodar Otimização", command=self.run_all)
        self.btn_run.grid(row=0, column=4, sticky="w")

        self.btn_open = ttk.Button(frame_top, text="Abrir outputs", command=self.open_outputs)
        self.btn_open.grid(row=0, column=5, sticky="w", padx=(10, 0))

        # --- Meio: status
        frame_status = ttk.Frame(self, padding=(10, 0))
        frame_status.pack(fill="x")

        self.lbl_status = ttk.Label(frame_status, text="Status: pronto.")
        self.lbl_status.pack(anchor="w")

        # --- Área de log
        frame_log = ttk.Frame(self, padding=10)
        frame_log.pack(fill="both", expand=True)

        ttk.Label(frame_log, text="Resultados / Log:").pack(anchor="w")

        self.txt = tk.Text(frame_log, height=22, wrap="word")
        self.txt.pack(fill="both", expand=True)

        # --- Carrega nós pros dropdowns
        self.load_nodes()

    def open_outputs(self):
        # Se já rodou uma vez, abre a pasta do último run
        if self.last_run_dir and os.path.exists(self.last_run_dir):
            self.log(f"Abrindo pasta do último run: {self.last_run_dir}")
            open_folder(self.last_run_dir)
        else:
            # Senão abre a pasta outputs geral
            outputs_dir = p("outputs")
            self.log(f"Abrindo pasta outputs: {outputs_dir}")
            open_folder(outputs_dir)

    def log(self, msg: str):
        self.txt.insert("end", msg + "\n")
        self.txt.see("end")
        self.update_idletasks()

    def set_status(self, msg: str):
        self.lbl_status.config(text=f"Status: {msg}")
        self.update_idletasks()

    def load_nodes(self):
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

    def run_all(self):
        self.txt.delete("1.0", "end")
        self.set_status("executando...")

        try:
            start = self.cmb_start.get().strip()
            goal = self.cmb_goal.get().strip()

            if not start or not goal:
                messagebox.showwarning("Atenção", "Selecione origem e destino.")
                self.set_status("pronto.")
                return

            if start == goal:
                messagebox.showwarning("Atenção", "Origem e destino não podem ser iguais.")
                self.set_status("pronto.")
                return

            # Pasta do run (timestamp)
            ts = time.strftime("%Y%m%d_%H%M%S")
            run_dir = p("outputs", f"run_{ts}")
            os.makedirs(run_dir, exist_ok=True)
            self.last_run_dir = run_dir

            self.log(f"Run criado: {run_dir}")

            # Grafo
            self.log("1) Carregando grafo...")
            G = build_graph(p("data", "nodes.csv"), p("data", "edges.csv"))

            graph_path = os.path.join(run_dir, "graph.png")
            draw_graph(G, graph_path)
            self.log("   - Gerado: graph.png")

            # Pedidos
            self.log("2) Lendo pedidos...")
            deliveries_path = p("data", "deliveries.csv")
            self.log(f"   - Lendo arquivo: {deliveries_path}")

            if not os.path.exists(deliveries_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {deliveries_path}")

            # Se o arquivo tiver só espaços/linhas em branco, pandas pode dar EmptyDataError
            try:
                deliveries = pd.read_csv(deliveries_path)
            except pd.errors.EmptyDataError:
                raise ValueError(
                    "O arquivo data/deliveries.csv está sem colunas (vazio ou só com linhas em branco).\n"
                    "Abra data/deliveries.csv, cole o CSV com cabeçalho e pedidos, e salve (Ctrl+S)."
                )

            n_pedidos = len(deliveries)
            if n_pedidos == 0:
                raise ValueError("data/deliveries.csv não tem pedidos (0 linhas).")

            self.log(f"   - Pedidos: {n_pedidos}")

            # Regra de pico
            clustered_csv_path = os.path.join(run_dir, "deliveries_with_clusters.csv")
            clusters_img_path = os.path.join(run_dir, "clusters.png")

            if n_pedidos >= PICO_MIN_PEDIDOS:
                self.log(f"3) PICO: {n_pedidos} >= {PICO_MIN_PEDIDOS} -> K-Means (k={K_ENTREGADORES})")
                deliveries_clustered = kmeans_clusters(
                    deliveries_csv=deliveries_path,
                    k=K_ENTREGADORES,
                    out_csv=clustered_csv_path
                )
                draw_clusters(deliveries_clustered, clusters_img_path)
                self.log("   - Gerado: clusters.png")
            else:
                self.log(f"3) NORMAL: {n_pedidos} < {PICO_MIN_PEDIDOS} -> sem clustering")
                deliveries.to_csv(clustered_csv_path, index=False)
                self.log("   - Gerado: deliveries_with_clusters.csv (sem cluster)")

            # Comparação BFS / DFS / A*
            self.log("4) Calculando rotas (BFS / DFS / A*)...")

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

            # Imagem da rota (A*)
            route_path = os.path.join(run_dir, "route_result.png")
            draw_route(G, p_astar, route_path)
            self.log("   - Gerado: route_result.png")

            # Relatório
            report_path = os.path.join(run_dir, "report.txt")

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

            # Log final
            self.log("\n===== RESULTADOS =====")
            self.log(f"BFS: tempo_min={cost_bfs} | expandidos={ex_bfs} | ms={ms_bfs:.2f}")
            self.log(f"DFS: tempo_min={cost_dfs} | expandidos={ex_dfs} | ms={ms_dfs:.2f}")
            self.log(f"A*:  tempo_min={cost_astar} | expandidos={ex_astar} | ms={ms_astar:.2f}")
            self.log(f"Relatório: {report_path}")
            self.log(f"Arquivos deste run em: {run_dir}")

            self.set_status("finalizado ✅")
            messagebox.showinfo("Pronto", f"Execução finalizada!\n\nPasta do run:\n{run_dir}")

        except Exception as e:
            self.set_status("erro ❌")
            messagebox.showerror("Erro", str(e))

if __name__ == "__main__":
    app = App()
    app.mainloop()
