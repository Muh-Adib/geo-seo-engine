#!/usr/bin/env python3
import os
import sys
import time
import signal
import socket
import argparse
import subprocess
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PID_FILE = BASE_DIR / ".server.pid"

def get_env_var(key: str, default: str = "") -> str:
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv(key, default)

DEFAULT_PORT = int(get_env_var("PORT", "28420"))
DEFAULT_HOST = get_env_var("HOST", "127.0.0.1")

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def get_running_pid() -> int | None:
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            # Check if process is still alive
            os.kill(pid, 0)
            return pid
        except (ValueError, OSError):
            PID_FILE.unlink(missing_ok=True)
    return None

def start_server(host: str, port: int, no_browser: bool, daemon: bool):
    print("=" * 65)
    print(" ⚡ UNICAM PROGRAMMATIC SEO & GEO ENGINE")
    print(f" 🌐 Target URL: http://{host}:{port}")
    print("=" * 65)

    running_pid = get_running_pid()
    if running_pid:
        print(f"⚠️  Server sudah berjalan dengan PID {running_pid}.")
        if not no_browser:
            webbrowser.open(f"http://{host}:{port}")
        return

    if is_port_in_use(port, host):
        print(f"⚠️  Port {port} sudah digunakan oleh proses lain. Membuka browser...")
        if not no_browser:
            webbrowser.open(f"http://{host}:{port}")
        return

    # Check venv python
    venv_py = BASE_DIR / ".venv/bin/python"
    py_exec = str(venv_py) if venv_py.exists() else sys.executable

    cmd = [
        py_exec, "-m", "uvicorn", "web.app:app",
        "--host", host,
        "--port", str(port),
        "--app-dir", str(BASE_DIR)
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)
    env["PORT"] = str(port)
    env["HOST"] = host

    if daemon:
        log_file = open(BASE_DIR / "server.log", "a")
        proc = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL, stdout=log_file, stderr=log_file, start_new_session=True)
        PID_FILE.write_text(str(proc.pid))
        print(f"✅ Server berjalan di background (PID: {proc.pid})")
        print(f"📄 Log output: {BASE_DIR / 'server.log'}")
        if not no_browser:
            time.sleep(1.0)
            webbrowser.open(f"http://{host}:{port}")
    else:
        # Foreground
        if not no_browser:
            def open_tab():
                time.sleep(1.2)
                webbrowser.open(f"http://{host}:{port}")
            import threading
            threading.Thread(target=open_tab, daemon=True).start()

        try:
            proc = subprocess.Popen(cmd, env=env)
            PID_FILE.write_text(str(proc.pid))
            proc.wait()
        except KeyboardInterrupt:
            print("\n🛑 Menghentikan server...")
        finally:
            PID_FILE.unlink(missing_ok=True)
            print("✅ Server berhenti.")

def stop_server():
    print("🛑 Memeriksa proses SEO Engine...")
    pid = get_running_pid()
    if not pid:
        # Check via lsof if running on port
        port = DEFAULT_PORT
        try:
            out = subprocess.check_output(["lsof", "-ti", f":{port}"]).decode().strip()
            if out:
                pid = int(out.split()[0])
        except Exception:
            pass

    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
            # Verify killed
            try:
                os.kill(pid, 0)
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
            PID_FILE.unlink(missing_ok=True)
            print(f"✅ Sesi server berhasil dihentikan (PID {pid}).")
        except ProcessLookupError:
            PID_FILE.unlink(missing_ok=True)
            print("ℹ️  Proses sudah tidak aktif.")
        except Exception as e:
            print(f"❌ Gagal menghentikan server: {e}")
    else:
        print("ℹ️  Tidak ada server SEO Engine yang sedang berjalan.")

