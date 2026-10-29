export interface MarketSummary { observations: number; analyzed: number; average_price: number | null; top_models: Array<{ model: string; count: number }>; demand_signals: number; sale_signals: number; }
export interface Observation { id: number; source_id: number | null; source_url: string | null; content_type: string; raw_text: string; seller_name: string | null; brand: string | null; model_name: string | null; size: string | null; price: number | null; city: string | null; availability: string; status: string; confidence: number | null; created_at: string; }

