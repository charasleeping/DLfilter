use crate::{
    assets,
    engine::{Engine, fold},
};
use anyhow::Result;
use roaring::RoaringBitmap;
use rusqlite::{Connection, params};
use std::collections::HashMap;

pub struct TitleIndex {
    pub values: HashMap<String, HashMap<String, String>>,
    pub revision: i64,
    text: Connection,
}
impl TitleIndex {
    pub fn empty() -> Result<Self> {
        let text = Connection::open_in_memory()?;
        text.execute_batch(
            "CREATE VIRTUAL TABLE titles USING fts5(text, tokenize='trigram case_sensitive 1');",
        )?;
        Ok(Self {
            values: HashMap::new(),
            revision: 0,
            text,
        })
    }
    pub fn matches(&self, term: &str) -> Result<RoaringBitmap> {
        if term.chars().count() < 3 {
            return Ok(RoaringBitmap::new());
        }
        let expression = format!("\"{}\"", term.replace('"', "\"\""));
        Ok(self
            .text
            .prepare("SELECT rowid FROM titles WHERE titles MATCH ?")?
            .query_map([expression], |r| Ok((r.get::<_, i64>(0)? - 1) as u32))?
            .collect::<rusqlite::Result<_>>()?)
    }
    pub fn names(&self, id: &str) -> impl Iterator<Item = String> + '_ {
        self.values
            .get(id)
            .into_iter()
            .flat_map(|m| m.values())
            .map(|s| fold(s))
    }
    pub fn load(&mut self, engine: &Engine) -> Result<bool> {
        let path = engine.cfg.cache.join("titles.sqlite");
        if !path.exists() {
            return Ok(false);
        }
        let db = Connection::open(path)?;
        schema(&db)?;
        let revision: i64 = db.query_row(
            "SELECT COALESCE(MAX(seq),0) FROM collected_titles",
            [],
            |r| r.get(0),
        )?;
        if revision == self.revision {
            return Ok(false);
        }
        let mut changed = std::collections::HashSet::new();
        for row in db
            .prepare("SELECT id,language,title FROM collected_titles WHERE seq>? ORDER BY seq")?
            .query_map([self.revision], |r| {
                Ok((
                    r.get::<_, String>(0)?,
                    r.get::<_, String>(1)?,
                    r.get::<_, Option<String>>(2)?,
                ))
            })?
        {
            let (id, lang, title) = row?;
            if engine.ids.contains_key(&id)
                && ["ENG", "CHI_HANT", "CHI_HANS"].contains(&lang.as_str())
            {
                if let Some(t) = title {
                    self.values.entry(id.clone()).or_default().insert(lang, t);
                }
                changed.insert(id);
            }
        }
        let tx = self.text.transaction()?;
        for id in changed {
            let rowid = engine.ids[&id] as i64 + 1;
            tx.execute("DELETE FROM titles WHERE rowid=?", [rowid])?;
            let names = self
                .values
                .get(&id)
                .map(|m| m.values().map(|s| fold(s)).collect::<Vec<_>>().join("\n"))
                .unwrap_or_default();
            tx.execute(
                "INSERT INTO titles(rowid,text) VALUES (?,?)",
                params![rowid, names],
            )?;
        }
        tx.commit()?;
        self.revision = revision;
        Ok(true)
    }
}
pub fn schema(db: &Connection) -> Result<()> {
    db.execute_batch("PRAGMA busy_timeout=5000; CREATE TABLE IF NOT EXISTS collected_titles(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT NOT NULL,language TEXT NOT NULL,title TEXT,UNIQUE(id,language));")?;
    Ok(())
}
#[derive(serde::Serialize, serde::Deserialize, Default, Clone)]
pub struct Preferences {
    pub languages: Vec<String>,
    pub enabled: bool,
}
pub fn save_preferences(path: &std::path::Path, p: &Preferences) -> Result<()> {
    assets::atomic(path, &serde_json::to_vec(p)?)
}