def show_status():
    pid = get_running_pid()
    port = DEFAULT_PORT
    in_use = is_port_in_use(port)
    
    print("=" * 50)
    print(" ⚡ STATUS SEO ENGINE")
    print("=" * 50)
    print(f" Port Default: {port}")
    print(f" Status Port : {'🟢 AKTIF (Merespons)' if in_use else '⚪ Tidak Aktif'}")
    print(f" Process PID : {pid if pid else 'Tidak ada'}")
    
    # Check Gemini accounts
    try:
        from core.gemini_auth import GeminiAuthManager
        mgr = GeminiAuthManager()
        summary = mgr.get_accounts_summary()
        print(f" Antigravity : {'🟢 Terdeteksi di Mac' if summary.get('has_local_antigravity') else '⚪ Belum terdeteksi'}")
        print(f" Akun Gemini : {summary.get('accounts_count', 0)} akun terhubung")
        for acc in summary.get("accounts", []):
            print(f"   - {acc.get('email')} [{acc.get('source')}]")
    except Exception as e:
        print(f" Gemini Auth : {e}")

    # Check Database Brands
    try:
        from db.session import SessionLocal
        from db.models import Brand, Article
        db = SessionLocal()
        brands_count = db.query(Brand).count()
        articles_count = db.query(Article).count()
        print(f" Database    : {brands_count} Brand, {articles_count} Artikel tersimpan")
        db.close()
    except Exception as e:
        print(f" Database    : {e}")

    # Check 9router & Active Model
    try:
        from core.router_client import LLMRouterClient
        rc = LLMRouterClient()
        r_health = rc.check_health()
        print(f" 9router (20128): {'🟢 ONLINE (' + str(r_health.get('models_count', 0)) + ' models)' if r_health.get('online') else '⚪ Offline'}")
        print(f" Model Aktif : {rc.config.get('selected_model')}")
    except Exception as e:
        print(f" Router      : {e}")
    print("=" * 50)

def show_accounts(sync_antigravity: bool = False):
    from core.gemini_auth import GeminiAuthManager
    mgr = GeminiAuthManager()
    if sync_antigravity:
        acc = mgr.auto_connect_antigravity()
        if acc:
            print(f"✅ Berhasil sinkronisasi sesi Antigravity: {acc.get('email')}")
        else:
            print("❌ Sesi Antigravity tidak ditemukan di ~/.gemini/")
    
    summary = mgr.get_accounts_summary()
    print(f"Total Akun Terhubung: {summary.get('accounts_count', 0)}")
    for idx, acc in enumerate(summary.get("accounts", [])):
        curr = " [AKTIF]" if acc.get("is_current") else ""
        print(f"[{idx+1}] {acc.get('email')} - {acc.get('source')}{curr}")

def cli_generate(brand_id: str, service_id: str, region: str, city: str, publish: bool):
    import mcp.server as s
    print(f"⏳ Menghasilkan artikel GEO untuk {brand_id} ({city}, {region})...")
    if publish:
        res = s.tool_publish_to_site(brand_id, service_id, region, city, status="publish")
        if res.get("success"):
            print("🎉 ARTIKEL BERHASIL DITERBITKAN KE WORDPRESS!")
            print(f"   Judul: {res.get('title')}")
            print(f"   URL  : {res.get('url')}")
            print(f"   Tag  : {res.get('tags_count')} tags terpasang")
        else:
            print(f"❌ Gagal menerbitkan: {res.get('error')}")
    else:
        res = s.tool_preview_seo_article(brand_id, service_id, region, city)
        if res.get("success"):
            print("✅ PREVIEW ARTIKEL 12-BLOK BERHASIL DIBUAT!")
            print(f"   Judul: {res.get('title')}")
            print(f"   Slug : {res.get('slug')}")
            print(f"   Tags : {res.get('tags_count')} tags (siap untuk WP taxonomy)")
            print(f"   FAQs : {res.get('faq_items_count')} Q&A terstruktur")
        else:
            print(f"❌ Gagal: {res.get('error')}")

