// ─── Auth ─────────────────────────────────────────────────────────────────────
export interface LoginRequest {
  username: string
  password: string
}

export interface Token {
  access_token: string
  token_type: string
}

export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'viewer'
  is_active: boolean
  created_at: string
}

// ─── Metrics ──────────────────────────────────────────────────────────────────
export interface ColumnValidation {
  column: string
  required: boolean
  present: boolean
  missing_count: number
  missing_pct: number
}

export interface ValidationReport {
  raw_rows: number
  after_dedup: number
  after_missing_drop: number
  final_rows: number
  duplicates_removed: number
  rows_with_missing: number
  columns: ColumnValidation[]
  warnings: string[]
}

export interface MetricDataset {
  id: string
  name: string
  description: string | null
  file_path: string
  row_count: number
  raw_row_count: number
  duplicate_count: number
  missing_value_count: number
  status: 'pending' | 'processing' | 'ready' | 'error'
  error_message: string | null
  validation_report: ValidationReport | null
  avg_cpu_utilization: number | null
  avg_memory_utilization: number | null
  avg_latency_ms: number | null
  avg_cost_per_hour: number | null
  avg_request_volume: number | null
  avg_error_rate_pct: number | null
  avg_availability: number | null
  ts_min: string | null
  ts_max: string | null
  created_at: string
}

export interface MetricDatasetList {
  total: number
  items: MetricDataset[]
}

export interface MetricRecord {
  id: string
  dataset_id: string
  timestamp: string
  cpu_utilization: number | null
  memory_utilization: number | null
  latency_ms: number | null
  request_volume: number | null
  error_rate_pct: number | null
  availability: number | null
  instance_count: number | null
  instance_type: string | null
  instance_price: number | null
}

export interface MetricRecordList {
  total: number
  items: MetricRecord[]
}

export interface UploadResponse {
  dataset_id: string
  name: string
  row_count: number
  raw_row_count: number
  duplicate_count: number
  missing_value_count: number
  status: string
  message: string
  validation_report: ValidationReport
}

export interface DatasetStats {
  dataset_id: string
  record_count: number
  ts_min: string | null
  ts_max: string | null
  avg_cpu_utilization: number | null
  avg_memory_utilization: number | null
  avg_latency_ms: number | null
  avg_cost_per_hour: number | null
  avg_request_volume: number | null
  avg_error_rate_pct: number | null
  avg_availability: number | null
  instance_types: string[]
}

// ─── Simulator ────────────────────────────────────────────────────────────────
export interface SimulationConfig {
  name: string
  description?: string
  dataset_id?: string

  current_instance_type: string
  current_vcpu: number
  current_memory_gb: number
  current_cost_per_hour_usd: number

  target_instance_type: string
  target_vcpu: number
  target_memory_gb: number
  target_cost_per_hour_usd: number

  max_cpu_threshold_pct: number
  max_memory_threshold_pct: number
  safety_margin_pct: number
  time_window_hours: number
  instance_count: number
}

export interface PercentileStats {
  mean: number
  p50: number
  p90: number
  p95: number
  p99: number
  max: number
  std: number
}

export interface TrendInfo {
  slope_pct_per_hour: number
  direction: 'stable' | 'increasing' | 'decreasing'
  r2: number
}

export interface CostSavings {
  current_monthly_cost_usd: number
  target_monthly_cost_usd: number
  monthly_savings_usd: number
  annual_savings_usd: number
  savings_pct: number
  roi_months: number | null
  total_instances: number
}

export interface PerformanceRisk {
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  risk_score: number
  breach_probability_pct: number
  cpu_breach_probability_pct: number
  memory_breach_probability_pct: number
  affected_metrics: string[]
  recommendations: string[]
  cpu_trend: TrendInfo
  memory_trend: TrendInfo
}

export interface ResourceAnalysis {
  current_cpu: PercentileStats
  current_memory: PercentileStats
  projected_cpu: PercentileStats
  projected_memory: PercentileStats
  scaling_factors: { cpu_scale: number; memory_scale: number }
  cpu_headroom_pct: number
  memory_headroom_pct: number
  recommendation: 'safe_to_rightsize' | 'proceed_with_caution' | 'not_recommended'
  data_points_analysed: number
}

export interface SimulationResults {
  cost_savings: CostSavings
  performance_risk: PerformanceRisk
  resource_analysis: ResourceAnalysis
  data_driven: boolean
}

export interface SimulationRun {
  id: string
  name: string
  description: string | null
  dataset_id: string | null
  config: SimulationConfig
  results: SimulationResults | null
  status: 'queued' | 'running' | 'completed' | 'failed'
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export interface SimulationRunList {
  total: number
  items: SimulationRun[]
}

export interface TimeseriesData {
  timestamps: string[]
  cpu: number[]
  memory: number[]
  latency: number[]
  request_volume: number[]
  data_driven: boolean
}

// ─── Experiments ──────────────────────────────────────────────────────────────
export interface ScenarioConfig {
  name: string
  description?: string
  config: Record<string, unknown>
}

export interface ExperimentCreate {
  name: string
  description?: string
  dataset_id?: string
  scenarios: ScenarioConfig[]
}

export interface Experiment {
  id: string
  name: string
  description: string | null
  dataset_id: string | null
  scenarios: ScenarioConfig[]
  comparison_results: Record<string, unknown> | null
  status: 'draft' | 'running' | 'completed' | 'failed'
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface ExperimentList {
  total: number
  items: Experiment[]
}

// ─── Reports ──────────────────────────────────────────────────────────────────
export interface ReportCreate {
  title: string
  report_type: 'simulation_summary' | 'experiment_comparison' | 'cost_analysis' | 'performance_impact'
  simulation_id?: string
  experiment_id?: string
}

export interface Report {
  id: string
  title: string
  report_type: string
  simulation_id: string | null
  experiment_id: string | null
  content: Record<string, unknown>
  rendered_content: string | null
  status: 'draft' | 'final'
  created_at: string
}

export interface ReportList {
  total: number
  items: Report[]
}

// ─── Common ───────────────────────────────────────────────────────────────────
export interface PaginationParams {
  skip?: number
  limit?: number
}

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'
export type SimulationStatus = 'queued' | 'running' | 'completed' | 'failed'
export type ExperimentStatus = 'draft' | 'running' | 'completed' | 'failed'
