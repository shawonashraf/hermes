//! Start the Hermes container, attach to the Hermes chat, and stop the
//! containers when the chat ends (`/exit`, a crash, or a closed terminal).

use std::fs;
use std::io::{self, Write};
use std::path::Path;
use std::os::unix::process::ExitStatusExt;
use std::process::{Command, ExitCode, ExitStatus, Stdio};

/// Repo root: holds docker-compose.yml and .env. Baked in at build time so
/// the binary works from any directory (e.g. through a shell alias).
const PROJECT_DIR: &str = env!("CARGO_MANIFEST_DIR");
const SERVICE: &str = "hermes";
/// Hermes's working directory inside the container (bind-mounted host folder).
const CONTAINER_WORKDIR: &str = "/workdirectory";
/// Host folders bind-mounted by docker-compose.yml.
const HOST_DIRS: [&str; 2] = ["hermes_wd", "hindsight_data"];
/// First start installs the Hindsight plugin, so allow more than a restart needs.
const START_TIMEOUT_SECS: &str = "300";

fn main() -> ExitCode {
    // Survive Ctrl-C, SIGTERM and SIGHUP so the containers are always stopped.
    // Child processes still get the signal and exit; cleanup runs after.
    if let Err(e) = ctrlc::set_handler(|| {}) {
        note(&format!("cannot install signal handler: {e}"));
        return ExitCode::FAILURE;
    }

    let code = start_and_chat();

    note("stopping containers");
    // Detached from the terminal: it may already be gone (window closed),
    // and the stop must still happen.
    let mut stop = compose_cmd(&["stop"]);
    stop.stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null());
    match stop.status().map(exit_code) {
        Ok(0) => {
            note("containers stopped");
            ExitCode::from(code)
        }
        Ok(_) => {
            note("`docker compose stop` failed");
            ExitCode::FAILURE
        }
        Err(e) => {
            note(&format!("cannot run docker: {e}"));
            ExitCode::FAILURE
        }
    }
}

/// Returns the exit code to report: the chat's own, or the failing step's.
fn start_and_chat() -> u8 {
    // Create them ourselves: Docker would create missing ones as root.
    for dir in HOST_DIRS {
        if let Err(e) = fs::create_dir_all(Path::new(PROJECT_DIR).join(dir)) {
            note(&format!("cannot create {dir}/: {e}"));
            return 1;
        }
    }

    let up = compose(&["up", "--detach", "--wait", "--wait-timeout", START_TIMEOUT_SECS]);
    match up {
        Ok(0) => {}
        Ok(code) => {
            note("containers did not become ready (see `docker compose logs`)");
            return code;
        }
        Err(e) => {
            note(&format!("cannot run docker: {e}"));
            return 1;
        }
    }

    match compose(&["exec", "--user", "hermes", "--workdir", CONTAINER_WORKDIR, SERVICE, "hermes"]) {
        Ok(code) => code,
        Err(e) => {
            note(&format!("cannot run docker: {e}"));
            1
        }
    }
}

/// Runs `docker compose <args>` in the repo with the terminal attached.
fn compose(args: &[&str]) -> io::Result<u8> {
    compose_cmd(args).status().map(exit_code)
}

fn compose_cmd(args: &[&str]) -> Command {
    let mut cmd = Command::new("docker");
    cmd.arg("compose").args(args).current_dir(PROJECT_DIR);
    cmd
}

/// Status line on stderr. Ignores write errors: `eprintln!` panics when the
/// terminal is gone, which would skip stopping the container.
fn note(msg: &str) {
    let _ = writeln!(io::stderr(), "hermes-docker: {msg}");
}

/// Shell convention: the process's exit code, or 128 + signal if killed.
fn exit_code(status: ExitStatus) -> u8 {
    match (status.code(), status.signal()) {
        (Some(code), _) => u8::try_from(code).unwrap_or(1),
        (None, Some(signal)) => u8::try_from(128 + signal).unwrap_or(1),
        (None, None) => 1,
    }
}
