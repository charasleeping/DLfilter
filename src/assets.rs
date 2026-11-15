use anyhow::{Context, Result, bail, ensure};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    fs::{self, File},
    io::{Read, Write},
    path::Path,
    time::UNIX_EPOCH,
};
pub fn digest(data: &[u8]) -> String {
    hex::encode(Sha256::digest(data))
}
pub fn file_digest(path: &Path) -> Result<String> {
    let mut file = File::open(path)?;
    let mut hash = Sha256::new();
    let mut buf = [0u8; 65536];
    loop {
        let n = file.read(&mut buf)?;
        if n == 0 {
            break;
        }
        hash.update(&buf[..n]);
    }
    Ok(hex::encode(hash.finalize()))
}
pub fn atomic(path: &Path, data: &[u8]) -> Result<()> {
    let mut file = tempfile::NamedTempFile::new_in(path.parent().context("Missing parent")?)?;
    file.write_all(data)?;
    file.as_file().sync_all()?;
    file.persist(path)?;
    Ok(())
}
#[derive(Deserialize, Serialize)]
pub struct VectorManifest {
    pub version: u32,
    pub ids: Vec<String>,
    pub dimension: usize,
    pub sha256: String,
}
pub struct Vectors {
    pub ids: Vec<String>,
    pub gram: Vec<f64>,
}
pub fn vectors(data: &Path) -> Result<Vectors> {
    let manifest: VectorManifest = serde_json::from_slice(&fs::read(data.join("genre_vectors.json")).context("Portable vectors missing. Convert your trusted genre_vec.pkl with: python -m module.export_vectors --trusted-pickle PATH --output DATA_DIR")?)?;
    ensure!(
        manifest.version == 1
            && (1..=1000).contains(&manifest.ids.len())
            && (1..=65536).contains(&manifest.dimension),
        "Invalid vector manifest"
    );
    let raw = fs::read(data.join("genre_vectors.f32"))?;
    ensure!(
        raw.len() == manifest.ids.len() * manifest.dimension * 4 && digest(&raw) == manifest.sha256,
        "Vector checksum or length mismatch"
    );
    let mut previous = "";
    for id in &manifest.ids {
        ensure!(
            id.len() == 3 && id.bytes().all(|b| b.is_ascii_digit()) && id.as_str() > previous,
            "Invalid or repeated vector ID"
        );
        previous = id;
    }
    let values: Vec<f64> = raw
        .as_chunks::<4>()
        .0
        .iter()
        .map(|x| f32::from_le_bytes(*x) as f64)
        .collect();
    ensure!(values.iter().all(|x| x.is_finite()), "Nonfinite vector");
    let n = manifest.ids.len();
    let d = manifest.dimension;
    let mut gram = vec![0.; n * n];
    for i in 0..n {
        for j in 0..=i {
            let dot = values[i * d..(i + 1) * d]
                .iter()
                .zip(&values[j * d..(j + 1) * d])
                .map(|(a, b)| a * b)
                .sum();
            gram[i * n + j] = dot;
            gram[j * n + i] = dot;
        }
    }
    Ok(Vectors {
        ids: manifest.ids,
        gram,
    })
}
pub fn fingerprint(cfg: &crate::config::Config) -> Result<String> {
    let m = fs::metadata(cfg.database())?;
    let mut value = format!(
        "cache-v1-icu4x:{}:{}:{}",
        cfg.database().canonicalize()?.display(),
        m.len(),
        m.modified()?.duration_since(UNIX_EPOCH)?.as_nanos()
    );
    value.push_str(&digest(include_bytes!("../Cargo.lock")));
    #[cfg(unix)]
    {
        use std::os::unix::fs::MetadataExt;
        value.push_str(&format!(":{}:{}", m.dev(), m.ino()));
    }
    for name in [
        "genre_table.json",
        "workformat.json",
        "genre_vectors.json",
        "genre_vectors.f32",
    ] {
        value.push_str(&file_digest(&cfg.data.join(name))?);
    }
    Ok(digest(value.as_bytes()))
}
pub fn json(path: &Path) -> Result<serde_json::Value> {
    Ok(serde_json::from_slice(&fs::read(path)?)?)
}
pub fn required_database(conn: &rusqlite::Connection) -> Result<()> {
    let columns: Vec<String> = conn
        .prepare("PRAGMA table_info(maniax)")?
        .query_map([], |r| r.get(1))?
        .collect::<rusqlite::Result<_>>()?;
    for c in [
        "index",
        "name",
        "description",
        "maker",
        "siteId",
        "type",
        "ageCategory",
        "tags",
        "options",
        "registDate",
        "dlCount",
        "rate",
        "rateCount",
        "reviewCount",
    ] {
        if !columns.iter().any(|x| x == c) {
            bail!("Missing required column: {c}");
        }
    }
    Ok(())
}
