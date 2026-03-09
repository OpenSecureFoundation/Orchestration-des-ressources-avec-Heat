-- Schema de la base de donnees SQLite
-- Projet: Orchestration des ressources avec OpenStack Heat
-- Auteurs: Ngouo Franck Leonel, MOUDIO ABEGA Laurent Stephane

-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user', -- 'admin' ou 'user'
    full_name TEXT,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    failed_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);

-- Table des templates Heat
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    content TEXT NOT NULL, -- Contenu YAML du template
    type TEXT NOT NULL, -- 'builtin', 'git', 'uploaded', 'created'
    source_url TEXT, -- URL Git si type='git'
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT 0,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Table des stacks Heat deployees
CREATE TABLE IF NOT EXISTS stacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stack_id TEXT UNIQUE, -- ID OpenStack de la stack
    name TEXT NOT NULL,
    template_id INTEGER,
    status TEXT, -- CREATE_COMPLETE, UPDATE_IN_PROGRESS, etc.
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    parameters TEXT, -- JSON des parametres passes au template
    outputs TEXT, -- JSON des outputs de la stack
    FOREIGN KEY (template_id) REFERENCES templates(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Table des metriques collectees
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id TEXT NOT NULL, -- ID de la VM OpenStack
    server_name TEXT,
    metric_type TEXT NOT NULL, -- 'cpu', 'ram', 'disk', 'network_in', 'network_out', 'iops'
    value REAL NOT NULL,
    unit TEXT, -- '%', 'MB', 'GB', 'Mbps', etc.
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source TEXT -- 'agent', 'openstack', 'manual'
);

-- Table des politiques de scaling
CREATE TABLE IF NOT EXISTS scaling_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id TEXT UNIQUE NOT NULL,
    metric_type TEXT NOT NULL, -- Metrique surveillee
    scale_up_threshold REAL NOT NULL,
    scale_down_threshold REAL NOT NULL,
    cooldown_seconds INTEGER DEFAULT 120,
    evaluation_periods INTEGER DEFAULT 1,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des evenements de scaling
CREATE TABLE IF NOT EXISTS scaling_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id TEXT NOT NULL,
    event_type TEXT NOT NULL, -- 'scale_up', 'scale_down', 'cooldown', 'rejected'
    old_flavor TEXT,
    new_flavor TEXT,
    trigger_metric TEXT,
    trigger_value REAL,
    success BOOLEAN,
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des alertes recues
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    token_valid BOOLEAN NOT NULL,
    metrics TEXT NOT NULL, -- JSON avec toutes les metriques
    action_taken TEXT, -- 'scale_up', 'scale_down', 'none'
    is_valid BOOLEAN NOT NULL,
    rejection_reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des logs systeme
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL, -- 'INFO', 'WARNING', 'ERROR'
    category TEXT, -- 'auth', 'stack', 'scaling', 'template', etc.
    message TEXT NOT NULL,
    details TEXT, -- JSON avec details supplementaires
    user_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Index pour optimiser les requetes frequentes
CREATE INDEX IF NOT EXISTS idx_metrics_server_timestamp ON metrics(server_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_type_timestamp ON metrics(metric_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_stacks_created_by ON stacks(created_by);
CREATE INDEX IF NOT EXISTS idx_templates_type ON templates(type);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_scaling_events_server ON scaling_events(server_id, timestamp DESC);
