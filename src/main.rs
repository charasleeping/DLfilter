mod api;
mod assets;
mod config;
mod engine;
mod presets;
mod setup;
mod titles;
use anyhow::{Result, ensure};
use clap::{Parser, Subcommand};
#[derive(Parser)]
#[command(version, about = "DLFilter native search server")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}
#[derive(Subcommand)]
enum Command {
    Serve {
        #[arg(long)]
        open: bool,
    },
    Prepare {
        #[arg(long)]
        force: bool,
    },
    Doctor,
}
#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();
    let cfg = config::Config::load()?;
    if !matches!(cli.command, Command::Serve { .. }) {
        ensure!(
            cfg.database().is_file(),
            "Database missing at {}. Extract a database bundle into this data directory; see docs/database.md.",
            cfg.database().display()
        );
    }
    match cli.command {
        Command::Doctor => {
            let db = engine::readonly(&cfg.database())?;
            assets::required_database(&db)?;
            let vectors = assets::vectors(&cfg.data)?;
            let count: i64 = db.query_row("SELECT COUNT(*) FROM maniax", [], |r| r.get(0))?;
            println!(
                "Database: {} works\nGenres: {}\nCache: {}",
                count,
                vectors.ids.len(),
                cfg.cache.display()
            );
        }
        Command::Prepare { force } => {
            let start = std::time::Instant::now();
            let e = engine::Engine::load(cfg, force)?;
            println!(
                "Prepared {} works in {:.3}s",
                e.data.works.len(),
                start.elapsed().as_secs_f64()
            );
        }
        Command::Serve { open: show } => {
            let host = cfg.host.clone();
            let port = cfg.port;
            let listener = tokio::net::TcpListener::bind((host.as_str(), port)).await?;
            let url = format!(
                "http://{}:{port}/",
                if host.contains(':') {
                    format!("[{host}]")
                } else {
                    host
                }
            );
            eprintln!("DLFilter listening on {url}");
            if show {
                let _ = open::that(&url);
            }
            let (router, state) = setup::router(cfg);
            axum::serve(listener, router)
                .with_graceful_shutdown(async move {
                    shutdown_signal().await;
                    setup::shutdown(&state);
                })
                .await?;
        }
    }
    Ok(())
}

async fn shutdown_signal() {
    #[cfg(unix)]
    {
        let mut terminate =
            tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
                .expect("Register termination signal");
        tokio::select! {_=tokio::signal::ctrl_c()=>{},_=terminate.recv()=>{}}
    }
    #[cfg(not(unix))]
    {
        let _ = tokio::signal::ctrl_c().await;
    }
}
