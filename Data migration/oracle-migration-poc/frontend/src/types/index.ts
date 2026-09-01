export enum MigrationStatus {
  PENDING = 'pending',
  ANALYZING = 'analyzing',
  PLANNING = 'planning',
  AWAITING_APPROVAL = 'awaiting_approval',
  APPROVED = 'approved',
  EXECUTING = 'executing',
  VALIDATING = 'validating',
  COMPLETED = 'completed',
  FAILED = 'failed',
  ROLLED_BACK = 'rolled_back',
  CANCELLED = 'cancelled'
}

export enum MigrationStep {
  STEP_1_NON_CDB_TO_PDB = 'step_1_non_cdb_to_pdb',
  STEP_2_PDB_19C_TO_23C = 'step_2_pdb_19c_to_23c'
}

export enum DatabaseType {
  ORACLE_19C_STANDALONE = 'oracle_19c_standalone',
  ORACLE_19C_CDB_PDB = 'oracle_19c_cdb_pdb',
  ORACLE_23C_CDB_PDB = 'oracle_23c_cdb_pdb'
}

export interface DatabaseConfig {
  db_id: string;
  db_type: DatabaseType;
  host: string;
  port: number;
  service_name: string;
  username?: string;
  password?: string;
  pdb_name?: string;
  description?: string;
}

export interface TableInfo {
  table_name: string;
  schema_name: string;
  row_count: number;
  size_mb: number;
  selected: boolean;
}

export interface DependencyInfo {
  table_name: string;
  depends_on: string[];
  dependency_type: string;
  risk_level: string;
}

export interface AgentLog {
  timestamp: string;
  agent_name: string;
  action: string;
  reasoning: string;
  metadata: any;
}

export interface MigrationPlan {
  plan_id: string;
  migration_id: string;
  step: MigrationStep;
  execution_order: string[];
  dependencies: DependencyInfo[];
  estimated_duration_minutes: number;
  risk_assessment: string;
  pre_checks: string[];
  post_checks: string[];
  rollback_strategy: string;
  ai_reasoning: string;
  requires_approval: boolean;
  created_at: string;
  step_1?: {
    step: string;
    execution_order: string[];
    estimated_duration_minutes: number;
    risk_level: string;
  };
  step_2?: {
    step: string;
    execution_order: string[];
    estimated_duration_minutes: number;
    risk_level: string;
  };
}

export interface MigrationProgress {
  migration_id: string;
  status: MigrationStatus;
  current_step?: MigrationStep;
  current_table?: string;
  tables_completed: number;
  tables_total: number;
  progress_percentage: number;
  started_at?: string;
  completed_at?: string;
  agent_logs: AgentLog[];
  error_message?: string;
}

export interface MigrationResponse {
  migration_id: string;
  status: MigrationStatus;
  message: string;
  plan?: MigrationPlan;
  progress?: MigrationProgress;
}

export interface ValidationResult {
  validation_id: string;
  migration_id: string;
  step: MigrationStep;
  source_row_count: number;
  target_row_count: number;
  row_count_match: boolean;
  schema_match: boolean;
  constraint_match: boolean;
  index_match: boolean;
  issues: any[];
  passed: boolean;
  validation_time: string;
}

export interface SchemaAnalysis {
  db_id: string;
  total_tables: number;
  total_size_mb: number;
  tables: TableInfo[];
  dependencies: DependencyInfo[];
  compatibility_issues: string[];
  readiness_score: number;
  analysis_time: string;
}
