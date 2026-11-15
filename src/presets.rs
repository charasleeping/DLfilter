use crate::engine::product_id;
use anyhow::{Result, ensure};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::{fs, path::Path, sync::Mutex};
#[derive(Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Slider {
    #[serde(default)]
    pub enabled: bool,
    pub value: i64,
}
#[derive(Clone, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct Preset {
    pub rj_id: String,
    pub q: String,
    pub field: String,
    pub genres: Vec<String>,
    pub included_genres: Vec<String>,
    pub excluded_genres: Vec<String>,
    pub categories: Vec<String>,
    pub popularity_weight: Slider,
    pub release_date: Slider,
    pub download_count: Slider,
    pub ages: [bool; 3],
    pub excluded_contents: [bool; 5],
    pub advanced_options_open: bool,
}
impl Default for Preset {
    fn default() -> Self {
        Self {
            rj_id: String::new(),
            q: String::new(),
            field: "all".into(),
            genres: vec![],
            included_genres: vec![],
            excluded_genres: vec![],
            categories: vec![],
            popularity_weight: Slider {
                enabled: false,
                value: 1,
            },
            release_date: Slider {
                enabled: false,
                value: 5,
            },
            download_count: Slider {
                enabled: false,
                value: 50,
            },
            ages: [true, false, false],
            excluded_contents: [true; 5],
            advanced_options_open: false,
        }
    }
}
impl Preset {
    pub fn validate(&mut self) -> Result<()> {
        if !self.rj_id.is_empty() {
            self.rj_id =
                product_id(&self.rj_id).ok_or_else(|| anyhow::anyhow!("Invalid product ID"))?;
        }
        ensure!(
            self.q.chars().count() <= 100
                && ["all", "title", "artist", "id"].contains(&self.field.as_str()),
            "Invalid keyword settings"
        );
        for ids in [&self.genres, &self.included_genres, &self.excluded_genres] {
            ensure!(
                ids.len() <= 1000
                    && ids
                        .iter()
                        .all(|s| s.len() == 3 && s.bytes().all(|b| b.is_ascii_digit())),
                "Invalid genres"
            );
        }
        ensure!(
            self.categories.len() <= 1000
                && self.categories.iter().all(|s| s.len() == 3
                    && s.bytes()
                        .all(|b| b.is_ascii_uppercase() || b.is_ascii_digit())),
            "Invalid categories"
        );
        for slider in [
            &self.popularity_weight,
            &self.release_date,
            &self.download_count,
        ] {
            ensure!((0..=100).contains(&slider.value), "Invalid slider");
        }
        Ok(())
    }
}
pub fn valid_name(name: &str) -> bool {
    !name.is_empty()
        && name.chars().count() <= 60
        && name.trim() == name
        && name
            .chars()
            .all(|c| c.is_alphanumeric() || ['_', '-', ' '].contains(&c))
}
pub fn list(dir: &Path) -> Result<Vec<serde_json::Value>> {
    if !dir.exists() {
        return Ok(vec![]);
    }
    let mut result = vec![];
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();
        let Some(name) = path.file_stem().and_then(|s| s.to_str()) else {
            continue;
        };
        if path.extension().is_some_and(|s| s == "json") && path.is_file() && valid_name(name) {
            let date: DateTime<Utc> = entry.metadata()?.modified()?.into();
            result.push(serde_json::json!({"name":name,"modified":date.format("%Y-%m-%dT%H:%M:%SZ").to_string()}));
        }
    }
    result.sort_by(|a, b| b["modified"].as_str().cmp(&a["modified"].as_str()));
    Ok(result)
}
pub fn load(dir: &Path, name: &str) -> Result<Preset> {
    let path = dir.join(format!("{name}.json"));
    ensure!(
        path.canonicalize()?.parent() == Some(dir.canonicalize()?.as_path()),
        "Preset escapes folder"
    );
    let mut p: Preset = serde_json::from_slice(&fs::read(path)?)?;
    p.validate()?;
    Ok(p)
}
pub fn save(dir: &Path, name: &str, preset: &Preset, guard: &Mutex<()>) -> Result<bool> {
    let _guard = guard.lock().unwrap_or_else(|e| e.into_inner());
    fs::create_dir_all(dir)?;
    let path = dir.join(format!("{name}.json"));
    let count = fs::read_dir(dir)?
        .filter_map(|e| e.ok())
        .filter(|e| e.path().extension().is_some_and(|s| s == "json"))
        .count();
    if !path.exists() && count >= 200 {
        return Ok(false);
    }
    crate::assets::atomic(&path, &serde_json::to_vec_pretty(preset)?)?;
    Ok(true)
}
