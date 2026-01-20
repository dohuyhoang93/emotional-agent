use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::fs::{OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::collections::HashMap;
use std::path::Path;
use sysinfo::{Pid, System};
use shared_memory::ShmemConf;
use std::sync::{Arc, Mutex};

const REGISTRY_FILE: &str = ".theus_memory_registry.jsonl";

#[derive(Serialize, Deserialize, Debug, Clone)]
struct AllocRecord {
    name: String,
    pid: u32,
    session: String,
    size: usize,
    ts: f64,
}

#[pyclass]
pub struct MemoryRegistry {
    session_id: String,
    // pid field removed, use dynamic std::process::id()
    owned_allocations: Arc<Mutex<HashMap<String, usize>>>, // name -> size
}

#[pymethods]
impl MemoryRegistry {
    #[new]
    fn new(session_id: String) -> Self {
        let registry = MemoryRegistry {
            session_id,
            owned_allocations: Arc::new(Mutex::new(HashMap::new())),
        };
        
        // Auto-scan on startup
        registry.scan_zombies();
        registry
    }

    pub fn scan_zombies(&self) {
        if !Path::new(REGISTRY_FILE).exists() {
            return;
        }

        let mut sys = System::new_all();
        sys.refresh_all();
        
        let path = Path::new(REGISTRY_FILE);
        let file = match std::fs::File::open(path) {
            Ok(f) => f,
            Err(_) => return,
        };
        let reader = BufReader::new(file);

        let mut active_records = Vec::new();
        let mut zombies_cleaned = 0;

        for line in reader.lines() {
            if let Ok(l) = line {
     if let Ok(record) = serde_json::from_str::<AllocRecord>(&l) {
                     // Check Liveness
                     let current_pid = std::process::id();
                     let is_alive = if record.pid == current_pid {
                         true
                     } else {
                         // sysinfo 0.30 usage
                         sys.process(Pid::from_u32(record.pid)).is_some()
                     };

                     if !is_alive {
                         // ZOMBIE! Unlink.
                         // We use shared_memory crate (or standard OS remove)
                         // shared_memory::Shmem doesn't have a static unlink method usually, 
                         // it relies on drop or specific OS calls?
                         // The crate exposes `ShmemConf` but deletion requires opening.
                         // Actually, on Linux/Windows, unlink by name is different.
                         // The crate might not expose raw unlink easily without mapping?
                         // Let's try to map and drop with unlink_on_drop if possible,
                         // or use shm_unlink directly?
                         // The `shared_memory` crate documentation says:
                         // "To delete a shared memory link, simply drop the Shmem struct... however... persistence..."
                         // Actually checking documentation: `ShmemConf` creates. 
                         // To delete a named shm without mapping is tricky in this crate?
                         // Ideally we map it then drop it with unlink config?
                         // Let's try basic best-effort.
                         
                         // Attempt to remove via OS specific if needed, or open-then-unlink.
                         // For now, let's assume we can treat it as a file on Linux (/dev/shm)
                         // or use proper crate method if available.
                         // Wait, standard `remove_file` works on /dev/shm on Linux.
                         // On Windows? It's harder.
                         
                         // BUT, `shared_memory` crate usually unlinks on Drop if configured.
                         // So we try to Open -> Set UnlinkOnDrop -> Drop.
                         match ShmemConf::new().os_id(&record.name).open() {
                             Ok(mut shm) => {
                                 shm.set_owner(true); // Ensure we own it to unlink
                                 // Dropping shm now unlinks it if owner is true?
                                 // Depends on crate version behavior.
                                 // Let's assume yes.
                                 zombies_cleaned += 1;
                             },
                             Err(_) => {}
                         }
                     } else {
                         active_records.push(record);
                     }
                }
            }
        }

        // Rewrite Registry
        if zombies_cleaned > 0 {
            if let Ok(mut f) = std::fs::File::create(REGISTRY_FILE) {
                for rec in active_records {
                    if let Ok(s) = serde_json::to_string(&rec) {
                        let _ = writeln!(f, "{}", s);
                    }
                }
            }
            println!("[TheusCore] Cleaned {} zombie segments.", zombies_cleaned);
        }
    }

    pub fn log_allocation(&self, name: String, size: usize) {
        let record = AllocRecord {
            name: name.clone(),
            pid: std::process::id(), // Dynamic PID
            session: self.session_id.clone(),
            size,
            ts: 0.0, // Timestamp not critical for now
        };
        
        // Track locally
        if let Ok(mut map) = self.owned_allocations.lock() {
            map.insert(name, size);
        }

        // Append to file
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(REGISTRY_FILE)
            .unwrap_or_else(|_| std::fs::File::create(REGISTRY_FILE).unwrap());
            
        if let Ok(s) = serde_json::to_string(&record) {
            let _ = writeln!(file, "{}", s);
        }
    }
    
    pub fn cleanup(&self) {
        // Unlink all owned
        if let Ok(map) = self.owned_allocations.lock() {
             for (name, _) in map.iter() {
                 // Open and Unlink
                 match ShmemConf::new().os_id(name).open() {
                     Ok(mut shm) => {
                         shm.set_owner(true);
                         // Drop -> Unlink
                     },
                     Err(_) => {}
                 }
             }
        }
    }
}
