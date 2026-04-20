export interface User {
  id: number
  email: string
  full_name: string
  is_active: boolean
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
}

export interface Property {
  id: number
  user_id: number
  address: string
  postal_code?: string
  city?: string
  department?: string
  asking_price?: number
  surface_area?: number
  rooms?: number
  property_type?: string
  floor?: number
  building_floors?: number
  building_year?: number
  estimated_value?: number
  price_per_sqm?: number
  market_comparison_score?: number
  recommendation?: string
  created_at: string
  updated_at: string
}

export interface Document {
  id: number
  user_id: number
  property_id?: number
  filename: string
  file_type: string
  document_category: string
  is_analyzed: boolean
  analysis_summary?: string
  upload_date: string
  file_size: number
}

export interface PriceAnalysis {
  estimated_value: number
  price_per_sqm: number
  market_avg_price_per_sqm: number
  price_deviation_percent: number
  comparable_sales: DVFRecord[]
  recommendation: string
  confidence_score: number
}

export interface DVFRecord {
  id: number
  sale_date: string
  sale_price: number
  address: string
  postal_code: string
  city: string
  property_type: string
  surface_area?: number
  rooms?: number
  price_per_sqm?: number
  unit_count?: number
  is_multi_unit?: boolean
  is_outlier?: boolean
  longitude?: number
  latitude?: number
  lots_detail?: Array<{
    lot_type?: string
    surface_area?: number
    rooms?: number
    price_per_sqm?: number
  }>
}

export interface PriceAnalysisSummary {
  estimated_value?: number
  price_deviation_percent?: number
  recommendation?: string
  confidence_score?: number
  comparables_count?: number
  estimated_value_2025?: number
  trend_used?: number
  updated_at?: string
  is_stale?: boolean
}

export interface PriceAnalysisFull extends PriceAnalysisSummary {
  price_per_sqm?: number
  market_avg_price_per_sqm?: number
  market_median_price_per_sqm?: number
  market_trend_annual?: number
  projected_price_per_sqm?: number
  trend_source?: string
  trend_sample_size?: number
  comparable_sales?: DVFRecord[]
  trend_projection?: {
    estimated_value_2025?: number
    projected_price_per_sqm?: number
    trend_used?: number
    trend_source?: string
    trend_sample_size?: number
    base_sale_date?: string
    base_price_per_sqm?: number
    neighboring_sales?: Array<DVFRecord & { is_outlier?: boolean }>
    confidence_level?: 'high' | 'moderate' | 'low'
  }
  market_trend?: {
    years: number[]
    average_prices: number[]
    year_over_year_changes: number[]
    sample_counts: number[]
    postal_code?: string
    total_sales: number
    outliers_excluded: number
  }
  excluded_sale_ids: number[]
  excluded_neighboring_sale_ids: number[]
}

export interface Analysis {
  analysis_id: number
  property_id: number
  investment_score: number
  value_score: number
  risk_score: number
  overall_recommendation: string
  estimated_fair_price?: number
  price_deviation_percent?: number
  annual_costs: number
  has_amiante: boolean
  has_plomb: boolean
  dpe_rating?: string
  ges_rating?: string
  summary: string
  created_at: string
  updated_at: string
}

export interface PVAGAnalysis {
  document_id: number
  summary: string
  upcoming_works: Array<{
    description: string
    estimated_cost: number
    timeline: string
  }>
  estimated_costs: {
    upcoming_works: number
    total: number
  }
  risk_level: 'low' | 'medium' | 'high'
  key_findings: string[]
  recommendations: string[]
}

export interface DiagnosticAnalysis {
  document_id: number
  dpe_rating?: string
  ges_rating?: string
  energy_consumption?: number
  has_amiante: boolean
  has_plomb: boolean
  risk_flags: string[]
  estimated_renovation_cost?: number
  summary: string
  recommendations: string[]
}

export interface PropertySynthesisPreview {
  risk_level?: string
  total_annual_cost?: number
  total_one_time_cost?: number
  key_findings?: string[]
  document_count: number
  redesign_count: number
}

export interface PropertyWithSynthesis extends Property {
  synthesis?: PropertySynthesisPreview | null
}

export interface TaxChargesAnalysis {
  document_id: number
  document_type: string
  period_covered: string
  total_amount: number
  annual_amount: number
  breakdown: Record<string, number>
  summary: string
}
