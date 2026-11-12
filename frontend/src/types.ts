export interface RuleTrigger {
  id: string;
  name: string;
  points: number;
  explanation: string;
}

export interface HighlightedPhrase {
  phrase: string;
  start: number;
  end: number;
  weight: number;
  reason: string;
}

export interface TimelineEvent {
  timestamp: string;
  type: string;
  title: string;
  description: string;
}

export interface DealData {
  id: string;
  created_at: string;
  updated_at?: string;
  buyer_id?: string | null;
  seller_id?: string | null;
  buyer_name?: string;
  seller_name?: string;
  status?: string;
  invite_token?: string | null;
  invite_url?: string;
  share_message?: string;
  invite_status?: string;
  buyer_agreed?: boolean;
  seller_agreed?: boolean;
  item_name: string;
  price: number;
  currency: string;
  chat_text: string;
  source_type: 'text_paste' | 'screenshot' | 'in_app_room';
  initial_risk_score: number;
  risk_score: number;
  verdict: 'LOW' | 'MEDIUM' | 'HIGH';
  model_probability: number;
  explanation: string;
  rules_triggered: RuleTrigger[];
  highlighted_phrases: HighlightedPhrase[];
  paypal_order_id?: string | null;
  paypal_approval_url?: string | null;
  paypal_status?: string;
  paypal_capture_id?: string | null;
  drafted_message?: string | null;
  seller_reply_text?: string | null;
  seller_classification?: string | null;
  seller_confidence?: number | null;
  seller_litmus_verdict?: string | null;
  seller_risk_delta?: number;
  timeline: TimelineEvent[];
  // Transient/Display fields
  model_base_points?: number;
  rule_points_total?: number;
  verdict_title?: string;
  verdict_badge?: string;
  guidance?: string;
  // User role context
  user_role?: 'buyer' | 'seller' | 'viewer';
}

export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
}

export interface ChatMessage {
  id: string;
  deal_id?: string;
  sender_id: string;
  sender_name: string;
  sender_role: 'buyer' | 'seller';
  content: string;
  message_type: 'chat' | 'system' | 'paypal_card' | 'alert';
  is_private_to_buyer?: boolean;
  created_at: string;
}

export interface PayPalCard {
  order_id: string;
  approval_url: string;
  amount: number;
  currency: string;
  item_name: string;
  status: string;
  sandbox_notice: string;
}

export interface AIRiskUpdate {
  risk_score: number;
  verdict: 'LOW' | 'MEDIUM' | 'HIGH';
  verdict_title: string;
  verdict_badge: string;
  guidance: string;
  rules_triggered: RuleTrigger[];
  highlighted_phrases: HighlightedPhrase[];
  explanation: string;
  model_base_points: number;
  rule_points_total: number;
  seller_evaluation?: {
    classification: string;
    confidence: number;
    litmus_verdict: string;
    risk_delta: number;
    summary: string;
  } | null;
  refusal_warning?: string | null;
}

export interface WsEvent {
  type: string;
  deal_id: string;
  data: Record<string, unknown>;
}

export interface DealInvite {
  deal_id: string;
  token: string;
  item_name: string;
  price: number;
  currency: string;
  status: string;
  buyer_name: string;
  expires_at: string;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  version: string;
  models_loaded: boolean;
  paypal_configured: boolean;
  paypal_live?: boolean;
  paypal_environment: string;
  gemini_configured: boolean;
  gemini_live?: boolean;
  notice: string;
}

export interface ModelMetricsReport {
  timestamp: string;
  model_a_scam_classifier: {
    name: string;
    architecture: string;
    test_split_evaluation: {
      num_samples: number;
      accuracy: number;
      precision: number;
      recall: number;
      f1_score: number;
      confusion_matrix: {
        true_negative: number;
        false_positive: number;
        false_negative: number;
        true_positive: number;
      };
    };
    handwritten_holdout_evaluation: {
      num_samples: number;
      accuracy: number;
      precision: number;
      recall: number;
      f1_score: number;
      confusion_matrix: {
        true_negative: number;
        false_positive: number;
        false_negative: number;
        true_positive: number;
      };
    };
  };
  model_b_seller_reaction: {
    name: string;
    architecture: string;
    classes: string[];
    test_split_evaluation: {
      num_samples: number;
      accuracy: number;
      precision_macro: number;
      recall_macro: number;
      f1_macro: number;
      confusion_matrix: number[][];
    };
  };
}
