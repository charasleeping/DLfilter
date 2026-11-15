use crate::{assets, config::Config};
use anyhow::{Result, ensure};
use roaring::RoaringBitmap;
use rusqlite::{Connection, OpenFlags};
use serde::{Deserialize, Serialize};
use std::{
    collections::{HashMap, VecDeque},
    fs,
    io::Write,
    sync::{Arc, Mutex, OnceLock},
};

pub fn fold(s: &str) -> String {
    let n = icu_normalizer::ComposingNormalizerBorrowed::new_nfkc().normalize(s);
    icu_casemap::CaseMapper::new().fold_string(&n).into_owned()
}
pub fn product_id(s: &str) -> Option<String> {
    let id = icu_normalizer::ComposingNormalizerBorrowed::new_nfkc()
        .normalize(s)
        .trim()
        .to_uppercase();
    let b = id.as_bytes();
    ((b.len() == 8 || b.len() == 10)
        && [b"RJ", b"BJ", b"VJ"].iter().any(|p| b.starts_with(*p))
        && b[2..].iter().all(u8::is_ascii_digit))
    .then_some(id)
}
pub fn split(s: &Option<String>) -> Vec<String> {
    let mut values: Vec<String> = s
        .as_deref()
        .unwrap_or("")
        .split('+')
        .filter(|x| !x.is_empty())
        .map(str::to_owned)
        .collect();
    values.sort();
    values.dedup();
    values
}
fn lock<T>(m: &Mutex<T>) -> std::sync::MutexGuard<'_, T> {
    m.lock().unwrap_or_else(|e| e.into_inner())
}
#[derive(Clone, Serialize, Deserialize)]
pub struct Work {
    pub id: String,
    pub name: String,
    pub names: Vec<String>,
    pub maker: String,
    pub tags: Vec<u16>,
    pub norms: [f64; 4],
    pub date: String,
    pub downloads: f64,
}
#[derive(Serialize, Deserialize)]
pub struct Snapshot {
    pub works: Vec<Work>,
    pub gram: Vec<f64>,
    pub genre_ids: Vec<String>,
    pub weights: [Vec<f64>; 4],
    pub ages: [RoaringBitmap; 3],
    pub genres: HashMap<String, RoaringBitmap>,
    pub formats: HashMap<String, RoaringBitmap>,
    pub options: [RoaringBitmap; 4],
    pub rated: RoaringBitmap,
    pub newest: Vec<u32>,
    pub title_order: Vec<u32>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(default)]
