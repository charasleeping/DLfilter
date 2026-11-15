use crate::{
    engine::{Engine, Params, fold, product_id},
    presets,
};
use axum::{
    Json, Router,
    extract::{DefaultBodyLimit, Path, RawQuery, State},
    http::StatusCode,
    response::{Html, IntoResponse, Response},
    routing::{get, post},
};
use serde_json::{Value, json};
use std::{
    fs,
    sync::{Arc, Mutex},
    time::UNIX_EPOCH,
};
use tokio::sync::Semaphore;
pub struct App {
    pub engine: Arc<Engine>,
    pub workers: Arc<Semaphore>,
    pub preset_lock: Mutex<()>,
}
pub fn new_app(engine: Engine) -> Arc<App> {
    Arc::new(App {
        engine: Arc::new(engine),
        workers: Arc::new(Semaphore::new(2)),
        preset_lock: Mutex::new(()),
    })
}
pub fn router_shared(state: Arc<App>) -> Router {
    let static_dir = state.engine.cfg.root.join("static");
    Router::new()
        .route("/", get(root))
        .route("/api/info", get(info))
        .route("/api/locale/{locale}", get(locale))
        .route("/api/works", get(works))
        .route("/api/search", get(search))
        .route("/api/random", get(random))
        .route("/api/similarity", post(similarity))
        .route("/api/presets", get(list_presets))
        .route("/api/presets/{name}", get(load_preset).put(save_preset))
        .nest_service("/static", tower_http::services::ServeDir::new(static_dir))
        .layer(DefaultBodyLimit::max(100_000))
        .with_state(state)
}
pub fn error(code: u16, key: &str, message: &str) -> Response {
    (
        StatusCode::from_u16(code).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
        Json(json!({"state":"error","code":key,"message":message})),
    )
        .into_response()
}
fn db_error(e: anyhow::Error) -> Response {
    eprintln!("Request failed: {e:#}");
    error(500, "database_error", "Failed to read the database.")
}
async fn block<F>(state: Arc<App>, f: F) -> Response
where
    F: FnOnce(&App) -> anyhow::Result<Response> + Send + 'static,
{
    let permit = match state.workers.clone().acquire_owned().await {
        Ok(p) => p,
        Err(_) => return error(503, "unavailable", "Server is stopping."),
    };
    match tokio::task::spawn_blocking(move || {
        let _permit = permit;
        f(&state)
    })
    .await
    {
        Ok(Ok(r)) => r,
        Ok(Err(e)) => db_error(e),
        Err(e) => db_error(e.into()),
    }
}
async fn root(State(state): State<Arc<App>>) -> Response {
    block(state, |s| {
        let mut html = fs::read_to_string(s.engine.cfg.root.join("templates/index.html"))?;
        for name in ["script.js", "localisation.js", "template.js", "style.css"] {
            let version = fs::metadata(s.engine.cfg.root.join("static").join(name))?
                .modified()?
                .duration_since(UNIX_EPOCH)?
                .as_secs();
            html = html.replace(
                &format!("{{{{ asset_url('{name}') }}}}"),
                &format!("/static/{name}?v={version}"),
            );
        }
        Ok(Html(html).into_response())
    })
    .await
}
async fn info(State(state): State<Arc<App>>) -> Response {
    block(state,|s|{let date:chrono::DateTime<chrono::Utc>=fs::metadata(s.engine.cfg.database())?.modified()?.into();Ok(Json(json!({"state":"success","length":s.engine.data.works.len(),"time":date.format("%Y-%m-%d %H:%M:%S").to_string()})).into_response())}).await
}
async fn locale(State(state): State<Arc<App>>, Path(locale): Path<String>) -> Response {
    let language = if ["en_US", "ja_JP", "zh_TW", "zh_CN", "ko_KR"].contains(&locale.as_str()) {
        locale.as_str()
    } else {
        "en_US"
    };
    let label = |values: &Value, fallback: &str| {
        values
            .get(language)
            .or_else(|| values.get("en_US"))
            .or_else(|| values.get("ja_JP"))
            .and_then(Value::as_str)
            .unwrap_or(fallback)
            .to_owned()
    };
    let mut genres = serde_json::Map::new();
    if let Some(table) = state.engine.genre_json.as_object() {
        for (id, g) in table {
            genres.insert(id.clone(),json!({"name":label(&g["name"],id),"category":label(&g["category"],"Other"),"count":g.get("count").unwrap_or(&json!(0))}));
        }
    }
    let mut formats = serde_json::Map::new();
    if let Some(table) = state.engine.format_json.as_object() {
        for (id, g) in table {
            formats.insert(id.clone(),json!({"name":label(&g["name"],id),"category":label(&g["category"],"Other"),"category_id":g["category"].get("en_US").and_then(Value::as_str).unwrap_or("Miscellaneous")}));
        }
    }
    Json(json!({"state":"success","locale":{"genres":genres,"work_formats":formats}}))
        .into_response()
}
async fn works(State(state): State<Arc<App>>, RawQuery(raw): RawQuery) -> Response {
    let values: Vec<(String, String)> =
        match serde_urlencoded::from_str(raw.as_deref().unwrap_or("")) {
            Ok(v) => v,
            Err(_) => return error(422, "invalid_query", "Invalid work IDs."),
        };
    let ids: Vec<_> = values
        .into_iter()
        .filter(|(key, _)| key == "rj_id")
        .map(|(_, value)| product_id(&value))
        .collect();
    if ids.is_empty() || ids.iter().any(Option::is_none) {
        return error(
            422,
            "invalid_id",
            "Use RJ, BJ or VJ followed by 6 or 8 digits.",
        );
    }
    if ids.len() > 50 {
        return Json(
            json!({"state":"error","message":"The maximum number of requesting works is 50."}),
        )
        .into_response();
    }
    let ids: Vec<String> = ids.into_iter().flatten().collect();
    block(state, move |s| {
        let found = s.engine.hydrate(&ids, &[], true)?;
        let mut works = serde_json::Map::new();
        let mut missing = vec![];
        for id in ids {
            if let Some(work) = found.get(&id) {
                works.insert(id, work.clone());
            } else if !works.contains_key(&id) {
                missing.push(id.clone());
                works.insert(id, json!({}));
            }
        }
        Ok(Json(json!({"state":"success","works":works,"missing":missing})).into_response())
    })
    .await
}
fn parse(raw: Option<String>, state: &App) -> std::result::Result<Params, Box<Response>> {
    if raw.as_ref().is_some_and(|r| r.len() > 16384) {
        return Err(Box::new(error(422, "invalid_query", "Query too large.")));
    }
    let mut pairs: Vec<(String, String)> = serde_urlencoded::from_str(raw.as_deref().unwrap_or(""))
        .map_err(|_| Box::new(error(422, "invalid_query", "Invalid query parameters.")))?;
    for (key, value) in &mut pairs {
        if key == "excluded_low_rate" {
            *value = match value.to_ascii_lowercase().as_str() {
                "1" | "true" | "t" | "yes" | "on" | "y" => "true".into(),
                "0" | "false" | "f" | "no" | "off" | "n" => "false".into(),
                _ => value.clone(),
            };
        }
    }
    let encoded = serde_urlencoded::to_string(pairs).unwrap_or_default();
    let mut p: Params = serde_urlencoded::from_str(&encoded)
        .map_err(|_| Box::new(error(422, "invalid_query", "Invalid query parameters.")))?;
    state
        .engine
        .validate(&mut p)
        .map_err(|(code, key)| Box::new(error(code, key, "Invalid search parameters.")))?;
    Ok(p)
}

