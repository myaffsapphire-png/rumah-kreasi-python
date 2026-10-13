import os, sqlite3, secrets, re
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "CHANGE-ME-before-deploy-" + secrets.token_hex(16))
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
DB = os.environ.get("DATABASE_PATH", "rumahkreasi.db")
ALLOWED = {"png", "jpg", "jpeg", "webp", "gif"}
CATEGORIES = {
 "KIDS COLLECTION": ["WORKSHEET","PNG POSTER ❗","NOTEBOOK","MAPEL","LABEL NAMA","GANCI FREE CETAK FOTO","FC Transportasi","FC Profesi","FC Matematika","FC Hijaiyah","FC Hewan","FC Angka 1–10","FC Alphabet A–Z","Buku Mewarnai","Buku Cerita Anak (PROMO)","Bookmark/ penanda buku","BAG CHARM","17 Agustus ❗"],
 "GIFT & SOUVENIR": ["TUMBLER BOUQUET","STRAP HANDPHONE","POLAROID","KAWAT BULU"]
}
DEFAULT_SETTINGS = {
 "shop_name":"Rumah Kreasi", "tagline":"Hadiah kecil, kesan yang berarti.", "hero_title":"Kreasi kecil, cerita istimewa.",
 "hero_subtitle":"Temukan koleksi anak, hadiah personal, dan souvenir dari Rumah Kreasi.",
 "hero_image":"", "logo_image":"", "shopee_url":"", "lynk_url":"https://lynk.id/rumahkreasi060224_"
}
def db():
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    return con
def init_db():
    con=db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'customer');
    CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL, collection TEXT NOT NULL, description TEXT DEFAULT '', image TEXT DEFAULT '', featured INTEGER DEFAULT 0, active INTEGER DEFAULT 1, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, sender TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL, seen INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    """)
    for k,v in DEFAULT_SETTINGS.items():
        con.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",(k,v))
    con.commit()
    # First admin is created from environment variables, never from a public registration form.
    email=os.environ.get("ADMIN_EMAIL","admin@rumahkreasi.local").strip().lower()
    password=os.environ.get("ADMIN_PASSWORD","")
    row=con.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone()
    if not row and password:
        con.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,'admin')",("Admin Rumah Kreasi",email,generate_password_hash(password)))
        con.commit()
    con.close()
init_db()
def settings():
    con=db(); values={r["key"]:r["value"] for r in con.execute("SELECT key,value FROM settings")}; con.close()
    return {**DEFAULT_SETTINGS,**values}
@app.context_processor
def inject():
    return {"site":settings(),"current_user":session.get("user"),"categories":CATEGORIES}
def login_required(fn):
    @wraps(fn)
    def wrapper(*a,**kw):
        if not session.get("user"): return redirect(url_for("login", next=request.path))
        return fn(*a,**kw)
    return wrapper
def admin_required(fn):
    @wraps(fn)
    def wrapper(*a,**kw):
        if not session.get("user"): return redirect(url_for("login", next=request.path))
        if session["user"].get("role")!="admin": abort(403)
        return fn(*a,**kw)
    return wrapper
def save_upload(field):
    f=request.files.get(field)
    if not f or not f.filename: return None
    name=secure_filename(f.filename)
    if "." not in name or name.rsplit(".",1)[1].lower() not in ALLOWED: raise ValueError("Format foto harus PNG, JPG, JPEG, WEBP, atau GIF.")
    os.makedirs(app.config["UPLOAD_FOLDER"],exist_ok=True)
    name=secrets.token_hex(8)+"_"+name
    f.save(os.path.join(app.config["UPLOAD_FOLDER"],name))
    return "uploads/"+name
def time_now(): return datetime.now().strftime("%Y-%m-%d %H:%M")
@app.get("/")
def home():
    con=db()
    featured=con.execute("SELECT * FROM products WHERE active=1 AND featured=1 ORDER BY id DESC LIMIT 6").fetchall()
    con.close()
    return render_template("home.html",featured=featured)
@app.get("/katalog")
def catalog():
    collection=request.args.get("collection","")
    category=request.args.get("category","")
    q=request.args.get("q","").strip()
    con=db(); sql="SELECT * FROM products WHERE active=1"; args=[]
    if collection in CATEGORIES: sql+=" AND collection=?"; args.append(collection)
    if category: sql+=" AND category=?"; args.append(category)
    if q: sql+=" AND (name LIKE ? OR description LIKE ?)"; args.extend([f"%{q}%",f"%{q}%"])
    products=con.execute(sql+" ORDER BY featured DESC,id DESC",args).fetchall(); con.close()
    return render_template("catalog.html",products=products,selected_collection=collection,selected_category=category,q=q)
@app.get("/produk/<int:pid>")
def product_detail(pid):
    con=db(); p=con.execute("SELECT * FROM products WHERE id=? AND active=1",(pid,)).fetchone(); con.close()
    if not p: abort(404)
    return render_template("product.html",p=p)
@app.route("/daftar",methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form.get("name","").strip(); email=request.form.get("email","").strip().lower(); pw=request.form.get("password","")
        if not name or not email or len(pw)<8:
            flash("Lengkapi data. Kata sandi minimal 8 karakter.","error")
        else:
            con=db()
            try:
                con.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,'customer')",(name,email,generate_password_hash(pw))); con.commit()
                flash("Akun berhasil dibuat. Silakan masuk.","success"); return redirect(url_for("login"))
            except sqlite3.IntegrityError: flash("Email sudah terdaftar.","error")
            finally: con.close()
    return render_template("auth.html",mode="register")
@app.route("/masuk",methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower(); pw=request.form.get("password","")
        con=db(); u=con.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone(); con.close()
        if u and check_password_hash(u["password"],pw):
            session.clear(); session["user"]={"id":u["id"],"name":u["name"],"email":u["email"],"role":u["role"]}
            return redirect(request.args.get("next") or (url_for("admin") if u["role"]=="admin" else url_for("chat")))
        flash("Email atau kata sandi tidak sesuai.","error")
    return render_template("auth.html",mode="login")
@app.get("/keluar")
def logout(): session.clear(); return redirect(url_for("home"))
@app.get("/chat")
@login_required
def chat():
    return render_template("chat.html")
@app.get("/api/messages")
@login_required
def api_messages():
    uid=session["user"]["id"]; is_admin=session["user"]["role"]=="admin"
    con=db()
    if is_admin:
        user_id=request.args.get("user_id",type=int)
        if not user_id:
            con.close(); return jsonify({"messages":[]})
        rows=con.execute("SELECT m.*,u.name AS customer_name FROM messages m JOIN users u ON u.id=m.user_id WHERE m.user_id=? ORDER BY m.id",(user_id,)).fetchall()
        con.execute("UPDATE messages SET seen=1 WHERE user_id=? AND sender='customer'",(user_id,))
    else:
        rows=con.execute("SELECT * FROM messages WHERE user_id=? ORDER BY id",(uid,)).fetchall()
        con.execute("UPDATE messages SET seen=1 WHERE user_id=? AND sender='admin'",(uid,))
    con.commit(); con.close()
    return jsonify({"messages":[dict(r) for r in rows]})
@app.post("/api/messages")
@login_required
def send_message():
    body=request.json.get("body","").strip() if request.is_json else request.form.get("body","").strip()
    is_admin=session["user"]["role"]=="admin"
    user_id=(request.json.get("user_id") if request.is_json else request.form.get("user_id",type=int)) if is_admin else session["user"]["id"]
    if not body or len(body)>2000: return jsonify({"error":"Pesan kosong atau terlalu panjang."}),400
    con=db()
    if is_admin:
        exists=con.execute("SELECT id FROM users WHERE id=? AND role='customer'",(user_id,)).fetchone()
        if not exists: con.close(); return jsonify({"error":"Pelanggan tidak ditemukan."}),404
    con.execute("INSERT INTO messages(user_id,sender,body,created_at) VALUES(?,?,?,?)",(user_id,"admin" if is_admin else "customer",body,time_now()))
    con.commit(); con.close(); return jsonify({"ok":True})
@app.get("/admin")
@admin_required
def admin():
    con=db()
    products=con.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    customers=con.execute("SELECT u.id,u.name,u.email,COUNT(m.id) AS unread FROM users u LEFT JOIN messages m ON m.user_id=u.id AND m.sender='customer' AND m.seen=0 WHERE u.role='customer' GROUP BY u.id ORDER BY unread DESC,u.name").fetchall()
    unread=con.execute("SELECT COUNT(*) AS n FROM messages WHERE sender='customer' AND seen=0").fetchone()["n"]
    con.close()
    return render_template("admin.html",products=products,customers=customers,unread=unread)
@app.post("/admin/product")
@admin_required
def add_product():
    name=request.form.get("name","").strip(); collection=request.form.get("collection",""); category=request.form.get("category","")
    if not name or collection not in CATEGORIES or category not in CATEGORIES[collection]:
        flash("Nama produk, koleksi, dan kategori harus diisi dengan benar.","error"); return redirect(url_for("admin"))
    try: img=save_upload("image") or ""
    except ValueError as e: flash(str(e),"error"); return redirect(url_for("admin"))
    con=db(); con.execute("INSERT INTO products(name,category,collection,description,image,featured,created_at) VALUES(?,?,?,?,?,?,?)",(name,category,collection,request.form.get("description","").strip(),img,1 if request.form.get("featured") else 0,time_now())); con.commit(); con.close()
    flash("Produk berhasil ditambahkan.","success"); return redirect(url_for("admin"))
@app.post("/admin/product/<int:pid>/delete")
@admin_required
def delete_product(pid):
    con=db(); con.execute("DELETE FROM products WHERE id=?",(pid,)); con.commit(); con.close(); flash("Produk dihapus.","success"); return redirect(url_for("admin"))
@app.post("/admin/product/<int:pid>/feature")
@admin_required
def feature_product(pid):
    con=db(); con.execute("UPDATE products SET featured=CASE WHEN featured=1 THEN 0 ELSE 1 END WHERE id=?",(pid,)); con.commit(); con.close(); return redirect(url_for("admin"))
@app.post("/admin/settings")
@admin_required
def update_settings():
    updates={k:request.form.get(k,"").strip() for k in ["shop_name","tagline","hero_title","hero_subtitle","shopee_url","lynk_url"]}
    try:
        hero=save_upload("hero_image"); logo=save_upload("logo_image")
    except ValueError as e: flash(str(e),"error"); return redirect(url_for("admin"))
    if hero: updates["hero_image"]=hero
    if logo: updates["logo_image"]=logo
    con=db()
    for k,v in updates.items(): con.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(k,v))
    con.commit(); con.close(); flash("Pengaturan website berhasil disimpan.","success"); return redirect(url_for("admin"))
@app.get("/robots.txt")
def robots(): return "User-agent: *\nAllow: /\n",200,{"Content-Type":"text/plain"}
@app.errorhandler(403)
def forbidden(e): return render_template("message.html",title="Akses dibatasi",message="Halaman ini hanya bisa dibuka admin."),403
@app.errorhandler(404)
def missing(e): return render_template("message.html",title="Halaman tidak ditemukan",message="Halaman atau produk yang dicari tidak tersedia."),404
if __name__=="__main__":
    app.run(debug=False,host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