def cli_import_sheet(target: str):
    import mcp.server as s
    print(f"📥 Mengimpor bank data dari: {target} ...")
    res = s.tool_import_sheet_data(target)
    if res.get("success"):
        print("✅ BANK DATA BERHASIL DISINKRONKAN!")
        print(f"   Baris diproses  : {res.get('rows_processed')}")
        print(f"   Brand diupdate  : {res.get('brands_synced')}")
        print(f"   Layanan diupdate: {res.get('services_synced')}")
        print(f"   Lokasi diupdate : {res.get('locations_synced')}")
    else:
        print(f"❌ Gagal impor: {res.get('error')}")

def cli_models(fetch: bool = False, set_model: str = "", filter_q: str = ""):
    from core.router_client import LLMRouterClient
    rc = LLMRouterClient()
    
    if set_model:
        rc.config["selected_model"] = set_model
        rc.save_config()
        print(f"✅ Model aktif berhasil diubah menjadi: '{set_model}'")
        return

    print("=" * 60)
    print(" 🧠 DAFTAR MODEL DARI 9ROUTER (DYNAMIC FETCH)")
    print("=" * 60)
    print(f" Endpoint Router: {rc.config.get('base_url')}")
    print(f" Model Aktif    : {rc.config.get('selected_model')}")
    print("-" * 60)

    res = rc.fetch_models()
    if res.get("success"):
        models = res.get("models", [])
        if filter_q:
            models = [m for m in models if filter_q.lower() in m["id"].lower()]
        print(f" Total Model: {len(models)} model ditemukan")
        print()
        for idx, m in enumerate(models[:50], 1):
            is_active = " [AKTIF]" if m["id"] == rc.config.get("selected_model") else ""
            print(f"  {idx:2d}. {m['id']:<35} ({m.get('owned_by', 'router')}){is_active}")
        if len(models) > 50:
            print(f"  ... dan {len(models) - 50} model lainnya. Gunakan --filter untuk mempersempit.")
    else:
        print(f"❌ Gagal mengambil model: {res.get('error')}")
    print("=" * 60)

