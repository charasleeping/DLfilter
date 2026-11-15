use crate::{api, assets, config::Config, engine::Engine, titles};
use anyhow::{Context, Result, bail, ensure};
use axum::{
    Json, Router,
    extract::{DefaultBodyLimit, Multipart, Request, State},
    http::{HeaderMap, StatusCode},
    middleware::{self, Next},
    response::{Html, IntoResponse, Response},
    routing::{get, post},
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::{
    fs,
    io::{BufRead, BufReader, Read, Write},
    path::{Path, PathBuf},
    process::{Command, Stdio},
    sync::{
        Arc, Mutex, RwLock,
        atomic::{AtomicBool, Ordering},
    },
};
use tower::ServiceExt;
const MANIFEST: &str =
    "https://github.com/charasleeping/DLfilter/releases/download/database/serving-catalogue.json";
const MAX_BYTES: u64 = 16 * 1024 * 1024 * 1024;
fn lock<T>(m: &Mutex<T>) -> std::sync::MutexGuard<'_, T> {
    m.lock().unwrap_or_else(|e| e.into_inner())
}
#[derive(Clone, Serialize, Default)]
pub struct Job {
    state: String,
    phase: String,
    done: u64,
    total: u64,
    added: u64,
    message: String,
}
pub struct Setup {
    cfg: Config,
    token: String,
    app: RwLock<Option<Arc<api::App>>>,
    install: Mutex<Job>,
    title_job: Mutex<Job>,
    cancel: AtomicBool,
    title_stop: AtomicBool,
    child: Mutex<Option<std::process::Child>>,
    preferences: Mutex<titles::Preferences>,
}
impl Setup {
    fn app(&self) -> Option<Arc<api::App>> {
        self.app.read().unwrap().clone()
    }
    fn pref_path(&self) -> PathBuf {
        self.cfg.cache.join("catalogue-settings.json")
    }
    fn update_install(&self, state: &str, phase: &str, message: &str) {
        let mut j = lock(&self.install);
        j.state = state.into();
        j.phase = phase.into();
        j.message = message.into();
    }
}
pub fn router(cfg: Config) -> (Router, Arc<Setup>) {
    let recovery = recover_install(&cfg);
    let token = format!("{:032x}", rand::random::<u128>());
    let saved_preferences = fs::read(cfg.cache.join("catalogue-settings.json"))
        .ok()
        .and_then(|b| serde_json::from_slice(&b).ok())
        .unwrap_or_default();
    let state = Arc::new(Setup {
        cfg,
        token,
        app: RwLock::new(None),
        install: Mutex::new(Job::default()),
        title_job: Mutex::new(Job::default()),
        cancel: AtomicBool::new(false),
        title_stop: AtomicBool::new(false),
        child: Mutex::new(None),
        preferences: Mutex::new(saved_preferences),
    });
    if let Err(e) = recovery {
        state.update_install("error", "recover", &e.to_string());
    }
    if state.cfg.database().exists() {
        state.update_install("running", "prepare", "");
        let s = state.clone();
        std::thread::spawn(move || load_engine(&s));
    }
    let router = Router::new()
        .route("/setup", get(page))
        .route("/api/setup/status", get(status))
        .route("/api/setup/download", post(download))
        .route(
            "/api/setup/import",
            post(import).layer(DefaultBodyLimit::max(MAX_BYTES as usize)),
        )
        .route("/api/setup/cancel", post(cancel))
        .route("/api/setup/titles", post(preferences))
        .route("/api/setup/titles/pause", post(pause_titles))
        .fallback(forward)
        .layer(DefaultBodyLimit::max(65536))
        .layer(middleware::from_fn_with_state(state.clone(), protect))
        .with_state(state.clone());
    (router, state)
}
pub fn shutdown(state: &Setup) {
    state.cancel.store(true, Ordering::SeqCst);
    stop_titles(state);
}
async fn protect(State(s): State<Arc<Setup>>, req: Request, next: Next) -> Response {
    if req.uri().path().starts_with("/api/setup/") {
        let host = req
            .headers()
            .get("host")
            .and_then(|h| h.to_str().ok())
            .unwrap_or("");
        let expected = format!("http://{host}");
        let origin = req.headers().get("origin").and_then(|h| h.to_str().ok());
        if origin.is_some_and(|o| o != expected)
            || req
                .headers()
                .get("sec-fetch-site")
                .is_some_and(|v| v == "cross-site")
        {
            return api::error(
                403,
                "origin",
                "Open settings from the running DLFilter window.",
            );
        }
        // Disallow DNS rebinding on the default local listener.
        if ["127.0.0.1", "localhost", "::1"].contains(&s.cfg.host.as_str())
            && ![
                format!("127.0.0.1:{}", s.cfg.port),
                format!("localhost:{}", s.cfg.port),
                format!("[::1]:{}", s.cfg.port),
            ]
            .contains(&host.to_owned())
        {
            return api::error(403, "host", "Invalid local host.");
        }
        if req.method() != axum::http::Method::GET
            && req
                .headers()
                .get("x-dlfilter-token")
                .and_then(|v| v.to_str().ok())
                != Some(s.token.as_str())
        {
            return api::error(403, "token", "Reload catalogue settings and try again.");
        }
    }
    next.run(req).await
}
async fn page() -> Html<&'static str> {
    Html(include_str!("../templates/setup.html"))
}
async fn status(State(s): State<Arc<Setup>>) -> Json<serde_json::Value> {
    Json(
        json!({"ready":s.app().is_some(),"token":s.token,"installation":lock(&s.install).clone(),"titles":lock(&s.title_job).clone(),"preferences":lock(&s.preferences).clone(),"destination":s.cfg.data,"source":std::env::var("DLFILTER_DB_MANIFEST_URL").unwrap_or(MANIFEST.into())}),
    )
}
async fn forward(State(s): State<Arc<Setup>>, req: Request) -> Response {
    if req.uri().path() == "/static/setup.js" {
        return (
            [("content-type", "text/javascript; charset=utf-8")],
            include_str!("../static/setup.js"),
        )
            .into_response();
    }
    if req.uri().path() == "/static/setup.css" {
        return (
            [("content-type", "text/css; charset=utf-8")],
            include_str!("../static/setup.css"),
        )
            .into_response();
    }
    if let Some(app) = s.app() {
        return api::router_shared(app).oneshot(req).await.unwrap();
    }
    if req.uri().path() == "/" {
        let target = if s.cfg.database().is_file() && lock(&s.install).state == "running" {
            "/setup?launch=1"
        } else {
            "/setup"
        };
        return axum::response::Redirect::temporary(target).into_response();
    }
    api::error(503, "setup_required", "Complete catalogue setup first.")
}
fn begin(s: &Setup) -> Result<()> {
    ensure!(
        s.app().is_none(),
        "A catalogue is already active. Stop DLFilter before replacing it."
    );
    let mut j = lock(&s.install);
    ensure!(j.state != "running", "An installation is already running.");
    *j = Job {
        state: "running".into(),
        phase: "download".into(),
        ..Job::default()
    };
    s.cancel.store(false, Ordering::SeqCst);
    Ok(())
}
fn load_engine(s: &Arc<Setup>) {
    match Engine::load(s.cfg.clone(), false) {
        Ok(engine) => {
            *s.app.write().unwrap() = Some(api::new_app(engine));
            s.update_install("complete", "ready", "");
            if lock(&s.preferences).enabled {
                start_titles(s.clone());
            }
        }
        Err(e) => s.update_install("error", "prepare", &format!("{e:#}")),
    }
}
fn cancelled(s: &Setup) -> Result<()> {
    ensure!(!s.cancel.load(Ordering::SeqCst), "Installation cancelled.");
    Ok(())
}
#[derive(Deserialize)]
struct Bundle {
    version: u32,
    url: String,
    sha256: String,
    size: u64,
}
async fn fetch_bundle(s: Arc<Setup>) -> Result<()> {
    let url = std::env::var("DLFILTER_DB_MANIFEST_URL").unwrap_or(MANIFEST.into());
    let client = reqwest::Client::builder()
        .connect_timeout(std::time::Duration::from_secs(15))
        .read_timeout(std::time::Duration::from_secs(60))
        .build()?;
    let mut response = client
        .get(url)
        .timeout(std::time::Duration::from_secs(30))
        .send()
        .await?
        .error_for_status()?;
    let mut metadata = Vec::new();
    while let Some(chunk) = response.chunk().await? {
        metadata.extend_from_slice(&chunk);
        ensure!(metadata.len() <= 65536, "Catalogue manifest too large");
    }
    let manifest: Bundle = serde_json::from_slice(&metadata)?;
    ensure!(
        manifest.version == 1
            && manifest.size > 0
            && manifest.size <= MAX_BYTES
            && manifest.sha256.len() == 64,
        "Invalid catalogue manifest"
    );
    ensure!(
        manifest.url.starts_with("https://")
            || std::env::var_os("DLFILTER_DB_MANIFEST_URL").is_some(),
        "Catalogue URL must use HTTPS"
    );
    cancelled(&s)?;
    let mut response = client.get(&manifest.url).send().await?.error_for_status()?;
    let mut file = tempfile::NamedTempFile::new()?;
    lock(&s.install).total = manifest.size;
    let mut total = 0;
    loop {
        cancelled(&s)?;
        tokio::select! {
            chunk=response.chunk()=>{
                let Some(chunk)=chunk? else {break;};
                total+=chunk.len() as u64;ensure!(total<=manifest.size,"Download exceeds declared size");
                file.write_all(&chunk)?;lock(&s.install).done=total;
            },
            _=tokio::time::sleep(std::time::Duration::from_millis(200))=>{}
        }
    }
    cancelled(&s)?;
    tokio::task::spawn_blocking(move || {
        ensure!(
            total == manifest.size && assets::file_digest(file.path())? == manifest.sha256,
            "Catalogue checksum mismatch. Retry the download."
        );
        install(&s, file.path())
    })
    .await??;
    Ok(())
}
async fn download(State(s): State<Arc<Setup>>) -> Response {
    if let Err(e) = begin(&s) {
        return api::error(409, "busy", &e.to_string());
    }
    tokio::spawn(async move {
        if let Err(e) = fetch_bundle(s.clone()).await {
            s.update_install(
                if s.cancel.load(Ordering::SeqCst) {
                    "cancelled"
                } else {
                    "error"
                },
                "download",
                &format!("{e:#}"),
            );
        }
    });
    (StatusCode::ACCEPTED, Json(json!({"state":"started"}))).into_response()
}
async fn import(
    State(s): State<Arc<Setup>>,
    headers: HeaderMap,
    mut multipart: Multipart,
) -> Response {
    let _ = headers;
    if let Err(e) = begin(&s) {
        return api::error(409, "busy", &e.to_string());
    }
    lock(&s.install).phase = "import".into();
    let result = async {
        let mut file = tempfile::NamedTempFile::new()?;
        let mut field = multipart
            .next_field()
            .await?
            .context("Choose a catalogue ZIP")?;
        let mut total = 0;
        while let Some(chunk) = field.chunk().await? {
            cancelled(&s)?;
            total += chunk.len() as u64;
            ensure!(total <= MAX_BYTES, "Archive too large");
            file.write_all(&chunk)?;
            lock(&s.install).done = total;
        }
        Ok::<_, anyhow::Error>(file)
    }
    .await;
    match result {
        Ok(file) => {
            std::thread::spawn(move || {
                if let Err(e) = install(&s, file.path()) {
                    s.update_install(
                        if s.cancel.load(Ordering::SeqCst) {
                            "cancelled"
                        } else {
                            "error"
                        },
                        "import",
                        &format!("{e:#}"),
                    );
                }
            });
            (StatusCode::ACCEPTED, Json(json!({"state":"started"}))).into_response()
        }
        Err(e) => {
            s.update_install(
                if s.cancel.load(Ordering::SeqCst) {
                    "cancelled"
                } else {
                    "error"
                },
                "import",
                &e.to_string(),
            );
            api::error(422, "import_failed", &e.to_string())
        }
    }
}
fn install(s: &Arc<Setup>, archive: &Path) -> Result<()> {
    s.update_install("running", "extract", "");
    let parent = s.cfg.data.parent().context("Invalid data directory")?;
    fs::create_dir_all(parent)
        .context("The app folder is not writable. Move the extracted app to a writable folder.")?;
    let staging = tempfile::tempdir_in(parent)?;
    let mut zip = zip::ZipArchive::new(fs::File::open(archive)?)?;
    let names = [
        "works.sqlite",
        "genre_table.json",
        "workformat.json",
        "genre_vectors.json",
        "genre_vectors.f32",
    ];
    let mut found = std::collections::HashSet::new();
    let mut expanded = 0u64;
    for i in 0..zip.len() {
        let mut entry = zip.by_index(i)?;
        let safe = entry.enclosed_name().context("Unsafe archive path")?;
        ensure!(
            entry.unix_mode().is_none_or(|m| m & 0o170000 != 0o120000),
            "Archive symlinks are not allowed"
        );
        let name = safe.file_name().and_then(|s| s.to_str()).unwrap_or("");
        if !names.contains(&name) || entry.is_dir() {
            continue;
        }
        ensure!(found.insert(name.to_owned()), "Duplicate catalogue file");
        expanded = expanded
            .checked_add(entry.size())
            .context("Archive too large")?;
        ensure!(expanded <= MAX_BYTES, "Expanded archive too large");
        ensure!(
            fs2::available_space(parent)? > entry.size() + 64 * 1024 * 1024,
            "Not enough free disk space"
        );
        let mut out = fs::File::create(staging.path().join(name))?;
        let mut buffer = [0u8; 65536];
        let expected = entry.size();
        let mut written = 0u64;
        loop {
            cancelled(s)?;
            let n = entry.read(&mut buffer)?;
            if n == 0 {
                break;
            }
            written += n as u64;
            ensure!(
                written <= expected,
                "Archive size does not match its directory"
            );
            out.write_all(&buffer[..n])?;
        }
        out.sync_all()?;
    }
    ensure!(
        names.iter().all(|n| found.contains(*n)),
        "This ZIP lacks portable serving files. Choose a serving catalogue ZIP; legacy bundles require conversion (see docs/installation.md)."
    );
    let mut cfg = s.cfg.clone();
    cfg.data = staging.path().to_owned();
    let db = crate::engine::readonly(&cfg.database())?;
    assets::required_database(&db)?;
    let integrity: String = db.query_row("PRAGMA quick_check", [], |r| r.get(0))?;
    ensure!(integrity == "ok", "Invalid SQLite catalogue");
    drop(db);
    assets::vectors(&cfg.data)?;
    assets::json(&cfg.data.join("genre_table.json"))?;
    assets::json(&cfg.data.join("workformat.json"))?;
    cancelled(s)?;
    let backup = s.cfg.data.with_file_name(format!(
        "{}.before-setup",
        s.cfg.data.file_name().unwrap_or_default().to_string_lossy()
    ));
    ensure!(
        !backup.exists(),
        "A setup backup already exists at {}. Keep or move it before retrying.",
        backup.display()
    );
    let existed = s.cfg.data.exists();
    // Write-ahead marker makes an interrupted two-rename promotion recoverable at next launch.
    let marker = parent.join(".dlfilter-install.json");
    let stage = staging.keep();
    assets::atomic(
        &marker,
        &serde_json::to_vec(&json!({"stage":stage,"destination":s.cfg.data,"backup":backup}))?,
    )?;
    if existed {
        fs::rename(&s.cfg.data, &backup)?;
    }
    if let Err(e) = fs::rename(&stage, &s.cfg.data) {
        if existed {
            let _ = fs::rename(&backup, &s.cfg.data);
        }
        return Err(e.into());
    }
    fs::remove_file(marker)?;
    s.update_install("running", "prepare", "");
    load_engine(s);
    Ok(())
}
async fn cancel(State(s): State<Arc<Setup>>) -> Json<serde_json::Value> {
    s.cancel.store(true, Ordering::SeqCst);
    Json(json!({"state":"cancelling"}))
}
async fn preferences(
    State(s): State<Arc<Setup>>,
    Json(mut p): Json<titles::Preferences>,
) -> Response {
    p.languages.sort();
    p.languages.dedup();
    if p.languages
        .iter()
        .any(|l| !["ENG", "CHI_HANT", "CHI_HANS"].contains(&l.as_str()))
    {
        return api::error(422, "language", "Choose a supported title language.");
    }
    if let Err(e) = fs::create_dir_all(&s.cfg.cache)
        .map_err(anyhow::Error::from)
        .and_then(|_| titles::save_preferences(&s.pref_path(), &p))
    {
        return api::error(500, "save_failed", &e.to_string());
    }
    *lock(&s.preferences) = p.clone();
    if p.enabled {
        start_titles(s.clone());
    } else {
        stop_titles(&s);
    }
    Json(json!({"state":"saved"})).into_response()
}
fn stop_titles(s: &Setup) {
    s.title_stop.store(true, Ordering::SeqCst);
    if let Some(child) = lock(&s.child).as_mut() {
        let _ = child.kill();
    }
}
async fn pause_titles(State(s): State<Arc<Setup>>) -> Response {
    let mut p = lock(&s.preferences).clone();
    p.enabled = false;
    if let Err(e) = titles::save_preferences(&s.pref_path(), &p) {
        return api::error(500, "save_failed", &e.to_string());
    }
    *lock(&s.preferences) = p;
    stop_titles(&s);
    Json(json!({"state":"paused"})).into_response()
}
fn start_titles(s: Arc<Setup>) {
    if s.app().is_none() {
        return;
    }
    {
        let mut j = lock(&s.title_job);
        if j.state == "running" {
            return;
        }
        *j = Job {
            state: "running".into(),
            phase: "titles".into(),
            ..Job::default()
        };
    }
    s.title_stop.store(false, Ordering::SeqCst);
    std::thread::spawn(move || {
        let result = collect_titles(&s);
        let mut j = lock(&s.title_job);
        j.state = if s.title_stop.load(Ordering::SeqCst) {
            "paused"
        } else if result.is_ok() {
            "complete"
        } else {
            "error"
        }
        .into();
        if let Err(e) = result
            && j.state == "error"
        {
            j.message = format!("{e:#}");
        }
    });
}
fn collect_titles(s: &Arc<Setup>) -> Result<()> {
    let app = s.app().context("Catalogue is not ready")?;
    let prefs = lock(&s.preferences).clone();
    if prefs.languages.is_empty() {
        return Ok(());
    }
    let db = ConnectionAlias::open(s.cfg.cache.join("titles.sqlite"))?;
    titles::schema(&db)?;
    let source = crate::engine::readonly(&s.cfg.database())?;
    let cols: Vec<String> = source
        .prepare("PRAGMA table_info(maniax)")?
        .query_map([], |r| r.get(1))?
        .collect::<rusqlite::Result<_>>()?;
    let column = |lang: &str| {
        if cols.contains(&format!("name_{lang}")) {
            format!("[name_{lang}]")
        } else {
            "NULL".into()
        }
    };
    let sql = format!(
        "SELECT [index],name,siteId,options,{},{},{} FROM maniax ORDER BY registDate DESC,[index]",
        column("ENG"),
        column("CHI_HANT"),
        column("CHI_HANS")
    );
    let mut tasks = Vec::new();
    for row in source.prepare(&sql)?.query_map([], |r| {
        Ok((
            r.get::<_, String>(0)?,
            r.get::<_, String>(1)?,
            r.get::<_, Option<String>>(2)?,
            r.get::<_, Option<String>>(3)?,
            [
                r.get::<_, Option<String>>(4)?,
                r.get::<_, Option<String>>(5)?,
                r.get::<_, Option<String>>(6)?,
            ],
        ))
    })? {
        let (id, original, site, options, existing) = row?;
        let options = options.unwrap_or_default();
        if !options.split('#').any(|v| v == "JPN") {
            continue;
        }
        for (k, language) in ["ENG", "CHI_HANT", "CHI_HANS"].iter().enumerate() {
            if !prefs.languages.iter().any(|l| l == language)
                || !options.split('#').any(|v| v == *language)
                || existing[k].as_ref().is_some_and(|s| !s.is_empty())
            {
                continue;
            }
            let done: bool = db.query_row(
                "SELECT EXISTS(SELECT 1 FROM collected_titles WHERE id=? AND language=?)",
                rusqlite::params![id, language],
                |r| r.get(0),
            )?;
            if !done {
                let fallback = if id.starts_with("BJ") {
                    "books"
                } else if id.starts_with("VJ") {
                    "pro"
                } else {
                    "maniax"
                };
                tasks.push(json!({"id":id,"original":original,"source":site.as_deref().unwrap_or(fallback),"language":language}));
            }
        }
    }
    lock(&s.title_job).total = tasks.len() as u64;
    if tasks.is_empty() || s.title_stop.load(Ordering::SeqCst) {
        return Ok(());
    }
    let executable = s.cfg.root.join("bin").join(if cfg!(windows) {
        "dlfilter-titles.exe"
    } else {
        "dlfilter-titles"
    });
    let mut command = if executable.is_file() {
        Command::new(executable)
    } else if let Some(python) = std::env::var_os("DLFILTER_TITLE_PYTHON") {
        let mut c = Command::new(python);
        c.arg(s.cfg.root.join("scripts/title_helper.py"));
        c
    } else {
        bail!(
            "Title helper missing. Install a complete native release; source builds can set DLFILTER_TITLE_PYTHON."
        )
    };
    let mut child = command
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()?;
    let mut input = child.stdin.take().context("Helper input missing")?;
    let mut output = BufReader::new(child.stdout.take().context("Helper output missing")?);
    *lock(&s.child) = Some(child);
    let result = (|| -> Result<()> {
        for task in tasks {
            if s.title_stop.load(Ordering::SeqCst) {
                break;
            }
            writeln!(input, "{task}")?;
            input.flush()?;
            let mut line = String::new();
            ensure!(
                output.read_line(&mut line)? > 0,
                "Title helper stopped unexpectedly"
            );
            let response: serde_json::Value = serde_json::from_str(&line)?;
            if let Some(error) = response["error"].as_str() {
                bail!("{error}");
            }
            ensure!(
                response.get("title").is_some(),
                "Invalid title helper response"
            );
            let title = response["title"].as_str();
            db.execute(
                "INSERT OR IGNORE INTO collected_titles(id,language,title) VALUES (?,?,?)",
                rusqlite::params![task["id"].as_str(), task["language"].as_str(), title],
            )?;
            {
                let mut j = lock(&s.title_job);
                j.done += 1;
                if title.is_some() {
                    j.added += 1;
                }
            }
            // A checkpoint is one committed lookup. Both search slots are held during publication.
            let permits = loop {
                if let Ok(p) = app.workers.clone().try_acquire_many_owned(2) {
                    break p;
                }
                std::thread::sleep(std::time::Duration::from_millis(10));
            };
            app.engine.refresh_titles()?;
            drop(permits);
            std::thread::sleep(std::time::Duration::from_millis(500));
        }
        Ok(())
    })();
    drop(input);
    if let Some(mut child) = lock(&s.child).take() {
        let _ = child.kill();
        let _ = child.wait();
    }
    result
}
use rusqlite::Connection as ConnectionAlias;

