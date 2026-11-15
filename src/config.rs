use anyhow::{Context, Result};
use std::{
    env,
    path::{Path, PathBuf},
};
#[derive(Clone)]
pub struct Config {
    pub root: PathBuf,
    pub data: PathBuf,
    pub presets: PathBuf,
    pub cache: PathBuf,
    pub host: String,
    pub port: u16,
}
impl Config {
    pub fn load() -> Result<Self> {
        let root = env::var_os("DLFILTER_ROOT")
            .map(PathBuf::from)
            .or_else(|| {
                env::current_exe().ok().and_then(|p| {
                    p.ancestors()
                        .find(|a| a.join("templates/index.html").is_file())
                        .map(Path::to_path_buf)
                })
            })
            .unwrap_or_else(|| PathBuf::from(env!("CARGO_MANIFEST_DIR")));
        let data = env::var_os("DLFILTER_DATA_DIR")
            .map(PathBuf::from)
            .unwrap_or_else(|| root.join("database"));
        let presets = env::var_os("DLFILTER_PRESETS_DIR")
            .map(PathBuf::from)
            .unwrap_or_else(|| root.join("presets"));
        let key = crate::assets::digest(
            data.canonicalize()
                .unwrap_or(data.clone())
                .to_string_lossy()
                .as_bytes(),
        );
        let cache = env::var_os("DLFILTER_CACHE_DIR")
            .map(PathBuf::from)
            .unwrap_or_else(|| {
                directories::ProjectDirs::from("org", "dlfilter", "dlfilter")
                    .map(|p| p.cache_dir().join(&key[..16]))
                    .unwrap_or_else(|| env::temp_dir().join("dlfilter").join(&key[..16]))
            });
        Ok(Self {
            root,
            data,
            presets,
            cache,
            host: env::var("DLFILTER_HOST").unwrap_or("127.0.0.1".into()),
            port: env::var("DLFILTER_PORT")
                .unwrap_or("8000".into())
                .parse()
                .context("Invalid DLFILTER_PORT")?,
        })
    }
    pub fn database(&self) -> PathBuf {
        self.data.join("works.sqlite")
    }
}