def cli_generate_image(prompt: str, ratio: str = "16:9", style: str = "photorealistic", brand: str = "GEO Studio"):
    from generators.gemini_generator import GeminiMultiAccountEngine
    engine = GeminiMultiAccountEngine()
    print("=" * 60)
    print(" 🎨 STUDIO GENERATOR GAMBAR AI")
    print("=" * 60)
    print(f" Prompt : {prompt}")
    print(f" Rasio  : {ratio}")
    print(f" Style  : {style}")
    print(" Sedang merender visual...")
    res = engine.generate_custom_image(prompt=prompt, aspect_ratio=ratio, style=style, brand_name=brand)
    if res.get("success"):
        print("✅ VISUAL BERHASIL DIGENERATE!")
        print(f"   File   : {res.get('file_path')}")
        print(f"   URL    : {res.get('url')}")
        print(f"   Ukuran : {res.get('width')}x{res.get('height')}")
    else:
        print(f"❌ Gagal: {res.get('error')}")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(
        description="Unicam Programmatic SEO & GEO Engine CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh Penggunaan:
  seo-engine start                     Jalankan server & buka Web Dashboard
  seo-engine start --port 28420 -d     Jalankan di background (daemon)
  seo-engine stop                      Hentikan sesi server
  seo-engine status                    Lihat status proses, port & akun Gemini
  seo-engine accounts --sync           Sinkronkan sesi login Antigravity
  seo-engine import-sheet <URL/CSV>    Impor bank data dari Google Sheets
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Perintah yang tersedia")

    # Command: start
    start_p = subparsers.add_parser("start", help="Menghidupkan server & Web Dashboard")
    start_p.add_argument("-p", "--port", type=int, default=DEFAULT_PORT, help=f"Port server (default: {DEFAULT_PORT})")
    start_p.add_argument("-H", "--host", default=DEFAULT_HOST, help=f"Host (default: {DEFAULT_HOST})")
    start_p.add_argument("-n", "--no-browser", action="store_true", help="Jangan buka browser otomatis")
    start_p.add_argument("-d", "--daemon", action="store_true", help="Jalankan di background (daemon)")

    # Command: stop
    subparsers.add_parser("stop", help="Mematikan sesi server yang sedang berjalan")

    # Command: restart
    restart_p = subparsers.add_parser("restart", help="Restart server")
    restart_p.add_argument("-p", "--port", type=int, default=DEFAULT_PORT)

    # Command: status
    subparsers.add_parser("status", help="Lihat status server dan akun Gemini")

    # Command: accounts
    acc_p = subparsers.add_parser("accounts", help="Kelola akun Google Gemini")
    acc_p.add_argument("--sync", action="store_true", help="Sinkronkan sesi Antigravity Desktop")

    # Command: generate
    gen_p = subparsers.add_parser("generate", help="Generate artikel via CLI")
    gen_p.add_argument("--brand", required=True, help="ID Brand (contoh: unimasi)")
    gen_p.add_argument("--service", required=True, help="ID Service (contoh: unimasi-safety)")
    gen_p.add_argument("--region", required=True, help="Wilayah (contoh: Australia)")
    gen_p.add_argument("--city", default="", help="Kota target (contoh: Sydney)")
    gen_p.add_argument("--publish", action="store_true", help="Terbitkan langsung ke WordPress")

    # Command: import-sheet
    sheet_p = subparsers.add_parser("import-sheet", help="Impor bank data dari Google Sheets / CSV")
    sheet_p.add_argument("target", help="URL Google Sheet atau path file CSV")

    # Command: models (9router)
    model_p = subparsers.add_parser("models", help="Daftar & kelola model live dari 9router")
    model_p.add_argument("-f", "--filter", default="", help="Filter nama model (contoh: alpha, claude, sonnet)")
    model_p.add_argument("--set", dest="set_model", default="", help="Ganti model aktif (contoh: ox-alpha)")

    # Command: generate-image
    img_p = subparsers.add_parser("generate-image", help="Generate gambar/visual AI via CLI")
    img_p.add_argument("-p", "--prompt", required=True, help="Deskripsi visual / prompt")
    img_p.add_argument("-r", "--ratio", default="16:9", choices=["16:9", "1:1", "9:16"], help="Aspek rasio")
    img_p.add_argument("-s", "--style", default="photorealistic", choices=["photorealistic", "cyberpunk", "minimalist"], help="Gaya visual")
    img_p.add_argument("-b", "--brand", default="GEO Studio", help="Nama brand watermark")

    args = parser.parse_args()

    if not args.command or args.command == "start":
        port = getattr(args, "port", DEFAULT_PORT)
        host = getattr(args, "host", DEFAULT_HOST)
        no_b = getattr(args, "no_browser", False)
        daemon = getattr(args, "daemon", False)
        start_server(host, port, no_b, daemon)
    elif args.command == "stop":
        stop_server()
    elif args.command == "restart":
        stop_server()
        time.sleep(1)
        start_server(DEFAULT_HOST, getattr(args, "port", DEFAULT_PORT), False, False)
    elif args.command == "status":
        show_status()
    elif args.command == "accounts":
        show_accounts(getattr(args, "sync", False))
    elif args.command == "models":
        cli_models(fetch=True, set_model=getattr(args, "set_model", ""), filter_q=getattr(args, "filter", ""))
    elif args.command == "generate-image":
        cli_generate_image(prompt=args.prompt, ratio=args.ratio, style=args.style, brand=args.brand)
    elif args.command == "generate":
        cli_generate(args.brand, args.service, args.region, args.city, args.publish)
    elif args.command == "import-sheet":
        cli_import_sheet(args.target)

if __name__ == "__main__":
    main()
