export interface StockQuote {
  symbol: string;
  last_price: number;
  change: number;
  percent_change: number;
  volume: number;
  time: string;
}

export interface StockInfo {
  symbol: string;
  company_name: string;
  industry: string;
  market_cap: number;
}

export interface AgentOpinion {
  signal: string;
  confidence: number;
  sentiment_score: number;
  reasoning: string;
  key_points: string[];
  key_levels: Record<string, number>;
}

export interface AnalysisResult {
  symbol: string;
  status: string;
  info: StockInfo;
  quote: StockQuote;
  llm_analysis: string;
  opinion: AgentOpinion;
  is_multi_agent: boolean;
}
