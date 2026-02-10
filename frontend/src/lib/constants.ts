export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
export const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "SocialGenius";

export const CONVERSATION_TYPE_LABELS: Record<string, string> = {
  business_analysis: "Análisis de Negocio",
  content_strategy: "Estrategia de Contenido",
  calendar_creation: "Crear Calendario",
  copywriting: "Copywriting",
  hashtag_research: "Hashtags y Tendencias",
  general: "General",
};

export const PLATFORM_LABELS: Record<string, string> = {
  instagram: "Instagram",
  tiktok: "TikTok",
};

export const CONTENT_FORMAT_LABELS: Record<string, string> = {
  reel: "Reel",
  carousel: "Carrusel",
  single_image: "Imagen",
  story: "Story",
  tiktok_video: "Video TikTok",
  live: "En Vivo",
};