fn recover_install(cfg: &Config) -> Result<()> {
    let parent = cfg.data.parent().context("Invalid data directory")?;
    let marker = parent.join(".dlfilter-install.json");
    if !marker.exists() {
        return Ok(());
    }
    let value: serde_json::Value = serde_json::from_slice(&fs::read(&marker)?)?;
    let destination = PathBuf::from(
        value["destination"]
            .as_str()
            .context("Invalid install journal")?,
    );
    let stage = PathBuf::from(value["stage"].as_str().context("Invalid install journal")?);
    let backup = PathBuf::from(
        value["backup"]
            .as_str()
            .context("Invalid install journal")?,
    );
    ensure!(
        destination == cfg.data
            && stage.parent() == Some(parent)
            && backup.parent() == Some(parent),
        "Invalid install journal paths"
    );
    if !destination.exists() {
        if stage.exists() {
            fs::rename(&stage, &destination)?;
        } else if backup.exists() {
            fs::rename(&backup, &destination)?;
        } else {
            bail!("Interrupted installation has no recoverable data. Import the catalogue again.");
        }
    }
    if stage.exists() {
        fs::remove_dir_all(stage)?;
    }
    fs::remove_file(marker)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    fn config(root: &Path) -> Config {
        Config {
            root: root.into(),
            data: root.join("data"),
            cache: root.join("cache"),
            presets: root.join("presets"),
            host: "127.0.0.1".into(),
            port: 8000,
        }
    }
    #[test]
    fn interrupted_promotion_recovers_without_overwriting_existing_data() {
        let tmp = tempfile::tempdir().unwrap();
        let cfg = config(tmp.path());
        let stage = tmp.path().join("staged");
        let backup = tmp.path().join("data.before-setup");
        fs::create_dir(&stage).unwrap();
        fs::write(stage.join("works.sqlite"), b"new").unwrap();
        fs::create_dir(&backup).unwrap();
        fs::write(backup.join("works.sqlite"), b"old").unwrap();
        let marker = tmp.path().join(".dlfilter-install.json");
        assets::atomic(
            &marker,
            &serde_json::to_vec(&json!({"destination":cfg.data,"stage":stage,"backup":backup}))
                .unwrap(),
        )
        .unwrap();
        recover_install(&cfg).unwrap();
        assert_eq!(fs::read(cfg.database()).unwrap(), b"new");
        assert!(backup.exists());
        fs::create_dir(&stage).unwrap();
        fs::write(stage.join("works.sqlite"), b"abandoned").unwrap();
        assets::atomic(
            &marker,
            &serde_json::to_vec(&json!({"destination":cfg.data,"stage":stage,"backup":backup}))
                .unwrap(),
        )
        .unwrap();
        recover_install(&cfg).unwrap();
        assert_eq!(fs::read(cfg.database()).unwrap(), b"new");
        assert!(!stage.exists());
    }
}