async fn search(State(state): State<Arc<App>>, RawQuery(raw): RawQuery) -> Response {
    let p = match parse(raw, &state) {
        Ok(p) => p,
        Err(r) => return *r,
    };
    block(state, move |s| search_response(&s.engine, &p)).await
}
fn search_response(engine: &Engine, p: &Params) -> anyhow::Result<Response> {
    let ranked = engine.ranked(p)?;
    let begin = ((p.page - 1) as usize)
        .saturating_mul(p.page_size as usize)
        .min(ranked.ids.len());
    let end = (begin + p.page_size as usize).min(ranked.ids.len());
    let ids: Vec<String> = ranked.ids[begin..end]
        .iter()
        .map(|&i| engine.data.works[i as usize].id.clone())
        .collect();
    let terms: Vec<String> = fold(&p.q).split_whitespace().map(str::to_owned).collect();
    let mut found = engine.hydrate(&ids, &terms, false)?;
    let mut results = vec![];
    for (offset, id) in ids.iter().enumerate() {
        if let Some(mut work) = found.remove(id) {
            if let Some(scores) = &ranked.scores {
                work["score"] = json!(scores[begin + offset]);
            }
            results.push(work);
        }
    }
    Ok(Json(json!({"state":"success","source":"local","query":p.q,"field":p.field,"page":p.page,"page_size":p.page_size,"total":ranked.ids.len(),"results":results})).into_response())
}
async fn random(State(state): State<Arc<App>>, RawQuery(raw): RawQuery) -> Response {
    let p = match parse(raw, &state) {
        Ok(p) => p,
        Err(r) => return *r,
    };
    block(state, move |s| {
        let indices = s.engine.random(&p)?;
        let ids: Vec<String> = indices
            .iter()
            .map(|&i| s.engine.data.works[i as usize].id.clone())
            .collect();
        let terms: Vec<String> = fold(&p.q).split_whitespace().map(str::to_owned).collect();
        let mut found = s.engine.hydrate(&ids, &terms, false)?;
        let results: Vec<_> = ids.iter().filter_map(|id| found.remove(id)).collect();
        Ok(Json(json!({"state":"success","source":"local","results":results})).into_response())
    })
    .await
}
async fn similarity(
    State(state): State<Arc<App>>,
    body: std::result::Result<Json<Value>, axum::extract::rejection::JsonRejection>,
) -> Response {
    let Json(body) = match body {
        Ok(v) => v,
        Err(_) => return error(422, "invalid_query", "Invalid JSON."),
    };
    if !body
        .get("genres")
        .and_then(Value::as_str)
        .is_some_and(|s| !s.is_empty())
    {
        return error(422, "invalid_genres", "Select scoring genres.");
    }
    let mut defaults = json!({"genres":null,"weight_func":1,"excluded_low_rate":true,"excluded_options":"AIG+AIP+GRO+MEN"});
    if let Some(map) = body.as_object() {
        for (k, v) in map {
            defaults[k] = v.clone();
        }
    }
    let mut p: Params = match serde_json::from_value(defaults) {
        Ok(v) => v,
        Err(_) => return error(422, "invalid_query", "Invalid similarity parameters."),
    };
    p.since = Some(
        body.get("date")
            .and_then(Value::as_str)
            .unwrap_or("2000-01-01")
            .chars()
            .take(10)
            .collect(),
    );
    if let Err((code, key)) = state.engine.validate(&mut p) {
        return error(code, key, "Invalid similarity parameters.");
    }
    block(state,move|s|{let start=std::time::Instant::now();let ranked=s.engine.ranked(&p)?;if ranked.ids.is_empty(){return Ok(Json(json!({"state":"error","message":"No similar works found."})).into_response());}let result:Vec<_>=ranked.ids.iter().zip(ranked.scores.as_ref().unwrap()).take(240).map(|(&i,&score)|json!([s.engine.data.works[i as usize].id,score])).collect();Ok(Json(json!({"state":"success","result":result,"info":{"length":ranked.ids.len(),"time":start.elapsed().as_secs_f64()}})).into_response())}).await
}
async fn list_presets(State(state): State<Arc<App>>) -> Response {
    block(state,|s|{let folder=s.engine.cfg.presets.file_name().unwrap_or_default().to_string_lossy();Ok(Json(json!({"state":"success","folder":folder,"presets":presets::list(&s.engine.cfg.presets)?})).into_response())}).await
}
async fn load_preset(State(state): State<Arc<App>>, Path(name): Path<String>) -> Response {
    if !presets::valid_name(&name) {
        return error(
            400,
            "invalid_name",
            "Use up to 60 letters, digits, spaces, - or _.",
        );
    }
    block(state, move |s| {
        if !s.engine.cfg.presets.join(format!("{name}.json")).exists() {
            return Ok(error(404, "not_found", "No preset has this name."));
        }
        match presets::load(&s.engine.cfg.presets, &name) {
            Ok(p) => Ok(Json(json!({"state":"success","name":name,"preset":p})).into_response()),
            Err(_) => Ok(error(
                422,
                "invalid_preset",
                "The preset file could not be read.",
            )),
        }
    })
    .await
}
async fn save_preset(
    State(state): State<Arc<App>>,
    Path(name): Path<String>,
    body: std::result::Result<Json<presets::Preset>, axum::extract::rejection::JsonRejection>,
) -> Response {
    if !presets::valid_name(&name) {
        return error(
            400,
            "invalid_name",
            "Use up to 60 letters, digits, spaces, - or _.",
        );
    }
    let Json(mut p) = match body {
        Ok(p) => p,
        Err(_) => return error(422, "invalid_preset", "Invalid preset content."),
    };
    if p.validate().is_err() {
        return error(422, "invalid_preset", "Invalid preset content.");
    }
    block(state, move |s| {
        match presets::save(&s.engine.cfg.presets, &name, &p, &s.preset_lock) {
            Ok(true) => Ok(Json(json!({"state":"success","name":name})).into_response()),
            Ok(false) => Ok(error(
                409,
                "too_many_presets",
                "At most 200 presets can be saved.",
            )),
            Err(_) => Ok(error(500, "save_failed", "The preset could not be saved.")),
        }
    })
    .await
}
