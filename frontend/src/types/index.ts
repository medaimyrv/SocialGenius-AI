// === Enums ===
export type PlanTier = "free" | "pro";
export type SubscriptionStatus = "active" | "canceled" | "past_due" | "inactive";
export type ConversationType =
  | "business_analysis"
  | "content_strategy"
  | "calendar_creation"
  | "copywriting"
  | "hashtag_research"
  | "general";
export type MessageRole = "user" | "assistant" | "system";
export type ContentFormat =
  | "reel"
  | "carousel"
  | "single_image"
  | "story"
  | "tiktok_video"
  | "live";
export type Platform = "instagram" | "tiktok";

// === Models ===
export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  role: "user" | "admin";
  created_at: string;
}

export interface Business {
  id: string;
  owner_id: string;
  name: string;
  industry: string;
  description: string;
  target_audience: string | null;
  brand_voice: string | null;
  website_url: string | null;
  instagram_handle: string | null;
  tiktok_handle: string | null;
  extra_context: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  business_id: string | null;
  title: string;
  conversation_type: ConversationType;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  token_count: number | null;
  model_used: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
}

export interface Subscription {
  plan_tier: PlanTier;
  status: SubscriptionStatus;
  strategies_used_this_month: number;
  calendars_used_this_month: number;
  messages_used_this_month: number;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  max_strategies: number | null;
  max_calendars: number | null;
  max_messages: number | null;
  can_export_calendar: boolean;
  can_edit_content: boolean;
}

export interface ContentCalendar {
  id: string;
  business_id: string;
  conversation_id: string | null;
  title: string;
  week_start_date: string;
  week_end_date: string;
  platform: string;
  strategy_summary: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ContentPiece {
  id: string;
  calendar_id: string;
  platform: Platform;
  content_format: ContentFormat;
  topic: string;
  caption: string;
  hashtags: string[] | null;
  visual_description: string | null;
  hook: string | null;
  call_to_action: string | null;
  scheduled_date: string;
  scheduled_time: string | null;
  day_of_week: string;
  notes: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

// === Auth ===
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}
