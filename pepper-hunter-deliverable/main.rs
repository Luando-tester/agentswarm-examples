use serde::Deserialize;
use std::env;
use std::io::{self, Write};
use ureq;

#[derive(Deserialize)]
struct BountyItem {
    id: String,
    title: String,
    status: String,
    bounty: BountyReward,
}

#[derive(Deserialize)]
struct BountyReward {
    reward: String,
}

#[derive(Deserialize)]
struct ApiResponse {
    bounties: Vec<BountyItem>,
}

fn main() {
    let mut base_url = env::var("AGENTSWARM_BASE_URL")
        .unwrap_or_else(|_| "https://agentswarm.space".to_string());
    
    while base_url.ends_with('/') {
        base_url.pop();
    }

    let url = format!("{}/api/bounties", base_url);

    let resp = match ureq::get(&url).call() {
        Ok(r) => r,
        Err(e) => {
            eprintln!("HTTP error: {}", e);
            std::process::exit(1);
        }
    };

    let body = match resp.into_string() {
        Ok(b) => b,
        Err(e) => {
            eprintln!("HTTP read error: {}", e);
            std::process::exit(1);
        }
    };

    let parsed: ApiResponse = match serde_json::from_str(&body) {
        Ok(p) => p,
        Err(e) => {
            eprintln!("JSON parse error: {}", e);
            std::process::exit(1);
        }
    };

    let mut stdout = io::stdout();
    for item in parsed.bounties {
        if item.status == "open" {
            let line = format!(
                "{}\t{}\t{}\t{}/p/{}\n",
                item.id, item.title, item.bounty.reward, base_url, item.id
            );
            if let Err(_) = stdout.write_all(line.as_bytes()) {
                std::process::exit(1);
            }
        }
    }
}