pub struct Params {
    pub q: String,
    pub field: String,
    pub ages: String,
    pub page: i64,
    pub page_size: i64,
    pub count: i64,
    pub genres: Option<String>,
    pub rj_id: Option<String>,
    pub categories: Option<String>,
    pub included_genres: Option<String>,
    pub excluded_genres: Option<String>,
    pub since: Option<String>,
    pub excluded_low_rate: bool,
    pub excluded_options: Option<String>,
    pub weight_func: u8,
    pub dlcount: i64,
}
impl Default for Params {
    fn default() -> Self {
        Self {
            q: String::new(),
            field: "all".into(),
            ages: "100".into(),
            page: 1,
            page_size: 48,
            count: 48,
            genres: None,
            rj_id: None,
            categories: None,
            included_genres: None,
            excluded_genres: None,
            since: None,
            excluded_low_rate: false,
            excluded_options: None,
            weight_func: 4,
            dlcount: 50,
        }
    }
}
#[derive(Clone)]
pub struct Ranked {
    pub ids: Vec<u32>,
    pub scores: Option<Vec<f64>>,
}
impl Ranked {
    fn bytes(&self) -> usize {
        self.ids.capacity() * 4 + self.scores.as_ref().map_or(0, |v| v.capacity() * 8)
    }
}
#[derive(Default)]
struct Cache {
    entries: VecDeque<(String, Arc<Ranked>)>,
    bytes: usize,
}
impl Cache {
    fn get(&mut self, key: &str) -> Option<Arc<Ranked>> {
        let i = self.entries.iter().position(|(k, _)| k == key)?;
        let e = self.entries.remove(i)?;
        let result = e.1.clone();
        self.entries.push_front(e);
        Some(result)
    }
    fn insert(&mut self, key: String, result: Arc<Ranked>) {
        let n = result.bytes() + key.len();
        if n > 64 * 1024 * 1024 {
            return;
        }
        if self.entries.iter().any(|(k, _)| k == &key) {
            return;
        }
        while self.bytes + n > 64 * 1024 * 1024 {
            if let Some((k, v)) = self.entries.pop_back() {
                self.bytes -= v.bytes() + k.len();
            } else {
                break;
            }
        }
        self.bytes += n;
        self.entries.push_front((key, result));
    }
}
type Flight = Arc<OnceLock<std::result::Result<Arc<Ranked>, String>>>;
pub struct Engine {
    pub titles: Mutex<crate::titles::TitleIndex>,
    pub data: Snapshot,
    pub cfg: Config,
    pub genre_json: serde_json::Value,
    pub format_json: serde_json::Value,
    pub ids: HashMap<String, u32>,
    db: Mutex<Connection>,
    text: Mutex<Connection>,
    cache: Mutex<Cache>,
    flights: Mutex<HashMap<String, Flight>>,
}
#[derive(Serialize, Deserialize)]
struct CacheManifest {
    version: u32,
    fingerprint: String,
    snapshot_sha: String,
    text_sha: String,
}
pub fn readonly(path: &std::path::Path) -> Result<Connection> {
    Ok(Connection::open_with_flags(
        path,
        OpenFlags::SQLITE_OPEN_READ_ONLY,
    )?)
}
fn weight(count: f64, mode: usize) -> f64 {
    let x = (count.max(0.) + 1.).log10();
    match mode {
        0 => 1. - 1. / (1. + ((-x + 4.25) * 4.).exp()),
        1 => 1. / (1. + ((-x + 2.75) * 4.).exp()),
        2 => (-(x - 3.5).powi(2)).exp(),
        _ => 1.,
    }
}
impl Engine {
    pub fn load(cfg: Config, force: bool) -> Result<Self> {
        fs::create_dir_all(&cfg.cache)?;
        let guard = fs::OpenOptions::new()
            .create(true)
            .truncate(false)
            .read(true)
            .write(true)
            .open(cfg.cache.join("prepare.lock"))?;
        fs2::FileExt::lock_exclusive(&guard)?;
        let key = assets::fingerprint(&cfg)?;
        let snap = cfg.cache.join("search.bin");
        let text_path = cfg.cache.join("text.sqlite");
        let manifest = cfg.cache.join("cache.json");
        let cached = (|| -> Result<Snapshot> {
            let m: CacheManifest = serde_json::from_slice(&fs::read(&manifest)?)?;
            ensure!(
                !force && m.version == 1 && m.fingerprint == key,
                "Stale cache"
            );
            ensure!(
                assets::file_digest(&snap)? == m.snapshot_sha
                    && assets::file_digest(&text_path)? == m.text_sha,
                "Corrupt cache"
            );
            let bytes = fs::read(&snap)?;
            Ok(bincode::deserialize(&bytes)?)
        })();
        let db = readonly(&cfg.database())?;
        assets::required_database(&db)?;
        let genre_json = assets::json(&cfg.data.join("genre_table.json"))?;
        let format_json = assets::json(&cfg.data.join("workformat.json"))?;
        let data = match cached {
            Ok(data) => data,
            Err(_) => {
                eprintln!("Preparing search metadata and text index…");
                let vectors = assets::vectors(&cfg.data)?;
                let n = vectors.ids.len();
                let index: HashMap<_, _> = vectors
                    .ids
                    .iter()
                    .enumerate()
                    .map(|(i, g)| (g.clone(), i as u16))
                    .collect();
                let weights = std::array::from_fn(|mode| {
                    vectors
                        .ids
                        .iter()
                        .map(|g| weight(genre_json[g]["count"].as_f64().unwrap_or(0.), mode))
                        .collect::<Vec<_>>()
                });
                let mut data = Snapshot {
                    works: Vec::new(),
                    gram: vectors.gram,
                    genre_ids: vectors.ids,
                    weights,
                    ages: std::array::from_fn(|_| RoaringBitmap::new()),
                    genres: HashMap::new(),
                    formats: HashMap::new(),
                    options: std::array::from_fn(|_| RoaringBitmap::new()),
                    rated: RoaringBitmap::new(),
                    newest: Vec::new(),
                    title_order: Vec::new(),
                };
                let tmp = tempfile::NamedTempFile::new_in(&cfg.cache)?;
                let mut text = Connection::open(tmp.path())?;
                text.execute_batch("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF; PRAGMA cache_size=-16384; CREATE VIRTUAL TABLE search_text USING fts5(names,maker,tokenize='trigram case_sensitive 1');")?;
                let tx = text.transaction()?;
                {
                    let mut insert =
                        tx.prepare("INSERT INTO search_text(rowid,names,maker) VALUES (?,?,?)")?;
                    let present = columns(&db)?;
                    let optional = |name: &str| {
                        if present.iter().any(|x| x == name) {
                            format!("[{name}]")
                        } else {
                            "NULL".into()
                        }
                    };
                    let sql = format!(
                        "SELECT [index],COALESCE(name,''),COALESCE(maker,''),COALESCE(tags,''),COALESCE(registDate,''),COALESCE(dlCount,0),COALESCE(ageCategory,0),COALESCE(type,''),COALESCE(options,''),COALESCE(rate,0),{},{},{} FROM maniax ORDER BY [index]",
                        optional("name_ENG"),
                        optional("name_CHI_HANT"),
                        optional("name_CHI_HANS")
                    );
                    let mut stmt = db.prepare(&sql)?;
                    let mut rows = stmt.query([])?;
                    while let Some(r) = rows.next()? {
                        let i = data.works.len() as u32;
                        let id: String = r.get(0)?;
                        let name: String = r.get(1)?;
                        let maker = fold(&r.get::<_, String>(2)?);
                        let raw_tags: String = r.get(3)?;
                        let mut names = vec![fold(&name)];
                        for k in 10..13 {
                            if let Some(s) = r.get::<_, Option<String>>(k)? {
                                names.push(fold(&s));
                            }
                        }
                        let mut valid = true;
                        let mut tags = Vec::new();
                        for tag in raw_tags.split('#').filter(|x| !x.is_empty()) {
                            data.genres.entry(tag.into()).or_default().insert(i);
                            if let Some(k) = index.get(tag) {
                                tags.push(*k);
                            } else {
                                valid = false;
                            }
                        }
                        let mut norms = [0.; 4];
                        if valid && !tags.is_empty() {
                            for (mode, norm) in norms.iter_mut().enumerate() {
                                let mut sum = 0.;
                                for &a in &tags {
                                    for &b in &tags {
                                        sum += data.weights[mode][a as usize]
                                            * data.weights[mode][b as usize]
                                            * data.gram[a as usize * n + b as usize];
                                    }
                                }
                                *norm = sum.max(0.).sqrt();
                            }
                        }
                        let age: i64 = r.get(6)?;
                        if (1..=3).contains(&age) {
                            data.ages[age as usize - 1].insert(i);
                        }
                        data.formats.entry(r.get(7)?).or_default().insert(i);
                        let options: String = r.get(8)?;
                        for (k, option) in ["AIG", "AIP", "GRO", "MEN"].iter().enumerate() {
                            if options.split('#').any(|x| x == *option) {
                                data.options[k].insert(i);
                            }
                        }
                        if r.get::<_, f64>(9)? >= 40. {
                            data.rated.insert(i);
                        }
                        insert.execute(rusqlite::params![i as i64 + 1, names.join("\n"), maker])?;
                        data.works.push(Work {
                            id,
                            name,
                            names,
                            maker,
                            tags,
                            norms,
                            date: r.get(4)?,
                            downloads: r.get::<_, f64>(5)?.max(0.),
                        });
                    }
                }
                tx.commit()?;
                drop(text);
                ensure!(data.works.len() <= u32::MAX as usize, "Catalogue too large");
                data.newest = (0..data.works.len() as u32).collect();
                data.newest.sort_unstable_by(|&a, &b| {
                    data.works[b as usize]
                        .date
                        .cmp(&data.works[a as usize].date)
                        .then(a.cmp(&b))
                });
                data.title_order = (0..data.works.len() as u32).collect();
                data.title_order.sort_unstable_by(|&a, &b| {
                    data.works[a as usize]
                        .name
                        .cmp(&data.works[b as usize].name)
                        .then(a.cmp(&b))
                });
                let mut file = tempfile::NamedTempFile::new_in(&cfg.cache)?;
                bincode::serialize_into(&mut file, &data)?;
                file.flush()?;
                file.as_file().sync_all()?;
                let m = CacheManifest {
                    version: 1,
                    fingerprint: key,
                    snapshot_sha: assets::file_digest(file.path())?,
                    text_sha: assets::file_digest(tmp.path())?,
                };
                file.persist(&snap)?;
                tmp.persist(&text_path)?;
                assets::atomic(&manifest, &serde_json::to_vec(&m)?)?;
                data
            }
        };
        fs2::FileExt::unlock(&guard)?;
        let ids = data
            .works
            .iter()
            .enumerate()
            .map(|(i, w)| (w.id.clone(), i as u32))
            .collect();
        let text = readonly(&text_path)?;
        db.execute_batch("PRAGMA cache_size=-8192")?;
        text.execute_batch("PRAGMA cache_size=-8192")?;
        let engine = Self {
            titles: Mutex::new(crate::titles::TitleIndex::empty()?),
            data,
            cfg,
            genre_json,
            format_json,
            ids,
            db: Mutex::new(db),
            text: Mutex::new(text),
            cache: Mutex::default(),
            flights: Mutex::default(),
        };
        engine.refresh_titles()?;
        Ok(engine)
    }
    pub fn refresh_titles(&self) -> Result<()> {
        if lock(&self.titles).load(self)? {
            *lock(&self.cache) = Cache::default();
        }
        Ok(())
    }
    pub fn validate(&self, p: &mut Params) -> std::result::Result<(), (u16, &'static str)> {
        p.q = p.q.trim().into();
        if p.q.chars().count() > 100 {
            return Err((400, "query_too_long"));
        }
        if !["all", "title", "artist", "id"].contains(&p.field.as_str()) {
            return Err((400, "invalid_field"));
        }
        if p.ages.len() != 3 || !p.ages.bytes().all(|b| b == b'0' || b == b'1') {
            return Err((400, "invalid_ages"));
        }
        if p.page < 1 || p.page > i32::MAX as i64 {
            return Err((400, "invalid_page"));
        }
        if !(1..=48).contains(&p.page_size) {
            return Err((400, "invalid_page_size"));
        }
        if !(1..=48).contains(&p.count) {
            return Err((400, "invalid_count"));
        }
        for (value, kind, max) in [
            (&p.genres, 0, 1000),
            (&p.included_genres, 0, 5),
            (&p.excluded_genres, 0, 5),
            (&p.categories, 1, 1000),
            (&p.excluded_options, 2, 4),
        ] {
            let items = split(value);
            if items.len() > max
                || items.iter().any(|id| match kind {
                    0 => self.genre_json.get(id).is_none(),
                    1 => self.format_json.get(id).is_none(),
                    _ => !["AIG", "AIP", "GRO", "MEN"].contains(&id.as_str()),
                })
            {
                return Err((422, "invalid_filter"));
            }
        }
        if split(&p.included_genres)
            .iter()
            .any(|g| split(&p.excluded_genres).contains(g))
        {
            return Err((400, "conflicting_genres"));
        }
        if let Some(id) = &p.rj_id {
            p.rj_id = Some(product_id(id).ok_or((422, "invalid_id"))?);
        }
        if let Some(since) = &p.since
            && (since.len() != 10 || chrono::NaiveDate::parse_from_str(since, "%Y-%m-%d").is_err())
        {
            return Err((422, "invalid_since"));
        }
        if !(1..=4).contains(&p.weight_func) || !(0..=100).contains(&p.dlcount) {
            return Err((422, "invalid_weight"));
        }
        let selected = split(&p.genres);
        if !selected.is_empty() {
            let indices: Vec<usize> = selected
                .iter()
                .map(|id| self.data.genre_ids.binary_search(id))
                .collect::<std::result::Result<_, _>>()
                .map_err(|_| (422, "invalid_genres"))?;
            let weights = &self.data.weights[p.weight_func as usize - 1];
            let n = self.data.genre_ids.len();
            let norm_squared: f64 = indices
                .iter()
                .flat_map(|&i| {
                    indices
                        .iter()
                        .map(move |&j| weights[i] * weights[j] * self.data.gram[i * n + j])
                })
                .sum();
            if !norm_squared.is_finite() || norm_squared <= 0. {
                return Err((422, "invalid_genres"));
            }
        }
        Ok(())
    }
    fn eligible(&self, p: &Params) -> Result<RoaringBitmap> {
        let mut result = RoaringBitmap::new();
        for (i, b) in p.ages.bytes().enumerate() {
            if b == b'1' || p.ages == "000" {
                result |= &self.data.ages[i];
            }
        }
        let cats = split(&p.categories);
        if !cats.is_empty() {
            let mut selected = RoaringBitmap::new();
            for c in cats {
                if let Some(ids) = self.data.formats.get(&c) {
                    selected |= ids;
                }
            }
            result &= selected;
        }
        for g in split(&p.included_genres) {
            if let Some(ids) = self.data.genres.get(&g) {
                result &= ids;
            } else {
                result.clear();
            }
        }
        for g in split(&p.excluded_genres) {
            if let Some(ids) = self.data.genres.get(&g) {
                result -= ids;
            }
        }
        for option in split(&p.excluded_options) {
            if let Some(i) = ["AIG", "AIP", "GRO", "MEN"]
                .iter()
                .position(|x| *x == option)
            {
                result -= &self.data.options[i];
            }
        }
        if p.excluded_low_rate {
            result &= &self.data.rated;
        }
        if let Some(since) = &p.since {
            let len = self
                .data
                .newest
                .partition_point(|&i| self.data.works[i as usize].date.as_str() >= since.as_str());
            let dates: RoaringBitmap = self.data.newest[..len].iter().copied().collect();
            result &= dates;
        }
        let extra = lock(&self.titles);
        let folded = fold(&p.q);
        for term in folded.split_whitespace() {
            let id_matches: RoaringBitmap = if p.field == "all" || p.field == "id" {
                let prefix = term.to_uppercase();
                let begin = self.data.works.partition_point(|w| w.id < prefix);
                self.data.works[begin..]
                    .iter()
                    .take_while(|w| w.id.starts_with(&prefix))
                    .filter_map(|w| self.ids.get(&w.id).copied())
                    .collect()
            } else {
                RoaringBitmap::new()
            };
            if p.field == "id" {
                result &= id_matches;
                continue;
            }
            let mut possible = result.clone();
            if term.chars().count() >= 3 {
                let column = match p.field.as_str() {
                    "title" => "names",
                    "artist" => "maker",
                    _ => "{names maker}",
                };
                let expression = format!("{column} : \"{}\"", term.replace('"', "\"\""));
                let conn = lock(&self.text);
                let mut stmt =
                    conn.prepare("SELECT rowid FROM search_text WHERE search_text MATCH ?")?;
                let hits: RoaringBitmap = stmt
                    .query_map([expression], |r| Ok((r.get::<_, i64>(0)? - 1) as u32))?
                    .collect::<rusqlite::Result<_>>()?;
                let extra_hits = if p.field != "artist" {
                    extra.matches(term)?
                } else {
                    RoaringBitmap::new()
                };
                possible &= hits | &id_matches | extra_hits;
            }
            let verified: RoaringBitmap = possible
                .iter()
                .filter(|&i| {
                    let w = &self.data.works[i as usize];
                    id_matches.contains(i)
                        || ((p.field == "all" || p.field == "title")
                            && (w.names.iter().any(|s| s.contains(term))
                                || extra.names(&w.id).any(|s| s.contains(term))))
                        || ((p.field == "all" || p.field == "artist") && w.maker.contains(term))
                })
                .collect();
            result &= verified;
        }
        Ok(result)
    }
    pub fn ranked(&self, p: &Params) -> Result<Arc<Ranked>> {
        let mut canonical = p.clone();
        canonical.page = 1;
        canonical.page_size = 48;
        canonical.count = 48;
        canonical.q = fold(&p.q).split_whitespace().collect::<Vec<_>>().join(" ");
        for value in [
            &mut canonical.genres,
            &mut canonical.categories,
            &mut canonical.included_genres,
            &mut canonical.excluded_genres,
            &mut canonical.excluded_options,
        ] {
            *value = Some(split(value).join("+"));
        }
        let key = format!(
            "{}:{}",
            lock(&self.titles).revision,
            serde_json::to_string(&canonical)?
        );
        if let Some(r) = lock(&self.cache).get(&key) {
            return Ok(r);
        }
        let cell = lock(&self.flights)
            .entry(key.clone())
            .or_insert_with(|| Arc::new(OnceLock::new()))
            .clone();
        let result = cell
            .get_or_init(|| self.compute(p).map(Arc::new).map_err(|e| e.to_string()))
            .clone();
        if let Ok(r) = &result {
            lock(&self.cache).insert(key.clone(), r.clone());
        }
        lock(&self.flights).remove(&key);
        result.map_err(anyhow::Error::msg)
    }
    fn compute(&self, p: &Params) -> Result<Ranked> {
        let mut eligible = self.eligible(p)?;
        let selected = split(&p.genres);
        if !selected.is_empty() {
            if let Some(i) = p.rj_id.as_ref().and_then(|s| self.ids.get(s)) {
                eligible.remove(*i);
            }
            let n = self.data.genre_ids.len();
            let mode = p.weight_func as usize - 1;
            let a = &self.data.weights[mode];
            let selected: Vec<usize> = selected
                .iter()
                .filter_map(|s| self.data.genre_ids.binary_search(s).ok())
                .collect();
            let mut qnorm = 0.;
            for &i in &selected {
                for &j in &selected {
                    qnorm += a[i] * a[j] * self.data.gram[i * n + j];
                }
            }
            let qnorm = qnorm.max(0.).sqrt();
            ensure!(qnorm.is_finite() && qnorm > 0., "Unusable scoring genres");
            let dots: Vec<f64> = (0..n)
                .map(|i| {
                    a[i] * selected
                        .iter()
                        .map(|&j| a[j] * self.data.gram[i * n + j])
                        .sum::<f64>()
                        / qnorm
                })
                .collect();
            let mut scored: Vec<(u32, f64)> = eligible
                .iter()
                .filter_map(|i| {
                    let w = &self.data.works[i as usize];
                    let norm = w.norms[mode];
                    if norm <= 0. || !norm.is_finite() {
                        return None;
                    }
                    let mut score = w.tags.iter().map(|&g| dots[g as usize]).sum::<f64>() / norm;
                    if p.dlcount != 50 {
                        let sigma = 2. * p.dlcount as f64 / 50. - 2.;
                        let y = (w.downloads + 1.).log10() - 2.09;
                        score *= ((2. * sigma * y - sigma * sigma) / 2.).min(0.).exp();
                    }
                    score.is_finite().then_some((i, score))
                })
                .collect();
            scored.sort_unstable_by(|(a, x), (b, y)| y.total_cmp(x).then(a.cmp(b)));
            let (ids, scores) = scored.into_iter().unzip();
            Ok(Ranked {
                ids,
                scores: Some(scores),
            })
        } else {
            let q = fold(&p.q).split_whitespace().collect::<Vec<_>>().join(" ");
            let mut ids: Vec<u32> = if q.is_empty() {
                self.data
                    .newest
                    .iter()
                    .copied()
                    .filter(|i| eligible.contains(*i))
                    .collect()
            } else {
                self.data
                    .title_order
                    .iter()
                    .copied()
                    .filter(|i| eligible.contains(*i))
                    .collect()
            };
            if !q.is_empty() {
                let extra = lock(&self.titles);
                let id = product_id(&q);
                ids.sort_by_key(|&i| {
                    let w = &self.data.works[i as usize];
                    if id.as_deref() == Some(w.id.as_str()) {
                        0
                    } else {
                        let (exact, prefix) = if p.field == "artist" {
                            (w.maker == q, w.maker.starts_with(&q))
                        } else {
                            (
                                w.names.iter().any(|x| x == &q)
                                    || extra.names(&w.id).any(|x| x == q),
                                w.names.iter().any(|x| x.starts_with(&q))
                                    || extra.names(&w.id).any(|x| x.starts_with(&q)),
                            )
                        };
                        if exact {
                            1
                        } else if prefix {
                            2
                        } else {
                            3
                        }
                    }
                });
            }
            Ok(Ranked { ids, scores: None })
        }
    }
    pub fn random(&self, p: &Params) -> Result<Vec<u32>> {
        use rand::seq::index::sample;
        let eligible = self.eligible(p)?;
        let len = eligible.len() as usize;
        let count = (p.count as usize).min(len);
        Ok(sample(&mut rand::rng(), len, count)
            .iter()
            .map(|i| eligible.select(i as u32).unwrap())
            .collect())
    }
    pub fn hydrate(
        &self,
        ids: &[String],
        terms: &[String],
        all_columns: bool,
    ) -> Result<HashMap<String, serde_json::Value>> {
        if ids.is_empty() {
            return Ok(HashMap::new());
        }
        let db = lock(&self.db);
        let present = columns(&db)?;
        let required = [
            "index",
            "name",
            "maker",
            "siteId",
            "type",
            "ageCategory",
            "registDate",
            "tags",
            "options",
            "rate",
            "rateCount",
            "dlCount",
            "reviewCount",
            "description",
        ];
        let optional = [
            "lang",
            "originalWorkno",
            "originalLang",
            "originalName",
            "imageUrl",
            "name_ENG",
            "name_CHI_HANT",
            "name_CHI_HANS",
        ];
        let keys: Vec<String> = if all_columns {
            present.clone()
        } else {
            required
                .iter()
                .chain(optional.iter())
                .map(|s| (*s).into())
                .collect()
        };
        let expressions: Vec<String> = keys
            .iter()
            .map(|k| {
                if present.contains(k) {
                    format!("[{k}]")
                } else {
                    format!("NULL AS [{k}]")
                }
            })
            .collect();
        let sql = format!(
            "SELECT {} FROM maniax WHERE [index] IN ({})",
            expressions.join(","),
            vec!["?"; ids.len()].join(",")
        );
        let mut stmt = db.prepare(&sql)?;
        let mut rows = stmt.query(rusqlite::params_from_iter(ids))?;
        let mut result = HashMap::new();
        while let Some(row) = rows.next()? {
            let mut obj = serde_json::Map::new();
            for (i, k) in keys.iter().enumerate() {
                let value = match row.get_ref(i)? {
                    rusqlite::types::ValueRef::Null => serde_json::Value::Null,
                    rusqlite::types::ValueRef::Integer(n) => serde_json::json!(n),
                    rusqlite::types::ValueRef::Real(n) => serde_json::json!(n),
                    rusqlite::types::ValueRef::Text(s) => {
                        serde_json::Value::String(String::from_utf8_lossy(s).into_owned())
                    }
                    rusqlite::types::ValueRef::Blob(_) => serde_json::Value::Null,
                };
                obj.insert(k.clone(), value);
            }
            for k in ["tags", "options"] {
                let list: Vec<String> = obj
                    .get(k)
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .split('#')
                    .filter(|s| !s.is_empty())
                    .map(str::to_owned)
                    .collect();
                obj.insert(k.into(), serde_json::json!(list));
            }
            if let Some(date) = obj.get("registDate").and_then(|v| v.as_str()) {
                let date = date.split(' ').next().unwrap_or(date).to_owned();
                obj.insert("registDate".into(), date.into());
            }
            if let Some(extra) = lock(&self.titles)
                .values
                .get(obj["index"].as_str().unwrap_or(""))
            {
                for (lang, title) in extra {
                    obj.insert(format!("name_{lang}"), title.clone().into());
                }
            }
            if !all_columns {
                let titles: Vec<_> = [
                    ("ENG", "name_ENG"),
                    ("CHI_HANT", "name_CHI_HANT"),
                    ("CHI_HANS", "name_CHI_HANS"),
                ]
                .into_iter()
                .map(|(lang, k)| (lang, obj.remove(k).unwrap_or_default()))
                .collect();
                let name = obj
                    .get("name")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_owned();
                if !terms.is_empty()
                    && obj.get("lang").is_none_or(|v| v.is_null())
                    && !terms.iter().all(|t| fold(&name).contains(t))
                {
                    for (lang, title) in titles {
                        if let Some(s) = title.as_str()
                            && !s.is_empty()
                            && terms.iter().all(|t| fold(s).contains(t))
                        {
                            obj.insert("originalName".into(), name.clone().into());
                            obj.insert("originalLang".into(), "JPN".into());
                            obj.insert("lang".into(), lang.into());
                            obj.insert("name".into(), s.into());
                            break;
                        }
                    }
                }
                let supported = |key: &str| {
                    obj.get(key)
                        .and_then(|v| v.as_str())
                        .is_some_and(|s| ["ENG", "JPN", "CHI_HANT", "CHI_HANS"].contains(&s))
                };
                let toggle = !terms.is_empty()
                    && supported("lang")
                    && supported("originalLang")
                    && obj.get("lang") != obj.get("originalLang")
                    && obj
                        .get("originalName")
                        .and_then(|v| v.as_str())
                        .is_some_and(|s| {
                            !s.is_empty() && !terms.iter().all(|t| fold(s).contains(t))
                        });
                obj.insert("titleToggle".into(), toggle.into());
            }
            if let Some(id) = obj.get("index").and_then(|v| v.as_str()) {
                result.insert(id.into(), obj.into());
            }
        }
        Ok(result)
    }
}
fn columns(db: &Connection) -> Result<Vec<String>> {
    Ok(db
        .prepare("PRAGMA table_info(maniax)")?
        .query_map([], |r| r.get(1))?
        .collect::<rusqlite::Result<_>>()?)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    fn fixture() -> (tempfile::TempDir, Engine, Vec<[f64; 3]>) {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path();
        let vectors: Vec<[f64; 3]> = (0..12)
            .map(|i| [1., (i as f64 + 1.) / 16., ((i % 3) as f64 - 1.) / 4.])
            .collect();
        let ids: Vec<String> = (1..=12).map(|i| format!("{i:03}")).collect();
        let raw: Vec<u8> = vectors
            .iter()
            .flatten()
            .flat_map(|v| (*v as f32).to_le_bytes())
            .collect();
        fs::write(path.join("genre_vectors.f32"), &raw).unwrap();
        fs::write(
            path.join("genre_vectors.json"),
            serde_json::to_vec(
                &json!({"version":1,"ids":ids,"dimension":3,"sha256":assets::digest(&raw)}),
            )
            .unwrap(),
        )
        .unwrap();
        let genres: serde_json::Map<String, serde_json::Value> = ids
            .iter()
            .map(|id| {
                (
                    id.clone(),
                    json!({"count":100,"name":{"en_US":id},"category":{"en_US":"Tags"}}),
                )
            })
            .collect();
        fs::write(
            path.join("genre_table.json"),
            serde_json::to_vec(&genres).unwrap(),
        )
        .unwrap();
        fs::write(
            path.join("workformat.json"),
            br#"{"MNG":{"name":{"en_US":"Manga"},"category":{"en_US":"Manga"}}}"#,
        )
        .unwrap();
        let db = Connection::open(path.join("works.sqlite")).unwrap();
        db.execute_batch("CREATE TABLE maniax ([index] TEXT,name TEXT,description TEXT,maker TEXT,siteId TEXT,type TEXT,ageCategory INTEGER,tags TEXT,options TEXT,registDate TEXT,dlCount INTEGER,rate INTEGER,rateCount INTEGER,reviewCount INTEGER); CREATE INDEX ids ON maniax([index]);").unwrap();
        let sets = ["#001#002#", "#003#004#012#", "#001#012#", "", "#999#"];
        for (i, tags) in sets.iter().enumerate() {
            db.execute("INSERT INTO maniax VALUES (?,'Example','','Maker','books','MNG',1,?,'#JPN#','2024-01-01',100,45,1,0)",rusqlite::params![format!("BJ{:06}",i+1),tags]).unwrap();
        }
        drop(db);
        let cfg = Config {
            root: path.into(),
            data: path.into(),
            presets: path.join("presets"),
            cache: path.join("cache"),
            host: "127.0.0.1".into(),
            port: 8000,
        };
        let e = Engine::load(cfg, false).unwrap();
        (dir, e, vectors)
    }
    #[test]
    fn compact_scores_match_independent_vectors() {
        let (_dir, e, original) = fixture();
        for mode in 1..=4 {
            let p = Params {
                genres: Some(
                    (1..=12)
                        .map(|i| format!("{i:03}"))
                        .collect::<Vec<_>>()
                        .join("+"),
                ),
                weight_func: mode,
                ages: "000".into(),
                ..Default::default()
            };
            let result = e.ranked(&p).unwrap();
            assert_eq!(result.ids.len(), 3);
            let a = &e.data.weights[mode as usize - 1];
            let mut q = [0.; 3];
            for (i, v) in original.iter().enumerate() {
                for k in 0..3 {
                    q[k] += a[i] * v[k];
                }
            }
            let qnorm = q.iter().map(|x| x * x).sum::<f64>().sqrt();
            for (&i, &score) in result.ids.iter().zip(result.scores.as_ref().unwrap()) {
                let mut v = [0.; 3];
                for &g in &e.data.works[i as usize].tags {
                    for k in 0..3 {
                        v[k] += a[g as usize] * original[g as usize][k];
                    }
                }
                let expected = v.iter().zip(q).map(|(x, y)| x * y).sum::<f64>()
                    / (v.iter().map(|x| x * x).sum::<f64>().sqrt() * qnorm);
                assert!((score - expected).abs() < 1e-12);
            }
        }
    }
    #[test]
    fn filters_and_tagless_browse() {
        let (_dir, e, _) = fixture();
        assert_eq!(e.ranked(&Params::default()).unwrap().ids.len(), 5);
        assert_eq!(
            e.ranked(&Params {
                included_genres: Some("012".into()),
                ..Default::default()
            })
            .unwrap()
            .ids
            .len(),
            2
        );
        let p = Params {
            genres: Some("001".into()),
            rj_id: Some("BJ000001".into()),
            ..Default::default()
        };
        assert_eq!(e.ranked(&p).unwrap().ids.len(), 2);
    }
    #[test]
    fn unicode_and_product_ids() {
        assert_eq!(fold("Ｍａｇｉｃ ＳＴＲＡＳＳＥ"), "magic strasse");
        assert_eq!(fold("Straße"), "strasse");
        assert_eq!(
            product_id(" ｂｊ０１２３４５６７ "),
            Some("BJ01234567".into())
        );
        assert!(product_id("XX123456").is_none());
    }
    #[test]
    fn cache_reuses_result_and_limits_memory() {
        let (_dir, e, _) = fixture();
        let p = Params::default();
        let a = e.ranked(&p).unwrap();
        let b = e.ranked(&Params { page: 2, ..p }).unwrap();
        assert!(Arc::ptr_eq(&a, &b));
        let cache = lock(&e.cache);
        assert!(cache.bytes <= 64 * 1024 * 1024);
    }
}
